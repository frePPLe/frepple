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

from freppledb.common.models import AuditModel, MultiDBManager

from ..models.calendar import Calendar
from ..models.item import Item
from ..models.location import Location


class Buffer(AuditModel):
    # Types of buffers
    types = (("default", _("default")), ("infinite", _("infinite")))

    # Fields common to all buffer types
    id = models.AutoField(_("identifier"), primary_key=True)
    description = models.CharField(_("description"), null=True, blank=True)
    category = models.CharField(_("category"), null=True, blank=True, db_index=True)
    subcategory = models.CharField(
        _("subcategory"), null=True, blank=True, db_index=True
    )
    type = models.CharField(
        _("type"),
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
    batch = models.CharField(_("batch"), null=True, blank=True, default="")
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
        related_name="bufferminima",
    )
    min_interval = models.DurationField(
        _("min_interval"),
        null=True,
        blank=True,
        help_text=_("Batching window for grouping replenishments in batches"),
    )
    maximum = models.DecimalField(
        _("maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="0.00",
        help_text=_("maximum stock"),
    )
    maximum_calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("maximum calendar"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar storing a time-dependent maximum stock profile"),
        related_name="buffermaxima",
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
