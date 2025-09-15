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

from datetime import datetime, time, timedelta
from sys import maxsize

from django.db import models, DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import AuditModel, MultiDBManager


class Calendar(AuditModel):
    # Database fields
    name = models.CharField(_("name"), primary_key=True)
    description = models.CharField(_("description"), null=True, blank=True)
    category = models.CharField(_("category"), null=True, blank=True, db_index=True)
    subcategory = models.CharField(
        _("subcategory"), null=True, blank=True, db_index=True
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

    def findBucket(self, curDate):
        """
        This code needs to 100% in sync with the C++ Calendar::findbucket method.
        """
        curBucket = None
        for b in self.getBuckets():
            if (
                (not curBucket or b.priority < curBucket.priority)
                and curDate >= b.startdate
                and curDate < b.enddate
                and curDate.time() >= b.starttime
                and curDate.time() < b.endtime
                and curDate.weekday() in b.weekdays
            ):
                curBucket = b
        return curBucket

    def getBuckets(self):
        if hasattr(self, "_buckets"):
            return self._buckets
        database = self._state.db or DEFAULT_DB_ALIAS
        self._buckets = []
        for b in self.buckets.all().using(database).order_by("startdate", "priority"):
            b.weekdays = []
            if b.monday:
                b.weekdays.append(0)
            if b.tuesday:
                b.weekdays.append(1)
            if b.wednesday:
                b.weekdays.append(2)
            if b.thursday:
                b.weekdays.append(3)
            if b.friday:
                b.weekdays.append(4)
            if b.saturday:
                b.weekdays.append(5)
            if b.sunday:
                b.weekdays.append(6)
            self._buckets.append(b)
            if not b.startdate:
                b.startdate = datetime(1971, 1, 1)
            if not b.enddate:
                b.enddate = datetime(2030, 12, 31)
            if not b.starttime:
                b.starttime = time.min
            if not b.endtime:
                b.endtime = time.max
            elif b.endtime.second < 59:
                b.endtime = b.endtime.replace(second=b.endtime.second + 1)
            elif b.endtime.minute < 59:
                b.endtime = b.endtime.replace(minute=b.endtime.minute + 1, second=0)
            elif b.endtime.hour < 23:
                b.endtime = b.endtime.replace(
                    hour=b.endtime.hour + 1, minute=0, second=0
                )
            else:
                # Special case for 23:59:59
                b.endtime = time.max
            b.continuous = (
                len(b.weekdays) == 7
                and b.starttime == time.min
                and b.endtime == time.max
            )
        return self._buckets

    def getEvents(self, from_date, to_date):
        """
        This code needs to 100% in sync with the C++ Calendar::buildEventList method
        """
        # Build up event list
        events = []
        curDate = from_date
        curBucket = self.findBucket(curDate)
        curPriority = curBucket.priority if curBucket else maxsize
        lastPriority = curPriority
        lastBucket = curBucket
        while True:
            if curDate >= to_date:
                break
            prevDate = curDate

            # Go over all entries and evaluate if they qualify for the next event
            refDate = curDate
            curDate = datetime.max
            for b in self.getBuckets():
                if b.startdate >= b.enddate:
                    continue
                elif b.continuous:
                    # FIRST CASE: Bucket that is continuously effective
                    # Evaluate the start date of the bucket
                    if (
                        refDate < b.startdate
                        and b.priority <= lastPriority
                        and (
                            b.startdate < curDate
                            or (b.startdate == curDate and b.priority <= curPriority)
                        )
                    ):
                        curDate = b.startdate
                        curBucket = b
                        curPriority = b.priority
                        continue

                    #  Evaluate the end date of the bucket
                    if refDate < b.enddate and b.enddate <= curDate and lastBucket == b:
                        curDate = b.enddate
                        curBucket = self.findBucket(b.enddate)
                        curPriority = curBucket.priority if curBucket else maxsize
                        continue
                else:
                    # SECOND CASE: Interruptions in effectivity
                    effectiveAtStart = False
                    tmp = max(b.startdate, refDate)
                    ref_weekday = tmp.weekday()
                    ref_time = tmp.time()
                    if (
                        refDate < b.startdate
                        and ref_time >= b.starttime
                        and ref_time < b.endtime
                        and ref_weekday in b.weekdays
                    ):
                        effectiveAtStart = True

                    if (
                        ref_time >= b.starttime
                        and not effectiveAtStart
                        and ref_time < b.endtime
                        and ref_weekday in b.weekdays
                    ):
                        # Entry is currently effective.
                        if (
                            b.starttime == time(hour=0, minute=0, second=0)
                            and b.endtime == time.max
                        ):
                            # The next event is the start of the next ineffective day
                            tmp = tmp.replace(hour=0, minute=0, second=0)
                            while ref_weekday in b.weekdays and tmp <= to_date:
                                ref_weekday += 1
                                if ref_weekday > 6:
                                    ref_weekday = 0
                                tmp += timedelta(days=1)
                        else:
                            # The next event is the end date on the current day
                            tmp = tmp.replace(
                                hour=b.endtime.hour,
                                minute=b.endtime.minute,
                                second=b.endtime.second,
                            )
                        if tmp > b.enddate:
                            tmp = b.enddate

                        # Evaluate the result
                        if refDate < tmp and tmp <= curDate and lastBucket == b:
                            curDate = tmp
                            curBucket = self.findBucket(tmp)
                            curPriority = curBucket.priority if curBucket else maxsize

                    else:
                        # Reference date is before the start time on an effective date
                        # or it is after the end time of an effective date
                        # or it is on an ineffective day.

                        # The next event is the start date, either today or on the next
                        # effective day.
                        tmp = tmp.replace(
                            hour=b.starttime.hour,
                            minute=b.starttime.minute,
                            second=b.starttime.second,
                        )
                        if ref_time >= b.endtime and ref_weekday in b.weekdays:
                            ref_weekday += 1
                            if ref_weekday > 6:
                                ref_weekday = 0
                            tmp += timedelta(days=1)
                        while (
                            ref_weekday not in b.weekdays
                            and tmp <= to_date
                            and tmp <= b.enddate
                        ):
                            ref_weekday += 1
                            if ref_weekday > 6:
                                ref_weekday = 0
                            tmp += timedelta(days=1)
                        if tmp < b.startdate:
                            tmp = b.startdate
                        if tmp >= b.enddate:
                            continue

                        # Evaluate the result
                        if (
                            refDate < tmp
                            and b.priority <= lastPriority
                            and (
                                tmp < curDate
                                or (tmp == curDate and b.priority <= curPriority)
                            )
                        ):
                            curDate = tmp
                            curBucket = b
                            curPriority = b.priority

            events.append(
                (
                    min(prevDate, to_date),
                    min(curDate, to_date),
                    curBucket.id if curBucket else None,
                    float(curBucket.value if curBucket else self.defaultvalue),
                    lastBucket.id if lastBucket else None,
                    float(lastBucket.value if lastBucket else self.defaultvalue),
                )
            )

            # Remember the bucket that won the evaluation
            lastBucket = curBucket
            lastPriority = curPriority

        # Final result
        return events


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
