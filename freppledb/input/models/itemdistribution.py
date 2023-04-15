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

from django.db import models
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import AuditModel, MultiDBManager

from ..models.item import Item
from ..models.location import Location
from ..models.resource import Resource


class ItemDistribution(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        related_name="distributions",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=False,
        blank=False,
        db_index=True,
        related_name="itemdistributions_destination",
        on_delete=models.CASCADE,
        help_text=_("Destination location to be replenished"),
    )
    origin = models.ForeignKey(
        Location,
        verbose_name=_("origin"),
        on_delete=models.CASCADE,
        db_index=True,
        related_name="itemdistributions_origin",
        help_text=_("Source location shipping the item"),
    )
    leadtime = models.DurationField(
        _("lead time"), null=True, blank=True, help_text=_("Transport lead time")
    )
    sizeminimum = models.DecimalField(
        _("size minimum"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        default="1.0",
        help_text=_("A minimum shipping quantity"),
    )
    sizemultiple = models.DecimalField(
        _("size multiple"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A multiple shipping quantity"),
    )
    sizemaximum = models.DecimalField(
        _("size maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A maximum shipping quantity"),
    )
    batchwindow = models.DurationField(
        _("batching window"),
        null=True,
        blank=True,
        help_text=_(
            "Proposed distribution orders within this window will be grouped together"
        ),
        default=timedelta(days=7),
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Shipping cost per unit"),
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
        related_name="itemdistributions",
        on_delete=models.SET_NULL,
        help_text=_("Resource to model the distribution capacity"),
    )
    resource_qty = models.DecimalField(
        _("resource quantity"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="1.0",
        help_text=_("Resource capacity consumed per distributed unit"),
    )
    fence = models.DurationField(
        _("fence"),
        null=True,
        blank=True,
        help_text=_("Frozen fence for creating new shipments"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, item, location, origin, effective_start):
            return self.get(
                item=item,
                location=location,
                origin=origin,
                effective_start=effective_start or datetime(1971, 1, 1),
            )

    def natural_key(self):
        return (
            self.item,
            self.location,
            self.origin,
            self.effective_start or datetime(1971, 1, 1),
        )

    def validate_unique(self, exclude=None):
        if self.effective_start is None:
            self.effective_start = datetime(1971, 1, 1)
        super().validate_unique(exclude=exclude)

    objects = Manager()

    def __str__(self):
        return "%s - %s - %s" % (
            self.location.name if self.location else "Any destination",
            self.item.name if self.item else "No item",
            self.origin.name if self.origin else "No origin",
        )

    class Meta(AuditModel.Meta):
        db_table = "itemdistribution"
        unique_together = (("item", "location", "origin", "effective_start"),)
        verbose_name = _("item distribution")
        verbose_name_plural = _("item distributions")
