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
import os
import psutil
import shlex
import zoneinfo

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS, models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Now

from freppledb.common.models import User, Parameter

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
    """

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True, editable=False)
    name = models.CharField(_("name"), db_index=True, editable=False)
    submitted = models.DateTimeField(_("submitted"), editable=False)
    started = models.DateTimeField(_("started"), blank=True, null=True, editable=False)
    finished = models.DateTimeField(
        _("finished"), blank=True, null=True, editable=False
    )
    arguments = models.TextField(_("arguments"), null=True, editable=False)
    status = models.CharField(_("status"), editable=False)
    message = models.TextField(_("message"), null=True, editable=False)
    logfile = models.TextField(_("log file"), null=True, editable=False)
    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        blank=True,
        null=True,
        editable=False,
        related_name="tasks",
        on_delete=models.SET_NULL,
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

    @classmethod
    def removeUnhealthyTasks(cls, database):
        # Unhealthy tasks are:
        #  - Waiting tasks if no runworker is active.
        #    Eg server was rebooted while some task were still waiting. We don't want to
        #    catch up on the waiting tasks, but rather expect new ones to be launched.
        #  - Task running for longer than 3 hours.
        try:
            worker_alive = Parameter.getValue("Worker alive", database, None)
            if not worker_alive or datetime.now() - datetime.strptime(
                worker_alive, "%Y-%m-%d %H:%M:%S"
            ) > timedelta(seconds=30):
                x = (
                    Task.objects.using(database)
                    .filter(
                        status="waiting",
                        submitted__lte=Now() - timedelta(seconds=30),
                    )
                    .update(status="Canceled")
                )
                print(" canceled ", x)
            for t in Task.objects.using(database).filter(
                status__contains="%",
                finished__isnull=True,
                started__isnull=False,
                started__lte=Now() - timedelta(minutes=3),
            ):
                print("killed", t.id, t.processid)
                t.killProcess()
        except Exception as e:
            print("eeeeeee", e)
            pass

    def killProcess(self):
        # Kill the process and its children with signal 9
        if self.processid:
            database = self._state.db
            child_pid = [c.pid for c in psutil.Process(self.processid).children()]
            os.kill(self.processid, 9)
            self.message = "Canceled process"
            for child_task in (
                Task.objects.all().using(database).filter(processid__in=child_pid)
            ):
                try:
                    os.kill(child_task.processid, 9)
                except Exception:
                    pass
                child_task.message = "Canceled process"
                child_task.processid = None
                child_task.status = "Canceled"
                child_task.save(using=database)
        elif self.status != "waiting":
            return
        self.processid = None
        self.status = "Canceled"
        self.save(using=database)


class ScheduledTask(models.Model):
    # Database fields
    name = models.CharField("name", primary_key=True, db_index=True)
    next_run = models.DateTimeField("nextrun", blank=True, null=True, db_index=True)
    user = models.ForeignKey(
        User,
        blank=False,
        null=True,
        editable=False,
        related_name="schedules",
        on_delete=models.SET_NULL,
    )
    email_failure = models.CharField("email_failure", null=True, blank=True)
    email_success = models.CharField("email_success", null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    tz = models.CharField(
        _("time zone"),
        choices=[(i, i) for i in zoneinfo.available_timezones()],
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    def lastrun(self):
        return (
            Task.objects.all()
            .using(self._state.db)
            .filter(
                Q(arguments="--schedule=%s" % shlex.quote(self.name))
                | Q(arguments="--schedule='%s'" % shlex.quote(self.name)),
                name="scheduletasks",
            )
            .order_by("-id")
            .first()
        )

    class Meta:
        db_table = "execute_schedule"
        verbose_name_plural = _("scheduled tasks")
        verbose_name = _("scheduled task")
        default_permissions = ("add", "delete")

    def computeNextRun(self, now=None):
        self.next_run = None
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
            starts = self.data.get("starttime", None)
            if isinstance(starts, list):
                starts = [int(i) for i in starts if i is not None]
            elif starts is None:
                starts = []
            else:
                starts = [int(starts)]
            for starttime in starts:
                if not now:
                    now = datetime.now(
                        zoneinfo.ZoneInfo(self.tz or settings.TIME_ZONE)
                    ) + timedelta(seconds=1)
                time_of_day = now.hour * 3600 + now.minute * 60 + now.second
                weekday = now.weekday()
                # Loop over current + next 7 days
                for n in range(8):
                    if n == 0 and time_of_day > starttime:
                        # Too late to start today
                        weekday = (weekday + 1) % 7
                    elif self.data.get(weekdays[weekday], False):
                        d = now + timedelta(days=n)
                        nxt = datetime(
                            year=d.year,
                            month=d.month,
                            day=d.day,
                            hour=int(starttime / 3600),
                            minute=int(int(starttime % 3600) / 60),
                            second=starttime % 60,
                            microsecond=0,
                            tzinfo=zoneinfo.ZoneInfo(self.tz or settings.TIME_ZONE),
                        )
                        nxt = nxt.astimezone(zoneinfo.ZoneInfo(settings.TIME_ZONE))
                        if not self.next_run or nxt < self.next_run:
                            self.next_run = nxt
                    else:
                        weekday = (weekday + 1) % 7

    def adjustForTimezone(self, offset):
        if isinstance(offset, timedelta):
            offset = int(offset.total_seconds())
        if self.next_run:
            self.next_run += timedelta(seconds=offset)
        if callable(self.lastrun):
            self.lastrun = self.lastrun()  # Hack: replacing method with attribute
        if self.lastrun:
            if self.lastrun.submitted:
                self.lastrun.submitted += timedelta(seconds=offset)
            if self.lastrun.started:
                self.lastrun.started += timedelta(seconds=offset)
            if self.lastrun.finished:
                self.lastrun.finished += timedelta(seconds=offset)
        starts = self.data.get("starttime", None)
        if starts is not None and not isinstance(starts, list):
            self.data["starttime"] = [int(starts)]
        return self

    @staticmethod
    def updateScenario(database):
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                select count(*)
                from execute_schedule
                where next_run is not null
                """
            )
            scheduled = cursor.fetchone()[0]
            with connections[DEFAULT_DB_ALIAS].cursor() as cursor_dflt:
                cursor_dflt.execute(
                    """
                    update common_scenario
                    set info = %s
                    where name = %%s
                    """
                    % (
                        "coalesce(info, '{}') || '{\"has_schedule\": true}'"
                        if scheduled > 0
                        else "info - 'has_schedule'"
                    ),
                    (database,),
                )

    def save(self, *args, **kwargs):
        self.computeNextRun()
        super().save(*args, **kwargs)
        ScheduledTask.updateScenario(self._state.db)

    def delete(self, *args, **kwargs):
        db = self._state.db
        super().delete(*args, **kwargs)
        ScheduledTask.updateScenario(db)


