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

from freppledb.common.models import AuditModel, MultiDBManager

from .calendar import Calendar
from .item import Item
from .location import Location


class Buffer(AuditModel):
    # Types of buffers
    types = (("default", _("default")), ("infinite", _("infinite")))

    # Fields common to all buffer types
    id = models.AutoField(_("identifier"), primary_key=True)
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    type = models.CharField(
        _("type"),
        max_length=20,
        null=True,
        blank=True,
        choices=types,
        default="default",
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        db_index=True,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    batch = models.CharField(
        _("batch"), max_length=300, null=True, blank=True, default=""
    )
    onhand = models.DecimalField(
        _("onhand"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="0.00",
        help_text=_("current inventory"),
    )
    minimum = models.DecimalField(
        _("minimum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="0.00",
        help_text=_("safety stock"),
    )
    minimum_calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("minimum calendar"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar storing a time-dependent safety stock profile"),
    )
    min_interval = models.DurationField(
        _("min_interval"),
        null=True,
        blank=True,
        help_text=_("Batching window for grouping replenishments in batches"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, item, location, batch):
            return self.get(item=item, location=location, batch=batch or "")

    def natural_key(self):
        return (self.item, self.location, self.batch or "")

    objects = Manager()

    def validate_unique(self, exclude=None):
        if self.batch is None:
            self.batch = ""
        super().validate_unique(exclude=exclude)

    def __str__(self):
        return "%s @ %s" % (self.item.name, self.location.name)

    class Meta(AuditModel.Meta):
        db_table = "buffer"
        verbose_name = _("buffer")
        verbose_name_plural = _("buffers")
        ordering = ["item", "location", "batch"]
        unique_together = (("item", "location", "batch"),)
