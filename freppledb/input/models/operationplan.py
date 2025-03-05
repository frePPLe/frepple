#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import ast
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil.parser import parse
import json
from logging import INFO, ERROR, WARNING, DEBUG, getLogger
import math
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.worksheet.worksheet import Worksheet
from typing import List

from django.conf import settings
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.db import models, DEFAULT_DB_ALIAS, connections
from django.db.models import Q, ForeignKey
from django.db.models.fields import AutoField, NOT_PROVIDED
from django.db.models.fields.related import RelatedField
from django.forms.models import modelform_factory
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.utils.encoding import force_str
from django.utils.text import get_text_list

from freppledb.common.dataload import BulkForeignKeyFormField
from freppledb.common.fields import AliasDateTimeField, AliasField
from freppledb.common.models import AuditModel, MultiDBManager, Parameter, Comment

from ..models.calendar import Calendar
from ..models.demand import Demand
from ..models.item import Item
from ..models.location import Location
from ..models.operation import Operation, OperationResource, OperationDependency
from ..models.resource import Resource
from ..models.supplier import Supplier

logger = getLogger(__name__)


class OperationPlan(AuditModel):
    # Possible types
    types = (
        ("STCK", _("inventory")),
        ("MO", _("manufacturing order")),
        ("PO", _("purchase order")),
        ("DO", _("distribution order")),
        ("DLVR", _("delivery order")),
    )

    # Possible status
    orderstatus = (
        ("proposed", _("proposed")),
        ("approved", _("approved")),
        ("confirmed", _("confirmed")),
        ("completed", _("completed")),
        ("closed", _("closed")),
    )

    # Database fields
    # Common fields
    reference = models.CharField(
        _("reference"),
        max_length=300,
        primary_key=True,
        help_text=_("Unique identifier"),
    )
    status = models.CharField(
        _("status"),
        null=True,
        blank=True,
        max_length=20,
        choices=orderstatus,
        help_text=_("Status of the order"),
    )
    type = models.CharField(
        _("type"),
        max_length=5,
        choices=types,
        default="MO",
        help_text=_("Order type"),
        db_index=True,
    )
    quantity = models.DecimalField(
        _("quantity"), max_digits=20, decimal_places=8, default="1.00"
    )
    quantity_completed = models.DecimalField(
        _("completed quantity"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    color = models.DecimalField(
        _("color"),
        max_digits=20,
        null=True,
        blank=True,
        decimal_places=8,
        default="0.00",
    )
    startdate = models.DateTimeField(
        _("start date"), help_text=_("start date"), null=True, blank=True, db_index=True
    )
    enddate = models.DateTimeField(
        _("end date"), help_text=_("end date"), null=True, blank=True, db_index=True
    )
    remark = models.CharField(
        _("remark"),
        null=True,
        blank=True,
        max_length=300,
        help_text=_("remark"),
    )
    criticality = models.DecimalField(
        _("criticality"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        editable=False,
    )
    delay = models.DurationField(_("delay"), null=True, blank=True, editable=False)
    plan = models.JSONField(default=dict, null=True, blank=True, editable=False)
    # Used only for manufacturing orders
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("operation"),
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    owner = models.ForeignKey(
        "self",
        verbose_name=_("owner"),
        null=True,
        blank=True,
        related_name="xchildren",
        help_text=_("Hierarchical parent"),
        on_delete=models.CASCADE,
    )
    batch = models.CharField(
        _("batch"),
        max_length=300,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("MTO batch name"),
    )
    # Used for purchase orders and distribution orders
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    # Used only for distribution orders
    origin = models.ForeignKey(
        Location,
        verbose_name=_("origin"),
        null=True,
        blank=True,
        related_name="origins",
        db_index=True,
        on_delete=models.CASCADE,
    )
    destination = models.ForeignKey(
        Location,
        verbose_name=_("destination"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="destinations",
        db_index=True,
    )
    # Used only for purchase orders
    supplier = models.ForeignKey(
        Supplier,
        verbose_name=_("supplier"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    # Used for delivery operationplans
    demand = models.ForeignKey(
        Demand,
        verbose_name=_("demand"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    due = models.DateTimeField(
        _("due"),
        help_text=_("Due date of the demand/forecast"),
        null=True,
        blank=True,
        editable=False,
    )
    name = models.CharField(
        _("name"), max_length=1000, null=True, blank=True, db_index=True
    )

    class Manager(MultiDBManager):
        pass

    def __str__(self):
        return str(self.reference)

    def propagateStatus(self):
        if self.type == "STCK":
            return
        state = getattr(self, "_state", None)
        db = state.db if state else DEFAULT_DB_ALIAS

        # Get the parameter that controls whether completed operations are
        # allowed to have dates in the future
        completed_allow_future = cache.get("completed_allow_future_%s" % db, None)
        if completed_allow_future is None:
            completed_allow_future = (
                Parameter.getValue("COMPLETED.allow_future", db, "false").lower()
                == "true"
            )
            cache.set(
                "completed_allow_future_%s" % db, completed_allow_future, timeout=60
            )

        # Assure that all child operationplans also get the same status
        now = datetime.now()
        if self.type not in ("DO", "PO"):
            for subop in self.xchildren.all().using(db):
                if subop.status != self.status:
                    subop.status = self.status
                    subop.save(update_fields=["status"])

        # A parent operationplan can't be proposed when it's children already have a different status
        if (
            self.type == "MO"
            and self.owner
            and self.status != "proposed"
            and self.owner.status == "proposed"
        ):
            self.owner.status = "approved"
            self.owner.save(update_fields=["status"])

        if self.status not in ("completed", "closed"):
            return

        # Assure the start and end are in the past
        if not completed_allow_future:
            if self.enddate:
                if isinstance(self.enddate, str):
                    self.enddate = parse(self.enddate)
                if self.enddate > now:
                    self.enddate = now
            if self.startdate:
                if isinstance(self.startdate, str):
                    self.startdate = parse(self.startdate)
                if self.startdate > now:
                    self.startdate = now

        if self.type == "MO" and self.owner and self.owner.operation.type == "routing":
            # Assure that previous routing steps are also marked closed or completed
            subopplans = [i for i in self.owner.xchildren.all().using(db)]
            for subop in subopplans:
                if subop.reference == self.reference:
                    subop.status = self.status
            steps = {
                z: z.priority
                for z in self.owner.operation.childoperations.all()
                .using(db)
                .only("name", "priority")
            }
            myprio = steps.get(self.operation, 0)
            for subop in subopplans:
                if (
                    subop.status != self.status
                    and steps.get(subop.operation, 0) < myprio
                ):
                    subop.status = self.status
                    if not completed_allow_future:
                        if subop.enddate > now:
                            subop.enddate = now
                        if subop.startdate > now:
                            subop.startdate = now
                    subop.save(update_fields=["status", "startdate", "enddate"])

            # Assure that the parent is at least approved
            if len(steps) == len(subopplans):
                all_steps_completed = all_steps_closed = True
            else:
                # We know there are will be some proposed steps
                all_steps_completed = all_steps_closed = False
            for subop in subopplans:
                if subop.status not in ("closed", "completed"):
                    all_steps_completed = False
                if subop.status != "closed":
                    all_steps_closed = False
            if all_steps_closed and self.owner.status != "closed":
                self.owner.status = "closed"
                if not completed_allow_future:
                    if self.owner.enddate > now:
                        self.owner.enddate = now
                    if self.owner.startdate > now:
                        self.owner.startdate = now
                self.owner.save(
                    update_fields=["status", "startdate", "enddate"], using=db
                )
            elif all_steps_completed and self.owner.status != "completed":
                self.owner.status = "completed"
                if not completed_allow_future:
                    if self.owner.enddate > now:
                        self.owner.enddate = now
                    if self.owner.startdate > now:
                        self.owner.startdate = now
                self.owner.save(
                    update_fields=["status", "startdate", "enddate"], using=db
                )
            elif self.owner.status == "proposed":
                self.owner.status = "approved"
                if not completed_allow_future and self.owner.startdate > now:
                    self.owner.startdate = now
                self.owner.save(update_fields=["status", "startdate"], using=db)

        # Remove all capacity consumption of closed and completed
        self.resources.all().using(db).delete()

        for opplanmat in self.materials.all().using(db):
            # Assure the material production and consumption are in the past
            # We are not correcting the expected onhand. The next plan generation will do that.
            if not completed_allow_future and opplanmat.flowdate > now:
                opplanmat.flowdate = now
                opplanmat.save(using=db)
            # Check that upstream buffers have enough supply in the closed status
            if opplanmat.quantity < 0:
                # check the inventory + consumed
                flplns = [
                    i
                    for i in OperationPlanMaterial.objects.all()
                    .using(db)
                    .filter(item=opplanmat.item.name, location=opplanmat.location.name)
                    .order_by("flowdate", "-quantity")
                    .select_related("operationplan")
                ]
                closed_balance = Decimal(
                    0.00001
                )  # Leaving some room for rounding errors
                for f in flplns:
                    if (
                        f.operationplan.type == "STCK"
                        or f.operationplan.status in ["closed", "completed"]
                        or f.operationplan.reference == self.reference
                    ):
                        closed_balance += f.quantity
                if closed_balance < 0:
                    # Things don't add up here.
                    # We'll close some upstream supply to make things match up
                    # First, try changing the status of confirmed supply
                    for f in flplns:
                        if (
                            f.quantity > 0
                            and f.operationplan.status == "confirmed"
                            and f.operationplan.type != "STCK"
                        ):
                            f.operationplan.status = self.status
                            f.operationplan.save(update_fields=["status"])
                            closed_balance += f.quantity
                            if closed_balance >= 0:
                                break
                    if closed_balance < 0:
                        # Second, try changing the status of approved supply
                        for f in flplns:
                            if f.quantity > 0 and f.operationplan.status == "approved":
                                f.operationplan.status = self.status
                                f.operationplan.save(update_fields=["status"])
                                closed_balance += f.quantity
                                if closed_balance >= 0:
                                    break
                        if closed_balance < 0:
                            # Finally, try changing the status of proposed supply
                            for f in flplns:
                                if (
                                    f.quantity > 0
                                    and f.operationplan.status == "proposed"
                                ):
                                    f.operationplan.status = self.status
                                    f.operationplan.save(update_fields=["status"])
                                    closed_balance += f.quantity
                                    if closed_balance >= 0:
                                        break

    def save(self, *args, **kwargs):
        self.propagateStatus()
        # Call the real save() method
        super().save(*args, **kwargs)

    @classmethod
    def getDeleteStatements(cls):
        stmts = []
        stmts.append(
            """
            delete from operationplan where type = '%s'
            """
            % cls.getType()
        )
        return stmts

    class Meta(AuditModel.Meta):
        db_table = "operationplan"
        verbose_name = _("operationplan")
        verbose_name_plural = _("operationplans")
        ordering = ["reference"]


class OperationPlanRelatedMixin:
    @classmethod
    def getModelForm(cls, fields, database=DEFAULT_DB_ALIAS):
        template = modelform_factory(
            cls,
            fields=[
                i
                for i in fields
                if i
                not in (
                    "operationplan__startdate",
                    "operationplan__enddate",
                    "operationplan__quantity",
                    "operationplan__quantity_completed",
                    "operationplan__status",
                    "operationplan__reference",
                )
            ],
            formfield_callback=lambda f: (
                isinstance(f, RelatedField) and f.formfield(using=database)
            )
            or f.formfield(),
        )

        # Return a form class with some extra fields
        class OpplanRelated_form(template):
            operationplan__startdate = (
                forms.CharField() if "operationplan__startdate" in fields else None
            )
            operationplan__enddate = (
                forms.CharField() if "operationplan__enddate" in fields else None
            )
            operationplan__quantity = (
                forms.DecimalField(min_value=0)
                if "operationplan__quantity" in fields
                else None
            )
            operationplan__quantity_completed = (
                forms.DecimalField(min_value=0)
                if "operationplan__quantity_completed" in fields
                else None
            )
            operationplan__status = (
                forms.ChoiceField(choices=OperationPlan.orderstatus)
                if "operationplan__status" in fields
                else None
            )

            def save(self, commit=True):
                instance = super().save(commit=False)
                if instance and instance.operationplan.type != "STCK":
                    data = self.cleaned_data
                    dirty = False
                    if "operationplan__startdate" in fields:
                        instance.operationplan.startdate = data[
                            "operationplan__startdate"
                        ]
                        dirty = True
                    if "operationplan__enddate" in fields:
                        instance.operationplan.enddate = data["operationplan__enddate"]
                        dirty = True
                    if "operationplan__quantity" in fields:
                        instance.operationplan.quantity = data[
                            "operationplan__quantity"
                        ]
                        dirty = True
                    if "operationplan__quantity_completed" in fields:
                        instance.operationplan.quantity_completed = data[
                            "operationplan__quantity_completed"
                        ]
                        dirty = True
                    if "operationplan__status" in fields:
                        instance.operationplan.status = data["operationplan__status"]
                        dirty = True
                    if dirty:
                        instance.operationplan.save(using=database)
                if commit:
                    instance.save(using=database)
                return instance

        return OpplanRelated_form


class OperationPlanResource(AuditModel, OperationPlanRelatedMixin):
    # Possible status
    OPRstatus = (
        ("proposed", _("proposed")),
        ("confirmed", _("confirmed")),
        ("closed", _("closed")),
    )

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        related_name="operationplanresources",
        on_delete=models.CASCADE,
    )
    operationplan = models.ForeignKey(
        OperationPlan,
        verbose_name=_("reference"),
        db_index=True,
        related_name="resources",
        on_delete=models.CASCADE,
    )
    quantity = models.DecimalField(
        _("quantity"),
        max_digits=20,
        decimal_places=8,
        default=1.0,
        blank=True,
        null=True,
    )
    setup = models.CharField(_("setup"), max_length=300, null=True, blank=True)
    status = models.CharField(
        _("load status"),
        null=True,
        blank=True,
        max_length=20,
        choices=OPRstatus,
        help_text=_("Status of the resource assignment"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, resource, operationplan):
            # Note: we are not enforcing the uniqueness of this natural key in the database
            return self.get(operationplan=operationplan, resource=resource)

    def natural_key(self):
        return (self.resource, self.operationplan)

    objects = Manager()

    def __str__(self):
        return "%s %s %s %s" % (
            self.resource,
            self.operationplan.startdate,
            self.operationplan.enddate,
            self.status,
        )

    class Meta:
        db_table = "operationplanresource"
        unique_together = (("resource", "operationplan"),)
        ordering = ["resource", "operationplan"]
        verbose_name = _("resource detail")
        verbose_name_plural = _("resource detail")


class OperationPlanMaterial(AuditModel, OperationPlanRelatedMixin):
    # Possible status
    OPMstatus = (
        ("proposed", _("proposed")),
        ("confirmed", _("confirmed")),
        ("closed", _("closed")),
    )

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        related_name="operationplanmaterials",
        db_index=True,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        related_name="operationplanmaterials",
        db_index=True,
        on_delete=models.CASCADE,
    )
    operationplan = models.ForeignKey(
        OperationPlan,
        verbose_name=_("reference"),
        db_index=True,
        related_name="materials",
        on_delete=models.CASCADE,
    )
    quantity = models.DecimalField(_("quantity"), max_digits=20, decimal_places=8)
    flowdate = models.DateTimeField(_("date"), db_index=True)
    onhand = models.DecimalField(
        _("onhand"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    minimum = models.DecimalField(
        _("minimum"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    periodofcover = models.DecimalField(
        _("period of cover"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    status = models.CharField(
        _("material status"),
        null=True,
        blank=True,
        max_length=20,
        choices=OPMstatus,
        help_text=_("status of the material production or consumption"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operationplan, item, location):
            # Note: we are not enforcing the uniqueness of this natural key in the database
            # (eg when using transfer batching there can be multiple records for the same key)
            return self.get(operationplan=operationplan, item=item, location=location)

    def natural_key(self):
        return (self.operationplan, self.item, self.location)

    objects = Manager()

    def __str__(self):
        return "%s @ %s %s %s %s" % (
            self.item_id,
            self.location_id,
            self.flowdate,
            self.quantity,
            self.status,
        )

    class Meta:
        db_table = "operationplanmaterial"
        ordering = ["item", "location", "flowdate"]
        verbose_name = _("inventory detail")
        verbose_name_plural = _("inventory detail")
        indexes = [models.Index(fields=["item", "location"], name="opplanmat_itemloc")]

    @classmethod
    def export_objects(cls, query, request):
        # When exporting a workbook of the model, we don't want to include the stock operationplans
        return query.exclude(operationplan__type="STCK")


class DeliveryOrder(OperationPlan):
    class DeliveryOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            if "freppledb.forecast" in settings.INSTALLED_APPS:
                return (
                    super()
                    .get_queryset()
                    .filter(
                        (Q(demand__isnull=False) | Q(forecast__isnull=False))
                        & Q(owner__isnull=True)
                    )
                )
                # Note: defer screws up the model name when deleting a PO
                # .defer("operation", "owner", "supplier", "location", "origin", "destination")
            else:
                return (
                    super()
                    .get_queryset()
                    .filter(Q(demand__isnull=False) & Q(owner__isnull=True))
                )
                # Note: defer screws up the model name when deleting a PO
                # .defer("operation", "owner", "supplier", "location", "origin", "destination")

    objects = DeliveryOrderManager()

    @classmethod
    def getType(cls):
        return "DLVR"

    def save(self, *args, **kwargs):
        self.type = "DLVR"
        self.supplier = self.origin = self.destination = self.operation = self.owner = (
            None
        )
        if self.demand:
            self.item = self.demand.item
            self.location = self.demand.location
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("delivery order")
        verbose_name_plural = _("delivery orders")


class DistributionOrder(OperationPlan):
    shipping_date = AliasDateTimeField(
        db_column="startdate", verbose_name=_("shipping date"), null=True, blank=True
    )
    receipt_date = AliasDateTimeField(
        db_column="enddate", verbose_name=_("receipt date"), null=True, blank=True
    )

    def __init__(self, *args, **kwargs):
        if "startdate" in kwargs:
            kwargs["shipping_date"] = kwargs["startdate"]
        elif "shipping_date" in kwargs:
            kwargs["startdate"] = kwargs["shipping_date"]
        if "enddate" in kwargs:
            kwargs["receipt_date"] = kwargs["enddate"]
        elif "receipt_date" in kwargs:
            kwargs["enddate"] = kwargs["receipt_date"]
        return super().__init__(*args, **kwargs)

    class DistributionOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="DO")
            # .defer("operation", "owner", "supplier", "location")

    objects = DistributionOrderManager()

    @classmethod
    def getType(cls):
        return "DO"

    def save(self, *args, **kwargs):
        self.type = "DO"
        self.operation = self.owner = self.location = self.supplier = None
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("distribution order")
        verbose_name_plural = _("distribution orders")


class PurchaseOrder(OperationPlan):
    ordering_date = AliasDateTimeField(
        db_column="startdate", verbose_name=_("ordering date"), null=True, blank=True
    )
    receipt_date = AliasDateTimeField(
        db_column="enddate", verbose_name=_("receipt date"), null=True, blank=True
    )

    def __init__(self, *args, **kwargs):
        if "startdate" in kwargs:
            kwargs["ordering_date"] = kwargs["startdate"]
        elif "ordering_date" in kwargs:
            kwargs["startdate"] = kwargs["ordering_date"]
        if "enddate" in kwargs:
            kwargs["receipt_date"] = kwargs["enddate"]
        elif "receipt_date" in kwargs:
            kwargs["enddate"] = kwargs["receipt_date"]
        return super().__init__(*args, **kwargs)

    class PurchaseOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="PO")
            # Note: defer screws up the model name when deleting a PO
            # .defer("operation", "owner", "origin", "destination")

    objects = PurchaseOrderManager()

    @classmethod
    def getType(cls):
        return "PO"

    def save(self, *args, **kwargs):
        self.type = "PO"
        self.operation = self.owner = self.origin = self.destination = None
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("purchase order")
        verbose_name_plural = _("purchase orders")


class ManufacturingOrder(OperationPlan):
    extra_dependencies = [OperationResource]

    class ManufacturingOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="MO")
            # Note: defer screws up the model name when deleting a PO
            # .defer("supplier", "location", "origin", "destination")

    objects = ManufacturingOrderManager()

    @staticmethod
    def parseData(
        data,
        rowmapper,
        user,
        database,
        ping,
        excel_duration_in_days=False,
        skip_audit_log=False,
    ):
        selfReferencing = []

        def formfieldCallback(f):
            # global selfReferencing
            if isinstance(f, RelatedField):
                tmp = BulkForeignKeyFormField(field=f, using=database)
                if f.remote_field.model == ManufacturingOrder:
                    selfReferencing.append(tmp)
                return tmp
            else:
                return f.formfield(localize=True)

        # Initialize
        headers = []
        rownumber = 0
        changed = 0
        added = 0
        content_type_id = ContentType.objects.get_for_model(
            ManufacturingOrder, for_concrete_model=False
        ).pk

        # Call the beforeUpload method if it is defined
        if hasattr(ManufacturingOrder, "beforeUpload"):
            ManufacturingOrder.beforeUpload(database)

        errors = 0
        warnings = 0
        has_pk_field = False
        processed_header = False
        rowWrapper = rowmapper()
        newstyle = (
            Parameter.getValue("NewStyleOrderEditing", database, "false").lower()
            == "true"
        )

        # Detect excel autofilter data tables
        if isinstance(data, Worksheet) and data.auto_filter.ref:
            try:
                bounds = CellRange(data.auto_filter.ref).bounds
            except Exception:
                bounds = None
        else:
            bounds = None

        for row in data:
            rownumber += 1
            if bounds:
                # Only process data in the excel auto-filter range
                if rownumber < bounds[1]:
                    continue
                elif rownumber > bounds[3]:
                    break
                else:
                    rowWrapper.setData(row)
            else:
                rowWrapper.setData(row)

            # Case 1: Skip empty rows
            if rowWrapper.empty():
                continue

            # Case 2: The first line is read as a header line
            elif not processed_header:
                processed_header = True

                # Collect required fields
                required_fields = set()
                for i in ManufacturingOrder._meta.fields:
                    if (
                        not i.blank
                        and i.default == NOT_PROVIDED
                        and not isinstance(i, AutoField)
                    ):
                        required_fields.add(i.name)

                # Validate all columns
                for col in rowWrapper.values():
                    col = str(col).strip().strip("#").lower() if col else ""
                    if col == "":
                        headers.append(None)
                        continue
                    ok = False

                    if col == "resources":
                        headers.append(
                            models.JSONField(
                                name="resource", null=True, blank=True, editable=False
                            )
                        )
                        ok = True
                        continue

                    for i in ManufacturingOrder._meta.fields:
                        # Try with translated field names
                        if (
                            col == i.name.lower()
                            or (
                                isinstance(i, ForeignKey)
                                and col == "%s_id" % i.name.lower()
                            )
                            or col == i.verbose_name.lower()
                            or col
                            == (
                                "%s - %s"
                                % (ManufacturingOrder.__name__, i.verbose_name)
                            ).lower()
                        ):
                            if i.editable is True:
                                headers.append(i)
                            else:
                                headers.append(None)
                            required_fields.discard(i.name)
                            ok = True
                            break
                        if translation.get_language() != "en":
                            # Try with English field names
                            with translation.override("en"):
                                if (
                                    col == i.name.lower()
                                    or (
                                        isinstance(i, ForeignKey)
                                        and col == "%s_id" % i.name.lower()
                                    )
                                    or col == i.verbose_name.lower()
                                    or col
                                    == (
                                        "%s - %s"
                                        % (ManufacturingOrder.__name__, i.verbose_name)
                                    ).lower()
                                ):
                                    if i.editable is True:
                                        headers.append(i)
                                    else:
                                        headers.append(None)
                                    required_fields.discard(i.name)
                                    ok = True
                                    break
                    if not ok:
                        headers.append(None)
                        warnings += 1
                        yield (
                            WARNING,
                            None,
                            None,
                            None,
                            force_str(
                                _("Skipping unknown field %(column)s" % {"column": col})
                            ),
                        )
                    if (
                        col == ManufacturingOrder._meta.pk.name.lower()
                        or col == ManufacturingOrder._meta.pk.verbose_name.lower()
                    ):
                        has_pk_field = True
                if required_fields:
                    # We are missing some required fields
                    errors += 1
                    yield (
                        ERROR,
                        None,
                        None,
                        None,
                        force_str(
                            _(
                                "Some keys were missing: %(keys)s"
                                % {"keys": ", ".join(required_fields)}
                            )
                        ),
                    )
                # Abort when there are errors
                if errors:
                    if isinstance(data, Worksheet) and len(data.parent.sheetnames) > 1:
                        # Skip this sheet an continue with the next one
                        return
                    else:
                        raise NameError("Can't proceed")

                # Create a form class that will be used to validate the data
                fields = [i.name for i in headers if i]
                if hasattr(ManufacturingOrder, "getModelForm"):
                    UploadForm = ManufacturingOrder.getModelForm(
                        tuple(fields), database=database
                    )
                else:
                    UploadForm = modelform_factory(
                        ManufacturingOrder,
                        fields=tuple(fields),
                        formfield_callback=formfieldCallback,
                    )
                rowWrapper = rowmapper(headers)

                # Get natural keys for the class
                natural_key = None
                if hasattr(ManufacturingOrder.objects, "get_by_natural_key"):
                    if ManufacturingOrder._meta.unique_together:
                        natural_key = ManufacturingOrder._meta.unique_together[0]
                    elif hasattr(ManufacturingOrder, "natural_key") and isinstance(
                        ManufacturingOrder.natural_key, tuple
                    ):
                        natural_key = ManufacturingOrder.natural_key

            # Case 3: Process a data row
            else:
                try:
                    # Step 1: Send a ping-alive message to make the upload interruptable
                    if ping:
                        if rownumber % 50 == 0:
                            yield (DEBUG, rownumber, None, None, None)

                    # Step 2: Fill the form with data, either updating an existing
                    # instance or creating a new one.
                    if has_pk_field:
                        # A primary key is part of the input fields
                        try:
                            # Try to find an existing record with the same primary key
                            it = ManufacturingOrder.objects.using(database).get(
                                pk=rowWrapper[ManufacturingOrder._meta.pk.name]
                            )
                            form = UploadForm(rowWrapper, instance=it)
                        except ManufacturingOrder.DoesNotExist:
                            form = UploadForm(rowWrapper)
                            it = None
                    elif natural_key:
                        # A natural key exists for this model
                        try:
                            # Build the natural key
                            key = []
                            for x in natural_key:
                                key.append(rowWrapper.get(x, None))
                            # Try to find an existing record using the natural key
                            it = ManufacturingOrder.objects.get_by_natural_key(*key)
                            form = UploadForm(rowWrapper, instance=it)
                        except ManufacturingOrder.DoesNotExist:
                            form = UploadForm(rowWrapper)
                            it = None
                        except ManufacturingOrder.MultipleObjectsReturned:
                            yield (
                                ERROR,
                                rownumber,
                                None,
                                None,
                                force_str(_("Key fields not unique")),
                            )
                            continue
                    else:
                        # No primary key required for this model
                        form = UploadForm(rowWrapper)
                        it = None

                    # Step 3: Validate the form and model, and save to the database
                    if form.has_changed():
                        if form.is_valid():
                            # Call the update method before saving the model
                            obj = form.save(commit=False)
                            if newstyle and hasattr(ManufacturingOrder, "update"):
                                if it:
                                    ManufacturingOrder.update(
                                        obj, database, **form.cleaned_data
                                    )
                                else:
                                    ManufacturingOrder.update(
                                        obj, database, create=True, **form.cleaned_data
                                    )
                            # Save the form
                            obj = form.save(commit=False)
                            if it:
                                changed += 1
                                obj.save(using=database, force_update=True)
                            else:
                                added += 1
                                obj.save(using=database)
                                # Add the new object in the cache of available keys
                                for x in selfReferencing:
                                    if x.cache is not None and obj.pk not in x.cache:
                                        x.cache[obj.pk] = obj
                            if not skip_audit_log and user:
                                if it:
                                    Comment(
                                        user_id=user.id,
                                        content_type_id=content_type_id,
                                        object_pk=obj.pk,
                                        object_repr=force_str(obj)[:200],
                                        type="change",
                                        comment="Changed %s."
                                        % get_text_list(form.changed_data, "and"),
                                    ).save(using=database)
                                else:
                                    Comment(
                                        user_id=user.id,
                                        content_type_id=content_type_id,
                                        object_pk=obj.pk,
                                        object_repr=force_str(obj)[:200],
                                        type="add",
                                        comment="Added",
                                    ).save(using=database)
                        else:
                            # Validation fails
                            for error in form.non_field_errors():
                                errors += 1
                                yield (ERROR, rownumber, None, None, error)
                            for field in form:
                                for error in field.errors:
                                    errors += 1
                                    yield (
                                        ERROR,
                                        rownumber,
                                        field.name,
                                        rowWrapper[field.name],
                                        error,
                                    )

                except Exception as e:
                    errors += 1
                    yield (ERROR, None, None, None, "Exception during upload: %s" % e)

        yield (
            INFO,
            None,
            None,
            None,
            _(
                "%(rows)d data rows, changed %(changed)d and added %(added)d records, %(errors)d errors, %(warnings)d warnings"
            )
            % {
                "rows": rownumber - 1,
                "changed": changed,
                "added": added,
                "errors": errors,
                "warnings": warnings,
            },
        )

    @classmethod
    def getModelForm(cls, fields, database=DEFAULT_DB_ALIAS):
        template = modelform_factory(
            cls,
            fields=[i for i in fields if i != "resource" and i != "material"],
            formfield_callback=lambda f: (
                isinstance(f, RelatedField) and f.formfield(using=database)
            )
            or f.formfield(),
        )

        if "resource" not in fields and "material" not in fields:
            return template

        # Return a form class with an extra field
        class MO_form(template):
            resource = forms.CharField() if "resource" in fields else None
            material = forms.CharField() if "material" in fields else None

            def clean_resource(self):
                try:
                    cleaned = []
                    for res in ast.literal_eval(self.cleaned_data["resource"]):
                        if isinstance(res, str):
                            rsrc = Resource.objects.all().using(database).get(name=res)
                            cleaned.append((rsrc, 1))
                        else:
                            rsrc = (
                                Resource.objects.all().using(database).get(name=res[0])
                            )
                            cleaned.append((rsrc, res[1]))
                        rsrc.top_rsrc = (
                            Resource.objects.all()
                            .using(database)
                            .get(lvl=0, lft__lte=rsrc.lft, rght__gte=rsrc.rght)
                        )
                    return cleaned
                except Exception:
                    raise forms.ValidationError("Invalid resource")

            def clean_material(self):
                try:
                    cleaned = []
                    for item in ast.literal_eval(self.cleaned_data["material"]):
                        if isinstance(item, str):
                            clean = Item.objects.all().using(database).get(name=item)
                        else:
                            clean = Item.objects.all().using(database).get(name=item[0])
                        cleaned.append(clean)
                    return cleaned
                except Exception:
                    raise forms.ValidationError("Invalid item")

            def save(self, commit=True):
                instance = super(MO_form, self).save(commit=False)

                if "resource" in fields:
                    try:
                        updated_opr = []
                        unchanged_opr = []
                        created_opr = []
                        opr_to_create = []
                        # Make resource assignments unique: [(res1, 1), (res1, 1)] becomes [(res1, 2)]
                        unique_resources = []
                        for r in self.cleaned_data["resource"]:
                            f = None
                            for ur in unique_resources:
                                if ur[0] == r[0]:
                                    f = ur
                                    break
                            if f:
                                unique_resources.append(
                                    (f[0], str(float(f[1]) + float(r[1])))
                                )
                                unique_resources.remove(f)
                            else:
                                unique_resources.append(r)
                        for res, quantity in unique_resources:
                            found = False
                            # Let's see if an opr record already exists for that resource
                            for opplanres in instance.resources.all().select_related(
                                "resource"
                            ):
                                if opplanres.resource.name == res.name:
                                    found = True
                                    if opplanres.quantity != quantity:
                                        opplanres.quantity = quantity
                                        updated_opr.append(opplanres)
                                    else:
                                        unchanged_opr.append(opplanres)
                                    break

                            if not found:
                                # I need to create an opr record for that resource
                                # but I will do it later
                                opr_to_create.append((res, quantity))

                        # I visited all the resources, do I need to delete some unvisited opr records ?
                        deleted_oprs = False
                        for i in instance.resources.all():
                            if i not in updated_opr and i not in unchanged_opr:
                                deleted_oprs = True
                                i.delete()

                        # time now to create the new opr records
                        for i in opr_to_create:
                            created_opr.append(
                                OperationPlanResource(
                                    resource=i[0],
                                    quantity=i[1],
                                    status=instance.status,
                                    operationplan=instance,
                                )
                            )

                        # and to save all that stuff
                        if (
                            commit
                            or len(created_opr)
                            or deleted_oprs
                            or len(updated_opr) > 0
                        ):
                            instance.save(using=database)
                            for i in created_opr:
                                i.save(using=database)
                            for i in updated_opr:
                                i.save(using=database)

                    except Exception as e:
                        pass

                if "material" in fields:
                    try:
                        opmatlist = [
                            opmat
                            for opmat in instance.operation.operationmaterials.all()
                        ]

                        dict = {}
                        for rec in opmatlist:
                            if rec.name:
                                if rec.name not in dict:
                                    dict[rec.name] = [rec.item.name]
                                else:
                                    dict[rec.name].append(rec.item.name)

                        for mat in self.cleaned_data["material"]:
                            Found = False
                            for opplanmat in instance.materials.all().using(database):
                                # find lists where item is:
                                for k in dict.keys():
                                    if (
                                        mat.name in dict[k]
                                        and opplanmat.item.name in dict[k]
                                    ) or mat.name == opplanmat.item.name:
                                        opplanmat.item = mat
                                        opplanmat.save(using=database)
                                        Found = True
                                        break
                                if Found:
                                    break
                    except Exception:
                        pass
                    if commit:
                        instance.save()

                return instance

        return MO_form

    @classmethod
    def getType(cls):
        return "MO"

    def save(self, *args, **kwargs):
        self.type = "MO"
        self.supplier = self.origin = self.destination = None
        if self.operation:
            self.item = self.operation.item
            if not self.item and self.operation.owner:
                self.item = self.operation.owner.item
            self.location = self.operation.location
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("manufacturing order")
        verbose_name_plural = _("manufacturing orders")
