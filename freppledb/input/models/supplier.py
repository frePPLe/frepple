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

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import HierarchyModel, AuditModel, MultiDBManager

from ..models.calendar import Calendar
from ..models.item import Item
from ..models.location import Location
from ..models.resource import Resource


class Supplier(AuditModel, HierarchyModel):
    # Database fields
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    available = models.ForeignKey(
        Calendar,
        verbose_name=_("available"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar defining the working hours and holidays"),
    )

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "supplier"
        verbose_name = _("supplier")
        verbose_name_plural = _("suppliers")
        ordering = ["name"]


class ItemSupplier(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        related_name="itemsuppliers",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=True,
        blank=True,
        db_index=True,
        related_name="itemsuppliers",
        on_delete=models.CASCADE,
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name=_("supplier"),
        db_index=True,
        related_name="suppliers",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    leadtime = models.DurationField(
        _("lead time"), null=True, blank=True, help_text=_("Purchasing lead time")
    )
    extra_safety_leadtime = models.DurationField(
        _("soft safety lead time"),
        null=True,
        blank=True,
        help_text=_("soft safety lead time"),
    )
    hard_safety_leadtime = models.DurationField(
        _("hard safety lead time"),
        null=True,
        blank=True,
        help_text=_("hard safety lead time"),
    )
    sizeminimum = models.DecimalField(
        _("size minimum"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        default="1.0",
        help_text=_("A minimum purchasing quantity"),
    )
    sizemultiple = models.DecimalField(
        _("size multiple"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A multiple purchasing quantity"),
    )
    sizemaximum = models.DecimalField(
        _("size maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A maximum purchasing quantity"),
    )
    batchwindow = models.DurationField(
        _("batching window"),
        null=True,
        blank=True,
        help_text=_(
            "Proposed purchase orders within this window will be grouped together"
        ),
        default=timedelta(days=7),
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Purchasing cost per unit"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority among all alternates"),
    )
    effective_start = models.DateTimeField(
        _("effective start"),
        null=True,
        blank=True,
        help_text=_("Validity start date"),
        default=datetime(1971, 1, 1),
    )
    effective_end = models.DateTimeField(
        _("effective end"),
        null=True,
        blank=True,
        help_text=_("Validity end date"),
        default=datetime(2030, 12, 31),
    )
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        null=True,
        blank=True,
        db_index=True,
        related_name="itemsuppliers",
        on_delete=models.SET_NULL,
        help_text=_("Resource to model the supplier capacity"),
    )
    resource_qty = models.DecimalField(
        _("resource quantity"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="1.0",
        help_text=_("Resource capacity consumed per purchased unit"),
    )
    fence = models.DurationField(
        _("fence"),
        null=True,
        blank=True,
        help_text=_("Frozen fence for creating new procurements"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, item, location, supplier, effective_start):
            if location:
                return self.get(
                    item=item,
                    location=location,
                    supplier=supplier,
                    effective_start=effective_start or datetime(1971, 1, 1),
                )
            else:
                return self.get(
                    item=item,
                    location__isnull=True,
                    supplier=supplier,
                    effective_start=effective_start or datetime(1971, 1, 1),
                )

    def natural_key(self):
        return (
            self.item,
            self.location,
            self.supplier,
            self.effective_start or datetime(1971, 1, 1),
        )

    def validate_unique(self, exclude=None):
        if self.effective_start is None:
            self.effective_start = datetime(1971, 1, 1)
        if self.location is None and self._state.adding:
            # Django doesn't check unique partial indices
            if (
                ItemSupplier.objects.using(self._state.db)
                .filter(item=self.item)
                .filter(location__isnull=True)
                .filter(supplier=self.supplier)
                .filter(effective_start=self.effective_start)
                .exists()
            ):
                raise ValidationError(
                    "item, supplier and effective start date already exist"
                )
        super().validate_unique(exclude=exclude)

    objects = Manager()

    def __str__(self):
        return "%s - %s - %s" % (
            self.supplier.name if self.supplier else "No supplier",
            self.item.name if self.item else "No item",
            self.location.name if self.location else "Any location",
        )

    class Meta(AuditModel.Meta):
        db_table = "itemsupplier"
        unique_together = (("item", "location", "supplier", "effective_start"),)
        constraints = [
            UniqueConstraint(
                fields=["item", "supplier", "effective_start"],
                name="itemsupplier_partial2",
                condition=Q(location__isnull=True),
            ),
        ]
        verbose_name = _("item supplier")
        verbose_name_plural = _("item suppliers")
