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

from django.db import models
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import AuditModel

from .customer import Customer
from .item import Item
from .location import Location
from .operation import Operation


class Demand(AuditModel):
    # Status
    demandstatus = (
        ("inquiry", _("inquiry")),
        ("quote", _("quote")),
        ("open", _("open")),
        ("closed", _("closed")),
        ("canceled", _("canceled")),
    )

    # Delivery policies
    delivery_policies = (
        ("independent", _("independent")),
        ("alltogether", _("all together")),
        ("inratio", _("in ratio")),
    )

    # Database fields
    name = models.CharField(
        _("name"), max_length=300, primary_key=True, help_text=_("Unique identifier")
    )
    owner = models.CharField(
        _("owner"), max_length=300, null=True, blank=True, db_index=True
    )
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    customer = models.ForeignKey(
        Customer, verbose_name=_("customer"), db_index=True, on_delete=models.CASCADE
    )
    # No index on the item field, because have an index on item + location + customer + due
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        on_delete=models.CASCADE,
        db_index=False,
    )
    location = models.ForeignKey(
        Location, verbose_name=_("location"), db_index=True, on_delete=models.CASCADE
    )
    due = models.DateTimeField(
        _("due"), help_text=_("Due date of the sales order"), db_index=True
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        null=True,
        blank=True,
        choices=demandstatus,
        default="open",
        help_text=_(
            'Status of the demand. Only "open" and "quote" demands are planned'
        ),
    )
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("delivery operation"),
        null=True,
        blank=True,
        related_name="used_demand",
        on_delete=models.SET_NULL,
        help_text=_("Operation used to satisfy this demand"),
    )
    quantity = models.DecimalField(
        _("quantity"), max_digits=20, decimal_places=8, default=1
    )
    priority = models.IntegerField(
        _("priority"),
        default=10,
        help_text=_(
            "Priority of the demand (lower numbers indicate more important demands)"
        ),
    )
    minshipment = models.DecimalField(
        _("minimum shipment"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Minimum shipment quantity when planning this demand"),
    )
    maxlateness = models.DurationField(
        _("maximum lateness"),
        null=True,
        blank=True,
        help_text=_("Maximum lateness allowed when planning this demand"),
    )
    policy = models.CharField(
        _("policy"),
        max_length=15,
        null=True,
        blank=True,
        choices=delivery_policies,
        default="independent",
        help_text=_("Defines how sales orders are shipped together"),
    )
    batch = models.CharField(
        _("batch"),
        max_length=300,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("MTO batch name"),
    )
    delay = models.DurationField(_("delay"), null=True, blank=True, editable=False)
    plannedquantity = models.DecimalField(
        _("planned quantity"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        editable=False,
        help_text=_("Quantity planned for delivery"),
    )
    deliverydate = models.DateTimeField(
        _("delivery date"),
        help_text=_("Delivery date of the demand"),
        null=True,
        blank=True,
        editable=False,
    )
    plan = models.JSONField(default=dict, null=True, blank=True, editable=False)

    # Convenience methods
    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "demand"
        verbose_name = _("sales order")
        verbose_name_plural = _("sales orders")
        ordering = ["name"]
        indexes = [
            models.Index(
                fields=["item", "location", "customer", "due"], name="demand_sorted"
            )
        ]
