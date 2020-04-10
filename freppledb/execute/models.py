#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from freppledb.common.fields import JSONBField
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
        _("submitted"), blank=True, null=True, editable=False
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
    data = JSONBField(default="{}", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "execute_schedule"
        verbose_name_plural = _("scheduled tasks")
        verbose_name = _("scheduled task")

    def computeNextRun(self, now=None):
        if now:
            self.next_run = now + timedelta(seconds=600)
        else:
            self.next_run = datetime.now() + timedelta(seconds=600)

    def save(self, *args, **kwargs):
        self.computeNextRun()
        super().save(*args, **kwargs)