class DataExport(models.Model):
    # Database fields
    name = models.CharField("name", primary_key=True, db_index=True)
    sql = models.TextField("sql", null=True, blank=True)
    report = models.CharField("report", null=True, blank=True)
    arguments = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

    def basename(self):
        if self.name.endswith(".xlsx"):
            return self.name[:-5]
        elif self.name.endswith(".csv"):
            return self.name[:-4]
        elif self.name.endswith(".csv.gz"):
            return self.name[:-7]
        else:
            return self.name

    def extension(self):
        if self.name.endswith(".xlsx"):
            return ".xlsx"
        elif self.name.endswith(".csv"):
            return ".csv"
        elif self.name.endswith(".csv.gz"):
            return ".csv.gz"
        else:
            return ""

    def exporttype(self):
        if self.sql:
            return "sql"
        elif self.report.startswith("freppledb.reportmanager.models.SQLReport."):
            return "customreport"
        else:
            return "report"

    def reportid(self):
        return (
            int(self.report[41:])
            if self.report
            and self.report.startswith("freppledb.reportmanager.models.SQLReport.")
            else None
        )

    class Meta:
        db_table = "execute_export"
        verbose_name_plural = "execute_exports"
        verbose_name = "execute_exports"
        default_permissions = []

    def save(self, *args, **kwargs):
        name_lower = self.name.lower()
        if not (
            name_lower.endswith(".xlsx")
            or name_lower.endswith(".csv.gz")
            or name_lower.endswith(".csv")
        ):
            raise Exception("Exports must end with .xlsx, .csv or .csv.gz")
        if os.sep in self.name:
            raise Exception("Export names can't contain %s" % os.sep)
        super().save(*args, **kwargs)
