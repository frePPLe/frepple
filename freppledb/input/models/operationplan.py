#
# Copyright (C) 2007-2013 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
from django.db.models.fields import AutoField, NOT_PROVIDED
from django.db.models.fields.related import RelatedField
from django.forms.models import modelform_factory
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.utils.encoding import force_str
from django.utils.text import get_text_list

from freppledb.common.dataload import BulkForeignKeyFormField
from freppledb.common.fields import AliasDateTimeField
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

    def collectCalendars(self) -> List[Calendar]:
        if self.type == "PO":
            return PurchaseOrder.collectCalendars(self)
        elif self.type == "DO":
            return DistributionOrder.collectCalendars(self)
        elif self.type == "DLVR":
            return DeliveryOrder.collectCalendars(self)
        else:
            return ManufacturingOrder.collectCalendars(self)

    def calculateOperationTime(
        self, refdate, duration, forward=True, interruptions=None
    ) -> datetime:
        # Replicate Operation::calculateOperationTime:
        if not duration or not refdate:
            return refdate
        cals = self.collectCalendars()
        if not cals:
            if forward:
                return refdate + (duration or timedelta(0))
            else:
                return refdate - (duration or timedelta(0))
        else:
            if len(cals) > 1:
                logger.warning("Only a single calendar is supported right now")
            timecounter = duration
            st = refdate
            if forward:
                while st.year <= 2030:
                    nd = st + duration * 2
                    for event in cals[0].getEvents(st, nd):
                        if event[5]:
                            delta = event[1] - event[0]
                            if delta >= timecounter:
                                return event[0] + timecounter
                            else:
                                timecounter -= delta
                        elif interruptions is not None:
                            if interruptions and interruptions[-1][1] == event[0]:
                                interruptions[-1][1] = event[1]
                            else:
                                interruptions.append([event[0], event[1]])
                    st = nd
                return datetime(2030, 12, 31)
            else:
                while st.year >= 1971:
                    nd = st - duration * 2
                    for event in reversed(cals[0].getEvents(nd, st)):
                        if event[5]:
                            delta = event[1] - event[0]
                            if delta >= timecounter:
                                return event[1] - timecounter
                            else:
                                timecounter -= delta
                        elif interruptions is not None:
                            if interruptions and interruptions[-1][1] == event[0]:
                                interruptions[-1][1] = event[1]
                            else:
                                interruptions.append([event[0], event[1]])
                    st = nd
                return datetime(1971, 1, 1)

    def getEfficiency(self, when):
        eff = 100.0
        for r in self.resources.all().using(self._state.db or DEFAULT_DB_ALIAS):
            if r.resource.efficiency_calendar:
                t = r.resource.efficiency_calendar.findBucket(when)
                if t:
                    v = t.value
                else:
                    v = r.resource.efficiency_calendar.defaultvalue
            else:
                v = r.resource.efficiency
            if v and v > 0.0 and v < eff:
                eff = float(v)
        return eff / 100.0

    def update(self, database, delete=False, create=False, **fields):
        if self.type == "PO":
            PurchaseOrder.update(self, database, delete=delete, create=create, **fields)
        elif self.type == "DO":
            DistributionOrder.update(
                self, database, delete=delete, create=create, **fields
            )
        elif self.type == "DLVR":
            DeliveryOrder.update(self, database, delete=delete, create=create, **fields)
        else:
            ManufacturingOrder.update(
                self, database, delete=delete, create=create, **fields
            )
        # TODO handle change of STCK operationplan with an update of the buffer

    def _propagateDependencies(self, database, updateParent=True):
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                with cte as (
                  select
                    operationplan.reference,
                    operationplan.operation_id,
                    operationplan.startdate,
                    operationplan.enddate,
                    jsonb_array_elements(operationplan.plan->'downstream_opplans') as dwnstrm,
                    jsonb_array_elements(operationplan.plan->'upstream_opplans') as upstrm
                  from operationplan
                  where reference = %%s
                  )
                select
                   1, operationplan.reference,
                   coalesce(cte.enddate + operation_dependency.hard_safety_leadtime, cte.enddate)
                from cte
                inner join operationplan
                  on operationplan.reference = cte.dwnstrm->>1
                inner join operation_dependency
                  on cte.operation_id = operation_dependency.blockedby_id
                  and operationplan.operation_id = operation_dependency.operation_id
                where dwnstrm->>0 in ('1' %s)
                and operationplan.startdate < coalesce(cte.enddate + operation_dependency.hard_safety_leadtime, cte.enddate)
                and (operationplan.status is null or operationplan.status in ('approved', 'proposed'))
                union all
                select
                   2, operationplan.reference,
                   coalesce(cte.startdate - operation_dependency.hard_safety_leadtime, cte.startdate)
                from cte
                inner join operationplan
                  on operationplan.reference = cte.upstrm->>1
                inner join operation_dependency
                  on cte.operation_id = operation_dependency.operation_id
                  and operationplan.operation_id = operation_dependency.blockedby_id
                where upstrm->>0 in ('1' %s)
                and operationplan.enddate > coalesce(cte.startdate - operation_dependency.hard_safety_leadtime, cte.startdate)
                and (operationplan.status is null or operationplan.status in ('approved', 'proposed'))
                """
                % ((",'2'", ",'2'") if self.owner else ("", "")),
                (self.reference,),
            )
            for rec in cursor.fetchall():
                try:
                    depopplan = OperationPlan.objects.using(database).get(
                        reference=rec[1]
                    )
                    if rec[0] == 1:
                        # Move successor step later
                        depopplan.startdate = rec[2]
                        depopplan.update(database, startdate=rec[2])
                    else:
                        # Move predecessor step early
                        depopplan.enddate = rec[2]
                        depopplan.update(database, enddate=rec[2])
                    depopplan.save(using=database)
                    depopplan._propagateDependencies(database)
                except OperationPlan.DoesNotExist:
                    pass

            if self.operation.type == "routing":
                # Update children
                for ch in self.xchildren.all().using(database):
                    ch._propagateDependencies(database, updateParent=False)
            if self.owner:
                # Update parent
                parentdates = (
                    self.owner.xchildren.all()
                    .using(database)
                    .aggregate(models.Max("enddate"), models.Min("startdate"))
                )
                self.owner.startdate = parentdates["startdate__min"]
                self.owner.enddate = parentdates["enddate__max"]
                self.owner.save(using=database, update_fields=("startdate", "enddate"))
                if updateParent:
                    self.owner._propagateDependencies(database)

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

    def update(self, database, delete=False, create=False, **fields):
        if not self.operationplan:
            return
        delta = {}
        if "operationplan__startdate" in fields:
            delta["startdate"] = datetime.strptime(
                fields["operationplan__startdate"], "%Y-%m-%d %H:%M:%S"
            )
            self.operationplan.startdate = delta["startdate"]
        if "operationplan__enddate" in fields:
            delta["enddate"] = datetime.strptime(
                fields["operationplan__enddate"], "%Y-%m-%d %H:%M:%S"
            )
            self.operationplan.enddate = delta["enddate"]
        if "operationplan__status" in fields:
            delta["status"] = fields["operationplan__status"]
            self.operationplan.status = delta["status"]
        if "operationplan__quantity" in fields:
            delta["quantity"] = fields["operationplan__quantity"]
            self.operationplan.quantity = delta["quantity"]
        if delta:
            self.operationplan.update(
                database=database, delete=delete, create=create, **delta
            )
            self.operationplan.save(using=database)
        if "quantity" in fields:
            self.quantity = fields["quantity"]
            self.save(using=database)

    def updateResourcePlan(self, database, delete=False):

        with connections[database].cursor() as cursor:
            if self.resource.type is None or self.resource.type == "default":

                # default value of parameter is hours
                try:
                    p = (
                        Parameter.objects.using(database)
                        .get(name="loading_time_units")
                        .value
                    )
                    if p == "days":
                        time_unit = 3600 / 24
                    elif p == "weeks":
                        time_unit = 3600 / 24 / 7
                    else:
                        time_unit = 3600
                except Exception:
                    time_unit = 3600

                sql = """
                    with resource_hierachy as (
                        with recursive cte as (
                        select name as child, owner_id as parent from resource
                        where not exists (select 1 from resource res where owner_id = resource.name)
                        union all
                        select cte.child, resource.owner_id from resource
                        inner join cte on resource.name = cte.parent)
                        select * from cte
                    ),
                    working_time as (
                        select
                        operationplanresource.resource_id,
                        out_resourceplan.startdate,
                        -- working time
                        sum(operationresource.quantity * case when tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day')
                        * tstzrange(operationplan.startdate, operationplan.enddate, '[]') =
                        tstzrange(operationplan.startdate, operationplan.enddate, '[]')
                        then operationplan.enddate - operationplan.startdate
                        else upper(tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day')
                                * tstzrange(operationplan.startdate, operationplan.enddate, '[]'))
                                - lower(tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day')
                                        * tstzrange(operationplan.startdate, operationplan.enddate, '[]')) end) working_time
                        from operationplanresource
                        inner join (select  reference,
                                            startdate,
                                            enddate,
                                            plan,
                                            operation_id from operationplan
                                            where startdate <= enddate and reference != %%s
                                    %s
                                            ) operationplan on operationplan.reference = operationplanresource.operationplan_id

                        inner join resource_hierachy on resource_hierachy.child = operationplanresource.resource_id

                        inner join operationresource on
                            operationplan.operation_id = operationresource.operation_id
                            and (operationresource.resource_id = resource_hierachy.child or
                                operationresource.resource_id = resource_hierachy.parent)

                        inner join out_resourceplan on out_resourceplan.resource = operationplanresource.resource_id

                        where operationplanresource.resource_id = %%s

                        group by operationplanresource.resource_id,
                        out_resourceplan.startdate),
                    interruptions as (
                        select
                        operationplanresource.resource_id,
                        out_resourceplan.startdate,
                        sum(coalesce(
                        operationresource.quantity *
                        case when tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day')
                        * interruption_range = interruption_range
                        then upper(interruption_range) - lower(interruption_range)
                        else upper(tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day') * interruption_range)
                        -lower(tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day') * interruption_range) end
                        , interval '0 second')) as interruptions
                        from operationplanresource
                        inner join (select  reference,
                                            startdate,
                                            enddate,
                                            plan,
                                            operation_id from operationplan
                                            where startdate <= enddate and reference != %%s
                                    %s
                                            ) operationplan on operationplan.reference = operationplanresource.operationplan_id

                        inner join resource_hierachy on resource_hierachy.child = operationplanresource.resource_id

                        inner join operationresource on
                            operationplan.operation_id = operationresource.operation_id
                            and (operationresource.resource_id = resource_hierachy.child or
                                operationresource.resource_id = resource_hierachy.parent)

                        inner join out_resourceplan on out_resourceplan.resource = operationplanresource.resource_id

                        left join lateral
                        (select tstzrange((t->>0)::timestamp at time zone %%s, (t->>1)::timestamp at time zone %%s) as interruption_range
                        from jsonb_array_elements(plan->'interruptions') t) t on t.interruption_range
                                                    && tstzrange(out_resourceplan.startdate, out_resourceplan.startdate + interval '1 day')

                        where operationplanresource.resource_id = %%s
                        group by operationplanresource.resource_id,
                        out_resourceplan.startdate
                    )
                    update out_resourceplan
                    set load = case when available = 0 then 0 else
                    coalesce(extract(epoch from (select working_time from working_time where startdate = out_resourceplan.startdate))/%%s, 0)
                    - coalesce(extract(epoch from (select interruptions from interruptions where startdate = out_resourceplan.startdate))/%%s, 0) end,
                    free = greatest(available - (coalesce(extract(epoch from (select working_time from working_time where startdate = out_resourceplan.startdate))/%%s, 0)
                    - coalesce(extract(epoch from (select interruptions from interruptions where startdate = out_resourceplan.startdate))/%%s, 0)),0)
                    where resource = %%s
                    and (load != case when available = 0 then 0 else
                    coalesce(extract(epoch from (select working_time from working_time where startdate = out_resourceplan.startdate))/%%s, 0)
                    - coalesce(extract(epoch from (select interruptions from interruptions where startdate = out_resourceplan.startdate))/%%s, 0) end
                    or free != greatest(available - (coalesce(extract(epoch from (select working_time from working_time where startdate = out_resourceplan.startdate))/%%s, 0)
                    - coalesce(extract(epoch from (select interruptions from interruptions where startdate = out_resourceplan.startdate))/%%s, 0)),0))
                    """ % (
                    (
                        """union all
                                    select %s reference,
                                            %s startdate,
                                            %s enddate,
                                            %s plan,
                                            %s operation_id
                                            """
                    )
                    if not delete
                    else "",
                    (
                        """union all
                                    select %s reference,
                                            %s startdate,
                                            %s enddate,
                                            %s plan,
                                            %s operation_id
                                            """
                    )
                    if not delete
                    else "",
                )

                cursor.execute(
                    sql,
                    (self.operationplan.reference,)
                    + (
                        (
                            self.operationplan.reference,
                            self.operationplan.startdate,
                            self.operationplan.enddate,
                            json.dumps(self.operationplan.plan),
                            self.operationplan.operation.name,
                        )
                        if not delete
                        else tuple()
                    )
                    + (
                        self.resource.name,
                        self.operationplan.reference,
                    )
                    + (
                        (
                            self.operationplan.reference,
                            self.operationplan.startdate,
                            self.operationplan.enddate,
                            json.dumps(self.operationplan.plan),
                            self.operationplan.operation.name,
                        )
                        if not delete
                        else tuple()
                    )
                    + (
                        settings.TIME_ZONE,
                        settings.TIME_ZONE,
                        self.resource.name,
                        time_unit,
                        time_unit,
                        time_unit,
                        time_unit,
                        self.resource.name,
                        time_unit,
                        time_unit,
                        time_unit,
                        time_unit,
                    ),
                )
            elif "bucket" in self.resource.type:
                sql = """
                    with opplanres as (
                        select cb.startdate, sum(operationplanresource.quantity) as quantity from operationplanresource
                        inner join (select  reference,
                                            startdate from operationplan
                                            where startdate <= enddate and reference != %%s
                                    %s
                                            ) operationplan on operationplan.reference = operationplanresource.operationplan_id

                        inner join common_bucketdetail cb on cb.bucket_id = 'day' and tstzrange(cb.startdate, cb.enddate, '[)') @>
                            operationplan.startdate

                        where operationplanresource.resource_id = %%s

                        group by cb.startdate
                        )
                    insert into out_resourceplan (resource, startdate, available, unavailable, setup, load, free)
                    select %%s, opplanres.startdate, 0, 0, 0, opplanres.quantity, 0 from opplanres
                    on conflict(resource, startdate) do update
                    set load = excluded.load,
                    free = greatest(0, out_resourceplan.available - excluded.load)
                """ % (
                    (
                        """union all
                                    select %s reference,
                                            %s startdate
                                            """
                    )
                    if not delete
                    else "",
                )
                cursor.execute(
                    sql,
                    (self.operationplan.reference,)
                    + (
                        (
                            self.operationplan.reference,
                            self.operationplan.startdate,
                        )
                        if not delete
                        else tuple()
                    )
                    + (
                        self.resource.name,
                        self.resource.name,
                    ),
                )

            # we need to update the parent resources in the hierarchy
            # a first query to get recursively the owners
            cursor.execute(
                """
            with recursive cte as (
            select 1 as lvl, %s::varchar as name
            union all
            select cte.lvl+1, owner_id
                from resource
                inner join cte on cte.name = resource.name)
            select name from cte where cte.name is not null
            and cte.lvl > 1
            order by lvl
            """,
                (self.resource.name,),
            )
            # A second query to update the resource plan of the owner
            owners = []
            for i in cursor:
                owners.append(i[0])
            for i in owners:
                cursor.execute(
                    """
                with cte as (
                    select  out_resourceplan.startdate,
                            sum(available) available,
                            sum(unavailable) unavailable,
                            sum(setup) setup,
                            sum(load) load,
                            sum(free) free
                    from out_resourceplan
                    where resource in (select name from resource where owner_id = %s)
                    group by startdate)
                update out_resourceplan
                set available = cte.available,
                unavailable = cte.unavailable,
                setup = cte.setup,
                load = cte.load,
                free = cte.free
                from cte
                where out_resourceplan.startdate = cte.startdate
                and out_resourceplan.resource = %s
                and (out_resourceplan.available != cte.available
                    or out_resourceplan.unavailable != cte.unavailable
                    or out_resourceplan.setup != cte.setup
                    or out_resourceplan.load != cte.load
                    or out_resourceplan.free != cte.free)
                    """,
                    (i, i),
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

    def update(self, database, delete=False, create=False, **fields):
        if not self.operationplan:
            return
        delta = {}
        if "operationplan__startdate" in fields:
            delta["startdate"] = datetime.strptime(
                fields["operationplan__startdate"], "%Y-%m-%d %H:%M:%S"
            )
            self.operationplan.startdate = delta["startdate"]
        if "operationplan__enddate" in fields:
            delta["enddate"] = datetime.strptime(
                fields["operationplan__enddate"], "%Y-%m-%d %H:%M:%S"
            )
            self.operationplan.enddate = delta["enddate"]
        if "operationplan__status" in fields:
            delta["status"] = fields["operationplan__status"]
            self.operationplan.status = delta["status"]
        if "operationplan__quantity" in fields:
            delta["quantity"] = fields["operationplan__quantity"]
            self.operationplan.quantity = delta["quantity"]
        if delta:
            self.operationplan.update(
                database=database, delete=delete, create=create, **delta
            )
            self.operationplan.save(using=database)

    @staticmethod
    def updateOnhand(item_name, location_name, database):
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                with cte as (
                    select
                        operationplanmaterial.id,
                        sum(operationplanmaterial.quantity)
                        over (
                            partition by operationplanmaterial.item_id,
                              operationplanmaterial.location_id,
                              operationplan.batch
                            order by flowdate, operationplanmaterial.quantity desc, operationplanmaterial.id
                            ) as cumul,
                        (
                        select safetystock from (
                            select 1 as priority, coalesce(
                            (select calendarbucket.value
                                from calendarbucket
                                where calendar_id = 'SS for '||operationplanmaterial.item_id||' @ '||operationplanmaterial.location_id
                                and operationplanmaterial.flowdate >= startdate
                                and operationplanmaterial.flowdate < enddate
                                order by priority limit 1),
                            (select defaultvalue
                                from calendar
                                where name = 'SS for '||operationplanmaterial.item_id||' @ '||operationplanmaterial.location_id)
                            ) as safetystock
                            union all
                            select 2 as priority, coalesce(
                            (select calendarbucket.value
                                from calendarbucket
                                where calendarbucket.calendar_id = buffer.minimum_calendar_id
                                and operationplanmaterial.flowdate >= calendarbucket.startdate
                                and operationplanmaterial.flowdate < calendarbucket.enddate
                                order by priority limit 1),
                            (select defaultvalue
                                from calendar
                                where name = buffer.minimum_calendar_id)
                            ) as safetystock
                            union all
                            select 3 as priority, coalesce(buffer.minimum, 0)
                            ) t
                            where t.safetystock is not null
                            order by priority
                            limit 1
                        ) as minimum
                    from operationplanmaterial
                    inner join operationplan
                      on operationplanmaterial.operationplan_id = operationplan.reference
                    left outer join buffer on buffer.item_id = operationplanmaterial.item_id
                      and buffer.location_id = operationplanmaterial.location_id
                      and (
                        buffer.batch = ''
                        or buffer.batch is null
                        or buffer.batch = operationplan.batch
                        )
                    where operationplanmaterial.item_id = %s
                      and operationplanmaterial.location_id = %s
                    )
                update operationplanmaterial
                  set onhand = cte.cumul, minimum = cte.minimum
                from cte
                where cte.id = operationplanmaterial.id
                  and (
                    cte.cumul is distinct from operationplanmaterial.onhand
                    or cte.minimum is distinct from operationplanmaterial.minimum
                  )
                """,
                (item_name, location_name),
            )


class DeliveryOrder(OperationPlan):
    class DeliveryOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return (
                super().get_queryset().filter(demand__isnull=False, owner__isnull=True)
            )
            # Note: defer screws up the model name when deleting a PO
            # .defer("operation", "owner", "supplier", "location", "origin", "destination")

    objects = DeliveryOrderManager()

    @classmethod
    def getType(cls):
        return "DLVR"

    def save(self, *args, **kwargs):
        self.type = "DLVR"
        self.supplier = (
            self.origin
        ) = self.destination = self.operation = self.owner = None
        if self.demand:
            self.item = self.demand.item
            self.location = self.demand.location
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("delivery order")
        verbose_name_plural = _("delivery orders")

    def collectCalendars(self):
        if hasattr(self, "_calendars"):
            return self._calendars
        self._calendars = []
        if self.location and self.location.available:
            self._calendars.append(self.location.available)
        return self._calendars

    def update(self, database, delete=False, create=False, **fields):
        # Assure the start date, end date and quantity are consistent
        if not delete:
            interruptions = []
            if "enddate" in fields:
                # Mode 1: End date (optionally also quantity) given -> compute start date
                self.startdate = self.calculateOperationTime(
                    self.enddate, timedelta(0), False, interruptions
                )
            else:
                # Mode 2: Start date (optionally also quantity) given -> compute end date
                self.enddate = self.calculateOperationTime(
                    self.startdate, timedelta(0), True, interruptions
                )
            if interruptions:
                self.plan["interruptions"] = [
                    (
                        i[0].strftime("%Y-%m-%d %H:%M:%S"),
                        i[1].strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    for i in interruptions
                ]
            else:
                self.plan.pop("interruptions", None)

        # Create or update operationplanmaterial records
        if (
            delete
            or not self.item
            or not self.location
            or not self.enddate
            or not self.quantity
            or not self.demand
        ):
            recs = [
                (i.item.name, i.location.name, database)
                for i in self.materials.using(database).all()
            ]
            self.materials.using(database).delete()
            for i in recs:
                OperationPlanMaterial.updateOnhand(*i)
        elif self.enddate:
            recs = [
                (i.item.name, i.location.name, database)
                for i in self.materials.using(database).all()
                if i.item != self.demand.item or i.location != self.demand.location
            ]
            self.materials.using(database).delete()
            for i in recs:
                OperationPlanMaterial.updateOnhand(*i)
            OperationPlanMaterial(
                operationplan=self,
                quantity=self.quantity,
                flowdate=self.enddate,
                item=self.demand.item,
                location=self.demand.location,
            ).save(using=database)
            OperationPlanMaterial.updateOnhand(
                self.demand.item.name, self.demand.location.name, database
            )


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

    def collectCalendars(self):
        state = getattr(self, "_state", None)
        db = state.db if state else DEFAULT_DB_ALIAS
        if hasattr(self, "_calendars"):
            return self._calendars
        self._calendars = []
        if self.destination and self.destination.available:
            # 1. Destination calendar
            self._calendars.append(self.destination.available)
        itemdist = self.itemdistribution(db)
        if itemdist and itemdist.resource:
            if (
                itemdist.resource.available
                and itemdist.resource.available not in self._calendars
            ):
                # 2. resource calendar
                self._calendars.append(itemdist.resource.available)
            if (
                itemdist.resource.location
                and itemdist.resource.location.available
                and itemdist.resource.location.available not in self._calendars
            ):
                # 3. resource location calendar
                self._calendars.append(itemdist.resource.location.available)
        return self._calendars

    def itemdistribution(self, database=DEFAULT_DB_ALIAS):
        if hasattr(self, "_itemdistribution"):
            return self._itemdistribution
        item = self.item
        while item:
            for i in item.distributions.all().using(database).order_by("priority"):
                if self.destination == i.location and (
                    self.origin == i.origin or not self.origin
                ):
                    self._itemdistribution = i
                    return self._itemdistribution
            item = item.owner
        self._itemdistribution = None
        return self._itemdistribution

    def update(self, database, delete=False, create=False, **fields):
        itemdistribution = self.itemdistribution(database)

        # Computed fields
        change = not delete and not create
        self.name = "Ship %s%s%s to %s" % (
            self.item.name if self.item else "no-item",
            " @ %s" % self.batch if self.batch else "",
            " from %s " % self.origin.name if self.origin else "",
            self.destination.name if self.destination else "no-destination",
        )

        # Process quantity changes
        if (
            (create or (change and "quantity" in fields))
            and itemdistribution
            and (
                self.status
                in (
                    "approved",
                    "proposed",
                )
                or not self.status
            )
        ):
            if self.quantity < 0:
                self.quantity = 0
            sizemin = Decimal(
                itemdistribution.sizeminimum
                if itemdistribution.sizeminimum is not None
                else Decimal(1)
            )
            if self.quantity < sizemin:
                if itemdistribution.sizemultiple and itemdistribution.sizemultiple > 0:
                    # Round up from minimum
                    self.quantity = itemdistribution.sizemultiple * math.ceil(
                        sizemin / itemdistribution.sizemultiple
                    )
                else:
                    self.quantity = sizemin
            if (
                itemdistribution.sizemaximum is not None
                and itemdistribution.sizemaximum > 0
                and itemdistribution.sizemaximum >= self.quantity
            ):
                if itemdistribution.sizemultiple and itemdistribution.sizemultiple > 0:
                    # Round down from maximim
                    self.quantity = itemdistribution.sizemultiple * math.floor(
                        itemdistribution.sizemaximum / itemdistribution.sizemultiple
                    )
                    if self.quantity < sizemin:
                        # No multiple found between min and max.
                        # Use the multiple to break out of this.
                        self.quantity = itemdistribution.sizemultiple
                else:
                    self.quantity = itemdistribution.sizemaximum
            elif itemdistribution.sizemultiple and itemdistribution.sizemultiple > 0:
                # Round up to a multiple
                self.quantity = itemdistribution.sizemultiple * math.ceil(
                    self.quantity / itemdistribution.sizemultiple
                )

        # Assure the start date, end date and quantity are consistent
        if not delete:
            interruptions = []
            if "enddate" in fields or "receipt_date" in fields:
                # Mode 1: End date (optionally also quantity) given -> compute start date
                self.startdate = self.calculateOperationTime(
                    self.enddate,
                    itemdistribution.leadtime if itemdistribution else timedelta(0),
                    False,
                    interruptions,
                )
            else:
                # Mode 2: Start date (optionally also quantity) given -> compute end date
                self.enddate = self.calculateOperationTime(
                    self.startdate,
                    itemdistribution.leadtime if itemdistribution else timedelta(0),
                    True,
                    interruptions,
                )
            if interruptions:
                self.plan["interruptions"] = [
                    (
                        i[0].strftime("%Y-%m-%d %H:%M:%S"),
                        i[1].strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    for i in interruptions
                ]
            else:
                self.plan.pop("interruptions", None)

        # Create or update operationplanmaterial records
        if not self.item:
            recs = [
                (i.item.name, i.location.name, database)
                for i in self.materials.using(database).all()
            ]
            self.materials.all().using(database).delete()
            for i in recs:
                OperationPlanMaterial.updateOnhand(*i)
        else:
            if self.origin and self.startdate:
                recs = [
                    (i.item.name, i.location.name, database)
                    for i in self.materials.using(database).all()
                    if i.quantity < 0
                    and (i.item != self.item or i.location != self.origin)
                ]
                self.materials.all().using(database).filter(quantity__lt=0).delete()
                for i in recs:
                    OperationPlanMaterial.updateOnhand(*i)
                OperationPlanMaterial(
                    operationplan=self,
                    quantity=-self.quantity,
                    flowdate=self.startdate,
                    item=self.item,
                    location=self.origin,
                ).save(using=database)
                OperationPlanMaterial.updateOnhand(
                    self.item.name, self.origin.name, database
                )
            else:
                recs = [
                    (i.item.name, i.location.name, database)
                    for i in self.materials.using(database).all()
                    if i.quantity < 0
                ]
                self.materials.all().using(database).filter(quantity__lt=0).delete()
                for i in recs:
                    OperationPlanMaterial.updateOnhand(*i)
            if self.destination and self.enddate:
                recs = [
                    (i.item.name, i.location.name, database)
                    for i in self.materials.using(database).all()
                    if i.quantity < 0
                    and (i.item != self.item or i.location != self.destination)
                ]
                self.materials.all().using(database).filter(quantity__gt=0).delete()
                for i in recs:
                    OperationPlanMaterial.updateOnhand(*i)
                self.materials.all().using(database).filter(quantity__gt=0).delete()
                OperationPlanMaterial(
                    operationplan=self,
                    quantity=self.quantity,
                    flowdate=self.enddate,
                    item=self.item,
                    location=self.destination,
                ).save(using=database)
                OperationPlanMaterial.updateOnhand(
                    self.item.name, self.destination.name, database
                )
            else:
                recs = [
                    (i.item.name, i.location.name, database)
                    for i in self.materials.using(database).all()
                    if i.quantity > 0
                ]
                self.materials.all().using(database).filter(quantity__gt=0).delete()
                for i in recs:
                    OperationPlanMaterial.updateOnhand(*i)

        # Create or update operationplanresource records
        if delete or not itemdistribution or not itemdistribution.resource:
            for i in self.resources.using(database).all():
                i.updateResourcePlan(database, True)
            self.resources.using(database).delete()
        else:
            recs = 0
            self._resources = []
            if change:
                for i in self.resources.using(database).all():
                    self._resources.append(i)
                    i.update(
                        database,
                        quantity=(self.quantity or Decimal(0))
                        * (itemdistribution.resource_qty or Decimal(1)),
                        resource=itemdistribution.resource,
                    )
                    recs += 1
                if recs > 1:
                    self._resources.clear()
                    for i in self.resources.using(database).all():
                        i.updateResourcePlan(database, True)
                        self.resources.using(database).delete()
            if create or (change and recs != 1):
                OperationPlanResource(
                    operationplan=self,
                    quantity=(self.quantity or Decimal(0))
                    * (itemdistribution.resource_qty or Decimal(1)),
                    resource=itemdistribution.resource,
                ).save(using=database)
                self._resources += [
                    OperationPlanResource.objects.using(database).get(
                        operationplan=self
                    )
                ]

            # update resource plan
            for i in self._resources:
                i.operationplan = self
                i.updateResourcePlan(database)


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

    def collectCalendars(self):
        state = getattr(self, "_state", None)
        db = state.db if state else DEFAULT_DB_ALIAS
        if hasattr(self, "_calendars"):
            return self._calendars
        self._calendars = []
        if self.supplier and self.supplier.available:
            # 1. Supplier calendar
            self._calendars.append(self.supplier.available)
        itemsup = self.itemsupplier(db)
        if itemsup and itemsup.resource:
            if (
                itemsup.resource.available
                and itemsup.resource.available not in self._calendars
            ):
                # 2. resource calendar
                self._calendars.append(itemsup.resource.available)
            if (
                itemsup.resource.location
                and itemsup.resource.location.available
                and itemsup.resource.location.available not in self._calendars
            ):
                # 3. resource location calendar
                self._calendars.append(itemsup.resource.location.available)
        return self._calendars

    def itemsupplier(self, database=DEFAULT_DB_ALIAS):
        if hasattr(self, "_itemsupplier"):
            return self._itemsupplier
        item = self.item
        while item:
            for i in item.itemsuppliers.all().using(database).order_by("priority"):
                if self.supplier == i.supplier and (
                    self.location == i.location or not i.location
                ):
                    self._itemsupplier = i
                    return self._itemsupplier
            item = item.owner
        self._itemsupplier = None
        return self._itemsupplier

    def update(self, database, delete=False, create=False, **fields):
        itemsupplier = self.itemsupplier(database)

        # Computed fields
        change = not delete and not create
        self.name = "Purchase %s%s @ %s%s" % (
            self.item.name if self.item else "no-item",
            " @ %s" % self.batch if self.batch else "",
            self.location.name if self.location else "no-location",
            " from %s" % self.supplier.name if self.supplier else "",
        )

        # Process quantity changes
        if (
            (create or (change and "quantity" in fields))
            and itemsupplier
            and (
                self.status
                in (
                    "approved",
                    "proposed",
                )
                or not self.status
            )
        ):
            if self.quantity < 0:
                self.quantity = 0
            sizemin = Decimal(
                itemsupplier.sizeminimum
                if itemsupplier.sizeminimum is not None
                else Decimal(1)
            )
            if self.quantity < sizemin:
                if itemsupplier.sizemultiple and itemsupplier.sizemultiple > 0:
                    # Round up from minimum
                    self.quantity = itemsupplier.sizemultiple * math.ceil(
                        sizemin / itemsupplier.sizemultiple
                    )
                else:
                    self.quantity = sizemin
            if (
                itemsupplier.sizemaximum is not None
                and itemsupplier.sizemaximum > 0
                and itemsupplier.sizemaximum >= self.quantity
            ):
                if itemsupplier.sizemultiple and itemsupplier.sizemultiple > 0:
                    # Round down from maximim
                    self.quantity = itemsupplier.sizemultiple * math.floor(
                        itemsupplier.sizemaximum / itemsupplier.sizemultiple
                    )
                    if self.quantity < sizemin:
                        # No multiple found between min and max.
                        # Use the multiple to break out of this.
                        self.quantity = itemsupplier.sizemultiple
                else:
                    self.quantity = itemsupplier.sizemaximum
            elif itemsupplier.sizemultiple and itemsupplier.sizemultiple > 0:
                # Round up to a multiple
                self.quantity = itemsupplier.sizemultiple * math.ceil(
                    self.quantity / itemsupplier.sizemultiple
                )

        # Assure the start date, end date and quantity are consistent
        if not delete:
            interruptions = []
            if "enddate" in fields or "receipt_date" in fields:
                # Mode 1: End date (optionally also quantity) given -> compute start date
                self.startdate = self.calculateOperationTime(
                    self.enddate,
                    itemsupplier.leadtime if itemsupplier else timedelta(0),
                    False,
                    interruptions,
                )
            else:
                # Mode 2: Start date (optionally also quantity) given -> compute end date
                self.enddate = self.calculateOperationTime(
                    self.startdate,
                    itemsupplier.leadtime if itemsupplier else timedelta(0),
                    True,
                    interruptions,
                )
            if interruptions:
                self.plan["interruptions"] = [
                    (
                        i[0].strftime("%Y-%m-%d %H:%M:%S"),
                        i[1].strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    for i in interruptions
                ]
            else:
                self.plan.pop("interruptions", None)

        # Create or update operationplanmaterial records
        if (
            delete
            or not self.item
            or not self.location
            or not self.enddate
            or not self.quantity
        ):
            recs = [
                (i.item.name, i.location.name, database)
                for i in self.materials.using(database).all()
            ]
            self.materials.using(database).delete()
            for i in recs:
                OperationPlanMaterial.updateOnhand(*i)
        elif self.enddate:
            recs = 0
            if (
                itemsupplier
                and itemsupplier.hard_safety_leadtime
                and itemsupplier.hard_safety_leadtime > timedelta(0)
            ):
                d = self.calculateOperationTime(
                    self.enddate, itemsupplier.hard_safety_leadtime, forward=True
                )
            else:
                d = self.enddate
            recs = [
                (i.item.name, i.location.name, database)
                for i in self.materials.using(database).all()
                if i.item != self.item or i.location != self.location
            ]
            self.materials.using(database).delete()
            for i in recs:
                OperationPlanMaterial.updateOnhand(*i)
            OperationPlanMaterial(
                operationplan=self,
                quantity=self.quantity,
                flowdate=d,
                item=self.item,
                location=self.location,
            ).save(using=database)
            OperationPlanMaterial.updateOnhand(
                self.item.name,
                self.location.name,
                database,
            )

        # Create or update operationplanresource records
        if delete or not itemsupplier or not itemsupplier.resource:
            for i in self.resources.using(database).all():
                i.updateResourcePlan(database, True)
            self.resources.using(database).delete()
        else:
            recs = 0
            self._resources = []
            if change:
                for i in self.resources.using(database).all():
                    self._resources.append(i)
                    i.update(
                        database,
                        quantity=(self.quantity or Decimal(0))
                        * (itemsupplier.resource_qty or Decimal(1)),
                        resource=itemsupplier.resource,
                    )
                    recs += 1
                if recs > 1:
                    self._resources.clear()
                    for i in self.resources.using(database).all():
                        i.updateResourcePlan(database, True)
                        self.resources.using(database).delete()
            if create or (change and recs != 1):
                OperationPlanResource(
                    operationplan=self,
                    quantity=(self.quantity or Decimal(0))
                    * (itemsupplier.resource_qty or Decimal(1)),
                    resource=itemsupplier.resource,
                ).save(using=database)
                self._resources += [
                    OperationPlanResource.objects.using(database).get(
                        operationplan=self
                    )
                ]

            # update resource plan
            for i in self._resources:
                i.operationplan = self
                i.updateResourcePlan(database)


class ManufacturingOrder(OperationPlan):

    extra_dependencies = [OperationResource]

    class ManufacturingOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="MO")
            # Note: defer screws up the model name when deleting a PO
            # .defer("supplier", "location", "origin", "destination")

    objects = ManufacturingOrderManager()

    @staticmethod
    def parseData(data, rowmapper, user, database, ping):

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
                            if user:
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

                new_opr = []
                if "resource" in fields:
                    try:
                        opreslist = [
                            r
                            for r in instance.operation.operationresources.all().select_related(
                                "resource"
                            )
                        ]
                        for res, quantity in self.cleaned_data["resource"]:
                            newopres = None
                            for o in opreslist:
                                if o.resource.lft <= res.lft < o.resource.rght:
                                    newopres = o
                                    break
                            found = False
                            for opplanres in instance.resources.all().select_related(
                                "resource"
                            ):
                                found = True
                                oldopres = None
                                for o in opreslist:
                                    if (
                                        o.resource.lft
                                        <= opplanres.resource.lft
                                        < o.resource.rght
                                    ):
                                        oldopres = o
                                        break
                                if (
                                    oldopres
                                    and newopres
                                    and (
                                        oldopres.id == newopres.id
                                        or (
                                            oldopres.name == newopres.name
                                            and newopres.name
                                        )
                                    )
                                ):
                                    opplanres.resource = res
                                    opplanres.save(using=database)
                                    break
                            # record creation, no operationplanresource exists
                            if not found:
                                opr = OperationPlanResource(
                                    resource=res,
                                    quantity=quantity,
                                    status=instance.status,
                                    operationplan=instance,
                                    startdate=instance.startdate,
                                    enddate=instance.enddate,
                                )
                                new_opr.append(opr)

                    except Exception:
                        pass
                    if commit or len(new_opr) > 0:
                        instance.save(using=database)
                        for i in new_opr:
                            i.save(using=database)

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

    def collectCalendars(self):
        state = getattr(self, "_state", None)
        db = state.db if state else DEFAULT_DB_ALIAS
        if hasattr(self, "_calendars"):
            return self._calendars
        self._calendars = []
        if self.operation:
            if self.operation.available:
                # 1. Operation calendar
                self._calendars.append(self.operation.available)
            if (
                self.operation.location
                and self.operation.location.available
                and self.operation.location.available not in self._calendars
            ):
                # 2. Operation location calendar
                self._calendars.append(self.operation.location.available)
        ldplns_exist = False
        for r in self.resources.using(db).all():
            if r.resource.available and r.resource.available not in self._calendars:
                # 3. resource calendar
                self._calendars.append(r.resource.available)
            if (
                r.resource.location
                and r.resource.location.available
                and r.resource.location.available not in self._calendars
            ):
                # 4. resource location calendar
                self._calendars.append(r.resource.location.available)
            ldplns_exist = True
        if not ldplns_exist:
            for r in self.operation.operationresources.using(db).all():
                if r.resource.available and r.resource.available not in self._calendars:
                    # 3. resource calendar
                    self._calendars.append(r.resource.available)
                if (
                    r.resource.location
                    and r.resource.location.available
                    and r.resource.location.available not in self._calendars
                ):
                    # 4. resource location calendar
                    self._calendars.append(r.resource.location.available)
        return self._calendars

    def update(self, database, delete=False, create=False, **fields):

        # Computed fields
        change = not delete and not create
        self.name = self.operation.name if self.operation else "no-operation"

        # Process quantity changes
        if (
            (create or (change and "quantity" in fields))
            and self.operation
            and (
                self.status
                in (
                    "approved",
                    "proposed",
                )
                or not self.status
            )
        ):
            if self.quantity < 0:
                self.quantity = 0
            sizemin = Decimal(
                self.operation.sizeminimum
                if self.operation.sizeminimum is not None
                else Decimal(1)
            )
            if self.quantity < sizemin:
                if self.operation.sizemultiple and self.operation.sizemultiple > 0:
                    # Round up from minimum
                    self.quantity = self.operation.sizemultiple * math.ceil(
                        sizemin / self.operation.sizemultiple
                    )
                else:
                    self.quantity = sizemin
            if (
                self.operation.sizemaximum is not None
                and self.operation.sizemaximum > 0
                and self.operation.sizemaximum >= self.quantity
            ):
                if self.operation.sizemultiple and self.operation.sizemultiple > 0:
                    # Round down from maximim
                    self.quantity = self.operation.sizemultiple * math.floor(
                        self.operation.sizemaximum / self.operation.sizemultiple
                    )
                    if self.quantity < sizemin:
                        # No multiple found between min and max.
                        # Use the multiple to break out of this.
                        self.quantity = self.operation.sizemultiple
                else:
                    self.quantity = self.operation.sizemaximum
            elif self.operation.sizemultiple and self.operation.sizemultiple > 0:
                # Round up to a multiple
                self.quantity = self.operation.sizemultiple * math.ceil(
                    self.quantity / self.operation.sizemultiple
                )

        # Create or update operationplanresource records.
        # We need to do this before computing the efficiency and duration.
        if delete or not self.operation:
            for i in self.resources.using(database).all():
                i.updateResourcePlan(database, True)
                i.delete()
            self._resources = []
        else:
            self._resources = [r for r in self.resources.using(database).all()]
            if not self._resources:
                # Create new opplanres records
                for r in self.operation.operationresources.using(database).all():
                    rsrc = r.getPreferredResource()
                    if not rsrc:
                        # We may not find a resource that has the required skill
                        continue
                    if "bucket" in rsrc.type:
                        qty = (self.quantity or Decimal(0)) * (r.quantity or Decimal(0))
                    else:
                        qty = r.quantity or Decimal(1)
                    self._resources.append(
                        OperationPlanResource(
                            operationplan=self, resource=rsrc, quantity=qty
                        )
                    )
            else:
                # update quantity for opr records of bucketized resources
                for opr in self._resources:
                    if "bucket" in opr.resource.type:
                        for r in self.operation.operationresources.using(
                            database
                        ).all():
                            rsrc = r.getPreferredResource()
                            if rsrc == opr.resource:
                                opr.quantity = (self.quantity or Decimal(0)) * (
                                    r.quantity or Decimal(0)
                                ) + (r.quantity_fixed or Decimal(0))

        dependencies = (
            not delete
            and OperationDependency.objects.using(database)
            .filter(
                models.Q(operation__owner=self.operation.owner)
                | models.Q(blockedby__owner=self.operation.owner)
            )
            .exists()
        )

        # Assure the start date, end date and quantity are consistent
        if not delete:
            if "startdate" in fields:
                efficiency = self.getEfficiency(self.startdate)
            elif "enddate" in fields:
                efficiency = self.getEfficiency(self.enddate)
            else:
                efficiency = self.getEfficiency(self.startdate)

            if not self.operation:
                duration = timedelta(0)
            elif self.operation.type == "time_per" or not self.operation.type:
                duration = (
                    (self.operation.duration or timedelta(0))
                    + (self.operation.duration_per or timedelta(0))
                    * float(self.quantity)
                ) / efficiency
            elif self.operation.type == "fixed_time":
                duration = (self.operation.duration or timedelta(0)) / efficiency
            elif self.operation.type == "routing":
                if create:
                    # Create the child operationplans
                    # Can be tricky when we do this in a bulk upload that already has child MOs
                    pass
                else:
                    # Pass updates from parent to child operationplan
                    delta = {}
                    if "quantity" in fields:
                        delta["quantity"] = self.quantity
                    if "status" in fields:
                        delta["status"] = self.status
                    if "enddate" in fields:
                        delta["enddate"] = self.enddate
                        delta["noparentupdate"] = True
                        if dependencies:
                            # Update the final dependencies in the routing
                            for ch in self.xchildren.all().using(database):
                                if (
                                    ch.status not in ("approved", "proposed")
                                    or ch.operation.dependents.all()
                                    .using(database)
                                    .filter(operation__owner=self.operation)
                                    .exists()
                                ):
                                    continue
                                if "quantity" in delta:
                                    ch.quantity = self.quantity
                                if "status" in delta:
                                    ch.status = delta["status"]
                                ch.enddate = fields["enddate"]
                                ch.update(database, **delta)
                                ch.save(using=database)
                        else:
                            # Update the sequence of steps, starting from the last one
                            for ch in (
                                self.xchildren.all()
                                .using(database)
                                .order_by("-operation__priority")
                            ):
                                ch.quantity = self.quantity
                                if ch.status in ("approved", "proposed"):
                                    ch.enddate = delta["enddate"]
                                else:
                                    del delta["enddate"]
                                if "status" in delta:
                                    ch.status = delta["status"]
                                ch.update(database, **delta)
                                delta["enddate"] = ch.startdate
                                ch.save(using=database)
                            if ch:
                                self.startdate = ch.startdate
                    elif "startdate" in fields or "quantity" in fields:
                        delta["startdate"] = self.startdate
                        delta["noparentupdate"] = True
                        if dependencies:
                            # Update the initial dependencies in the routing
                            for ch in self.xchildren.all().using(database):
                                if (
                                    ch.status not in ("approved", "proposed")
                                    or ch.operation.dependencies.all()
                                    .using(database)
                                    .filter(blockedby__owner=self.operation)
                                    .exists()
                                ):
                                    continue
                                if "quantity" in delta:
                                    ch.quantity = self.quantity
                                if "status" in delta:
                                    ch.status = delta["status"]
                                ch.startdate = delta["startdate"]
                                ch.update(database, **delta)
                                ch.save(using=database)
                        else:
                            # Update the sequence of steps, starting from the last one
                            for ch in (
                                self.xchildren.all()
                                .using(database)
                                .order_by("operation__priority")
                            ):
                                if "quantity" in delta:
                                    ch.quantity = self.quantity
                                if ch.status in ("approved", "proposed"):
                                    ch.startdate = delta["startdate"]
                                else:
                                    del delta["startdate"]
                                if "status" in delta:
                                    ch.status = delta["status"]
                                ch.update(database, **delta)
                                ch.save(using=database)
                                delta["startdate"] = ch.enddate
                            if ch:
                                self.enddate = ch.enddate
                    elif delta:
                        for ch in self.xchildren.all().using(database):
                            ch.quantity = self.quantity
                            if "status" in delta:
                                ch.status = delta["status"]
                            ch.update(database, **delta)
                            ch.save(using=database)
                    parentdates = (
                        self.xchildren.all()
                        .using(database)
                        .aggregate(models.Max("enddate"), models.Min("startdate"))
                    )
                    self.startdate = parentdates["startdate__min"]
                    self.enddate = parentdates["enddate__max"]
                    self.save(
                        using=database,
                        update_fields=("startdate", "enddate"),
                    )
            else:
                raise Exception(
                    "Can't change manufacturing orders of type %s yet"
                    % self.operation.type
                )

            if self.operation.type != "routing":
                interruptions = []
                unavailable = timedelta(0)
                if "enddate" in fields:
                    # Mode 1: End date (optionally also quantity) given -> compute start date
                    self.startdate = self.calculateOperationTime(
                        self.enddate, duration, False, interruptions
                    )
                else:
                    # Mode 2: Start date (optionally also quantity) given -> compute end date
                    self.enddate = self.calculateOperationTime(
                        self.startdate, duration, True, interruptions
                    )
                if interruptions:
                    self.plan["interruptions"] = [
                        (
                            i[0].strftime("%Y-%m-%d %H:%M:%S"),
                            i[1].strftime("%Y-%m-%d %H:%M:%S"),
                        )
                        for i in interruptions
                    ]
                    for i in interruptions:
                        unavailable += i[1] - i[0]
                    self.plan["unavailable"] = int(unavailable.total_seconds())
                else:
                    self.plan.pop("interruptions", None)
                    self.plan.pop("unavailable", None)

        # Propagate dependencies
        if dependencies and change:
            self.save(using=database)  # Unfortunately, saving twice
            self._propagateDependencies(database)
        elif (
            change
            and self.owner
            and self.operation.owner
            and self.operation.owner.type == "routing"
            and "noparentupdate" not in fields
        ):
            # Keep the timing of a following routing step consistent
            found = False
            self.save(using=database)  # Unfortunately, saving twice
            # Backward propagation before the current step
            prevstep = None
            for x in (
                self.owner.xchildren.all()
                .using(database)
                .order_by("-operation__sequence")
            ):
                if x.reference == self.reference:
                    found = True
                elif (
                    found
                    and prevstep
                    and (x.enddate > prevstep.startdate or "quantity" in fields)
                ):
                    if x.enddate > prevstep.startdate:
                        x.enddate = prevstep.startdate
                    x.quantity = prevstep.quantity
                    x.update(
                        database,
                        enddate=x.enddate,
                        quantity=self.quantity,
                        noparentupdate=True,
                    )
                    x.save(using=database)
                prevstep = x

            # Forward propagation after the current step
            prevstep = None
            for x in (
                self.owner.xchildren.all()
                .using(database)
                .order_by("operation__sequence")
            ):
                if x.reference == self.reference:
                    found = True
                elif (
                    found
                    and prevstep
                    and (x.startdate < prevstep.enddate or "quantity" in fields)
                ):
                    if x.startdate < prevstep.enddate:
                        x.startdate = prevstep.enddate
                    x.quantity = prevstep.quantity
                    x.update(
                        database,
                        startdate=x.startdate,
                        quantity=x.quantity,
                        noparentupdate=True,
                    )
                    x.save(using=database)
                prevstep = x

            # Update parent
            parentdates = (
                self.owner.xchildren.all()
                .using(database)
                .aggregate(models.Max("enddate"), models.Min("startdate"))
            )
            self.owner.startdate = parentdates["startdate__min"]
            self.owner.enddate = parentdates["enddate__max"]
            if "quantity" in fields:
                self.owner.quantity = self.quantity
            self.owner.save(
                using=database,
                update_fields=("quantity", "startdate", "enddate"),
            )

        # Propagate the deletion of child operationplans
        if delete and self.operation.type == "routing":
            for ch in self.xchildren.all().using(database):
                ch.update(database, delete=True)

        # Create or update operationplanmaterial records
        if delete or not self.operation or not self.quantity:
            self.materials.using(database).delete()
        else:
            has_opplanmat_records = False
            if self.status and self.status in ("confirmed"):
                # Update existing operationplanmaterial records, even if they
                # are not in sync with the operationmaterial definition.
                for fl in self.materials.all():
                    if fl.quantity > Decimal(0):
                        fl.flowdate = self.enddate
                    else:
                        fl.flowdate = self.startdate
                    fl.save(update_fields=["flowdate"], using=database)
                    has_opplanmat_records = True
                    OperationPlanMaterial.updateOnhand(
                        fl.item.name, fl.location.name, database
                    )
            else:
                recs = [
                    (i.item.name, i.location.name, database)
                    for i in self.materials.using(database).all()
                ]
                self.materials.using(database).all().delete()
                for i in recs:
                    OperationPlanMaterial.updateOnhand(*i)
            if not has_opplanmat_records:
                # Create new opplanmat records
                produced = False
                for fl in self.operation.operationmaterials.using(database).all():
                    if fl.type == "transfer_batch":
                        continue
                    if fl.type == "start" and not self.startdate:
                        continue
                    if fl.type == "end" and not self.enddate:
                        continue
                    if fl.offset:
                        d = self.calculateOperationTime(
                            self.enddate if fl.type == "end" else self.startdate,
                            fl.offset,
                            forward=True,
                        )
                    else:
                        d = self.enddate if fl.type == "end" else self.startdate
                    if (fl.quantity and fl.quantity > Decimal(0)) or (
                        fl.quantity_fixed and fl.quantity_fixed > Decimal(0)
                    ):
                        produced = True
                    OperationPlanMaterial(
                        operationplan=self,
                        quantity=self.quantity * (fl.quantity or Decimal(0))
                        + (fl.quantity_fixed or Decimal(0)),
                        flowdate=d,
                        item=fl.item,
                        location=self.operation.location,
                    ).save(using=database)
                    OperationPlanMaterial.updateOnhand(
                        fl.item.name, self.operation.location.name, database
                    )
                if not produced and self.operation.item and self.enddate:
                    # Automatic produce material if not explicitly specified
                    OperationPlanMaterial(
                        operationplan=self,
                        quantity=self.quantity,
                        flowdate=self.enddate,
                        item=self.operation.item,
                        location=self.operation.location,
                    ).save(using=database)
                    OperationPlanMaterial.updateOnhand(
                        self.operation.item.name, self.operation.location.name, database
                    )

            # Save or create operationplanresource records
            for r in self._resources:
                r.save(using=database)
                r.updateResourcePlan(database)
