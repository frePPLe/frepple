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
    description = models.CharField(_("description"), null=True, blank=True)
    category = models.CharField(_("category"), null=True, blank=True, db_index=True)
    subcategory = models.CharField(
        _("subcategory"), null=True, blank=True, db_index=True
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
            if not hasattr(self, "item") or not hasattr(self, "supplier"):
                raise ValidationError("Some required fields are missing")
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
