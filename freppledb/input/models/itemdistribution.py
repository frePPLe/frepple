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

from django.db import models
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import AuditModel, MultiDBManager

from .item import Item
from .location import Location
from .resource import Resource


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
