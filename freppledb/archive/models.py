#
# Copyright (C) 2020 by frePPLe bv
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

from django.db import models
from django.utils.translation import gettext as _

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


class ArchivedModel(models.Model):
    """
    This is an abstract base model used to archive data
    """

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

    item = models.CharField(_("item"), max_length=300, db_index=True)
    location = models.CharField(_("location"), max_length=300, db_index=True)
    batch = models.CharField(_("batch"), max_length=300, null=True, blank=True)
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


class ArchivedDemand(ArchivedModel):

    name = models.CharField(_("name"), max_length=300)
    item = models.CharField(_("item"), max_length=300, db_index=True)
    cost = models.DecimalField(
        _("cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    location = models.CharField(_("location"), max_length=300, db_index=True)
    customer = models.CharField(_("customer"), max_length=300, db_index=True)
    due = models.DateTimeField(_("due"))
    status = models.CharField(_("status"), max_length=10, null=True, blank=True)
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


class ArchivedOperationPlan(ArchivedModel):

    reference = models.CharField(_("reference"), max_length=300)
    status = models.CharField(_("status"), null=True, blank=True, max_length=20)
    type = models.CharField(_("type"), max_length=5, db_index=True)
    quantity = models.DecimalField(_("quantity"), max_digits=20, decimal_places=8)
    startdate = models.DateTimeField(
        _("start date"), help_text=_("start date"), null=True, blank=True
    )
    enddate = models.DateTimeField(
        _("end date"), help_text=_("end date"), null=True, blank=True
    )
    # Used only for manufacturing orders
    operation = models.CharField(_("operation"), max_length=300, blank=True, null=True)
    owner = models.CharField(_("owner"), max_length=300, null=True, blank=True)
    batch = models.CharField(_("batch"), max_length=300, null=True, blank=True)
    # Used for purchase orders and distribution orders
    item = models.CharField(_("item"), max_length=300, db_index=True)
    item_cost = models.DecimalField(
        _("item cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    itemsupplier_cost = models.DecimalField(
        _("itemsupplier cost"), null=True, blank=True, max_digits=20, decimal_places=8
    )
    # Used only for distribution orders
    origin = models.CharField(_("origin"), max_length=300, null=True, blank=True)
    destination = models.CharField(
        _("destination"), max_length=300, db_index=True, null=True, blank=True
    )
    # Used only for purchase orders
    supplier = models.CharField(_("supplier"), max_length=300, null=True, blank=True)
    location = models.CharField(_("location"), max_length=300, null=True, blank=True)
    # Used for delivery operationplans
    demand = models.CharField(_("demand"), max_length=300, null=True, blank=True)
    due = models.DateTimeField(_("due"), null=True, blank=True)
    name = models.CharField(
        _("name"), max_length=1000, null=True, blank=True, db_index=True
    )

    def __str__(self):
        return "Archived %s @ %s" % (self.reference, self.snapshot_date)

    class Meta:
        db_table = "ax_operationplan"
        verbose_name = "operationplan"
        verbose_name_plural = "operationplans"
        ordering = ["reference"]
