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

from freppledb.common.models import User

import logging

logger = logging.getLogger(__name__)


class Task(models.Model):
    """
    Expected status values are:
      - 'Waiting'
      - 'Done'
      - 'Failed'
      - 'Canceled'
      - 'DD%', where DD represents the percentage completed
    Other values are okay, but the above have translations.
    """

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True, editable=False)
    name = models.CharField(_("name"), max_length=50, db_index=True, editable=False)
    submitted = models.DateTimeField(_("submitted"), editable=False)
    started = models.DateTimeField(_("started"), blank=True, null=True, editable=False)
    finished = models.DateTimeField(
        _("finished"), blank=True, null=True, editable=False
    )
    arguments = models.TextField(
        _("arguments"), max_length=200, null=True, editable=False
    )
    status = models.CharField(_("status"), max_length=20, editable=False)
    message = models.TextField(_("message"), max_length=200, null=True, editable=False)
    logfile = models.TextField(_("log file"), max_length=200, null=True, editable=False)
    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        blank=True,
        null=True,
        editable=False,
        related_name="tasks",
        on_delete=models.CASCADE,
    )
    processid = models.IntegerField("processid", editable=False, null=True)

    def __str__(self):
        return "%s - %s - %s" % (self.id, self.name, self.status)

    class Meta:
        db_table = "execute_log"
        verbose_name_plural = _("tasks")
        verbose_name = _("task")
        default_permissions = ["view"]

    @staticmethod
    def submitTask():
        # Add record to the database
        # Check if a worker is present. If not launch one.
        return 1


class ScheduledTask(models.Model):
    # Database fields
    name = models.CharField("name", primary_key=True, max_length=300, db_index=True)
    next_run = models.DateTimeField("nextrun", blank=True, null=True, db_index=True)
    user = models.ForeignKey(
        User,
        blank=False,
        null=True,
        editable=False,
        related_name="schedules",
        on_delete=models.CASCADE,
    )
    email_failure = models.CharField(
        "email_failure", max_length=300, null=True, blank=True
    )
    email_success = models.CharField(
        "email_success", max_length=300, null=True, blank=True
    )
    data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

    def lastrun(self):
        return (
            Task.objects.all()
            .using(self._state.db)
            .filter(name="scheduletasks", arguments="--schedule=%s" % self.name)
            .order_by("-id")
            .first()
        )

    class Meta:
        db_table = "execute_schedule"
        verbose_name_plural = _("scheduled tasks")
        verbose_name = _("scheduled task")

    def computeNextRun(self, now=None):
        if self.data:
            weekdays = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            starttime = self.data.get("starttime", -1)
            if starttime is not None and starttime >= 0:
                starttime = int(starttime)
                if not now:
                    now = datetime.now()
                time_of_day = now.hour * 3600 + now.minute * 60 + now.second
                weekday = now.weekday()
                # Loop over current + next 7 days
                for n in range(8):
                    if n == 0 and time_of_day > starttime:
                        # Too late to start today
                        weekday = (weekday + 1) % 7
                    elif self.data.get(weekdays[weekday], False):
                        self.next_run = (now + timedelta(days=n)).replace(
                            hour=int(starttime / 3600),
                            minute=int(int(starttime % 3600) / 60),
                            second=starttime % 60,
                            microsecond=0,
                        )
                        return
                    else:
                        weekday = (weekday + 1) % 7
        self.next_run = None

    def adjustForTimezone(self, offset):
        if isinstance(offset, timedelta):
            offset = int(offset.total_seconds())
        if self.next_run:
            self.next_run += timedelta(seconds=offset)
        if self.data and self.data.get("starttime", None) is not None:
            self.data["starttime"] += offset
            if self.data["starttime"] < 0:
                # Starts the previous day!
                self.data["starttime"] += 24 * 3600
                tmp = self.data.get("monday", False)
                self.data["monday"] = self.data.get("tuesday", False)
                self.data["tuesday"] = self.data.get("wednesday", False)
                self.data["wednesday"] = self.data.get("thursday", False)
                self.data["thursday"] = self.data.get("friday", False)
                self.data["friday"] = self.data.get("saturday", False)
                self.data["saturday"] = self.data.get("sunday", False)
                self.data["sunday"] = tmp
            elif self.data["starttime"] > 24 * 3600:
                # Starts the next day!
                self.data["starttime"] -= 24 * 3600
                tmp = self.data.get("sunday", False)
                self.data["sunday"] = self.data.get("saturday", False)
                self.data["saturday"] = self.data.get("friday", False)
                self.data["friday"] = self.data.get("thursday", False)
                self.data["thursday"] = self.data.get("wednesday", False)
                self.data["wednesday"] = self.data.get("tuesday", False)
                self.data["tuesday"] = self.data.get("monday", False)
                self.data["monday"] = tmp
        return self

    def save(self, *args, **kwargs):
        self.computeNextRun()
        super().save(*args, **kwargs)
