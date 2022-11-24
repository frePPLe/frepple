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

from datetime import datetime, time

from django.db import models
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import AuditModel, MultiDBManager


class Calendar(AuditModel):
    # Database fields
    name = models.CharField(_("name"), max_length=300, primary_key=True)
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    defaultvalue = models.DecimalField(
        _("default value"),
        max_digits=20,
        decimal_places=8,
        default="0.00",
        null=True,
        blank=True,
        help_text=_("Value to be used when no entry is effective"),
    )

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "calendar"
        verbose_name = _("calendar")
        verbose_name_plural = _("calendars")
        ordering = ["name"]


class CalendarBucket(AuditModel):

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("calendar"),
        related_name="buckets",
        on_delete=models.CASCADE,
    )
    startdate = models.DateTimeField(
        _("start date"), null=True, blank=True, default=datetime(1971, 1, 1)
    )
    enddate = models.DateTimeField(
        _("end date"), null=True, blank=True, default=datetime(2030, 12, 31)
    )
    value = models.DecimalField(
        _("value"), default="0.00", blank=True, max_digits=20, decimal_places=8
    )
    priority = models.IntegerField(_("priority"), default=0, blank=True, null=True)
    monday = models.BooleanField(_("Monday"), blank=True, default=True)
    tuesday = models.BooleanField(_("Tuesday"), blank=True, default=True)
    wednesday = models.BooleanField(_("Wednesday"), blank=True, default=True)
    thursday = models.BooleanField(_("Thursday"), blank=True, default=True)
    friday = models.BooleanField(_("Friday"), blank=True, default=True)
    saturday = models.BooleanField(_("Saturday"), blank=True, default=True)
    sunday = models.BooleanField(_("Sunday"), blank=True, default=True)
    starttime = models.TimeField(
        _("start time"), blank=True, null=True, default=time(0, 0, 0)
    )
    endtime = models.TimeField(
        _("end time"), blank=True, null=True, default=time(23, 59, 59)
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, calendar, startdate, enddate, priority):
            return self.get(
                calendar=calendar,
                startdate=startdate or datetime(1971, 1, 1),
                enddate=enddate or datetime(2030, 12, 31),
                priority=priority,
            )

    def natural_key(self):
        return (
            self.calendar,
            self.startdate or datetime(1971, 1, 1),
            self.enddate or datetime(2030, 12, 31),
            self.priority,
        )

    objects = Manager()

    def validate_unique(self, exclude=None):
        if self.startdate is None:
            self.startdate = datetime(1971, 1, 1)
        if self.enddate is None:
            self.enddate = datetime(2030, 12, 31)
        super().validate_unique(exclude=exclude)

    def __str__(self):
        return "%s" % self.id

    class Meta(AuditModel.Meta):
        ordering = ["calendar", "id"]
        db_table = "calendarbucket"
        verbose_name = _("calendar bucket")
        verbose_name_plural = _("calendar buckets")
        unique_together = (("calendar", "startdate", "enddate", "priority"),)
