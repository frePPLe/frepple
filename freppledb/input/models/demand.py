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
        _("name"), primary_key=True, help_text=_("Unique identifier")
    )
    owner = models.CharField(_("owner"), null=True, blank=True, db_index=True)
    description = models.CharField(_("description"), null=True, blank=True)
    category = models.CharField(_("category"), null=True, blank=True, db_index=True)
    subcategory = models.CharField(
        _("subcategory"), null=True, blank=True, db_index=True
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
    quantity = models.DecimalField(_("quantity"), max_digits=20, decimal_places=8)
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
        null=True,
        blank=True,
        choices=delivery_policies,
        default="independent",
        help_text=_("Defines how sales orders are shipped together"),
    )
    batch = models.CharField(
        _("batch"),
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
