#
# Copyright (C) 2020 by frePPLe bv
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

from django.db import models
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import MultiDBManager


class ArchiveManager(models.Model):
    """
    This class allows to manage archived data
    """

    snapshot_date = models.DateTimeField(
        "snapshot date", null=False, blank=False, db_index=True, primary_key=True
    )
    total_records = models.IntegerField("total_records")
    buffer_records = models.IntegerField("buffer_records")
    demand_records = models.IntegerField("demand_records")
    operationplan_records = models.IntegerField("operationplan_records")

    class Meta:
        db_table = "ax_manager"
        verbose_name = "archive manager"
        verbose_name_plural = "archive managers"
        ordering = ["snapshot_date"]
        default_permissions = ()


class ArchivedModel(models.Model):
    """
    This is an abstract base model used to archive data
    """

    allow_report_manager_access = True

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    snapshot_date = models.ForeignKey(
        ArchiveManager,
        verbose_name="snapshot date",
        db_index=True,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    objects = MultiDBManager()  # The default manager.

    class Meta:
        abstract = True


class ArchivedBuffer(ArchivedModel):
    item = models.CharField(_("item"))
    location = models.CharField(_("location"))
    batch = models.CharField(_("batch"), null=True, blank=True)
    cost = models.DecimalField(
        _("cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    onhand = models.DecimalField(
        _("onhand"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    safetystock = models.DecimalField(
        _("safety stock"), null=True, blank=True, max_digits=20, decimal_places=8
    )

    def __str__(self):
        return "Archived %s @ %s @ %s" % (self.item, self.location, self.snapshot_date)

    class Meta:
        db_table = "ax_buffer"
        verbose_name = "archived buffer"
        verbose_name_plural = "archived buffers"
        ordering = ["item", "location", "batch"]
        default_permissions = ()
        # Specify explicitly which indices we want.
        # By default django extra ones which our queries don't use.
        indexes = [
            models.Index(fields=["item"], name="ax_buffer_item_idx"),
            models.Index(fields=["location"], name="ax_buffer_location_idx"),
        ]


class ArchivedDemand(ArchivedModel):
    name = models.CharField(_("name"))
    item = models.CharField(_("item"))
    cost = models.DecimalField(
        _("cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    location = models.CharField(_("location"))
    customer = models.CharField(_("customer"))
    due = models.DateTimeField(_("due"))
    status = models.CharField(_("status"), null=True, blank=True)
    priority = models.IntegerField(_("priority"))
    quantity = models.DecimalField(_("quantity"), max_digits=20, decimal_places=8)
    deliverydate = models.DateTimeField(_("delivery date"), null=True, blank=True)
    quantityplanned = models.DecimalField(
        _("planned quantity"), max_digits=20, decimal_places=8, null=True, blank=True
    )

    def __str__(self):
        return "Archived %s @ %s" % (self.name, self.snapshot_date)

    class Meta:
        db_table = "ax_demand"
        verbose_name = "archived sales order"
        verbose_name_plural = "archived sales orders"
        ordering = ["priority", "due"]
        default_permissions = ()
        # Specify explicitly which indices we want.
        # By default django extra ones which our queries don't use.
        indexes = [
            models.Index(fields=["customer"], name="ax_demand_customer_idx"),
            models.Index(fields=["item"], name="ax_demand_item_idx"),
            models.Index(fields=["location"], name="ax_demand_location_idx"),
        ]


class ArchivedOperationPlan(ArchivedModel):
    reference = models.CharField(_("reference"))
    status = models.CharField(_("status"), null=True, blank=True)
    type = models.CharField(_("type"))
    quantity = models.DecimalField(_("quantity"), max_digits=20, decimal_places=8)
    startdate = models.DateTimeField(
        _("start date"), help_text=_("start date"), null=True, blank=True
    )
    enddate = models.DateTimeField(
        _("end date"), help_text=_("end date"), null=True, blank=True
    )
    # Used only for manufacturing orders
    operation = models.CharField(_("operation"), blank=True, null=True)
    owner = models.CharField(_("owner"), null=True, blank=True)
    batch = models.CharField(_("batch"), null=True, blank=True)
    # Used for purchase orders and distribution orders
    item = models.CharField(_("item"))
    item_cost = models.DecimalField(
        _("item cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    itemsupplier_cost = models.DecimalField(
        _("itemsupplier cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    # Used only for distribution orders
    origin = models.CharField(_("origin"), null=True, blank=True)
    destination = models.CharField(_("destination"), null=True, blank=True)
    # Used only for purchase orders
    supplier = models.CharField(_("supplier"), null=True, blank=True)
    location = models.CharField(_("location"), null=True, blank=True)
    # Used for delivery operationplans
    demand = models.CharField(_("demand"), null=True, blank=True)
    due = models.DateTimeField(_("due"), null=True, blank=True)
    name = models.CharField(_("name"), null=True, blank=True)

    def __str__(self):
        return "Archived %s @ %s" % (self.reference, self.snapshot_date)

    class Meta:
        db_table = "ax_operationplan"
        verbose_name = "operationplan"
        verbose_name_plural = "operationplans"
        ordering = ["reference"]
        default_permissions = ()
        # Specify explicitly which indices we want.
        # By default django extra ones which our queries don't use.
        indexes = [
            models.Index(fields=["destination"], name="ax_opplan_destination_idx"),
            models.Index(fields=["item"], name="ax_opplan_item_idx"),
            models.Index(fields=["type"], name="ax_opplan_type_idx"),
            models.Index(fields=["name"], name="ax_opplan_name_idx"),
        ]
