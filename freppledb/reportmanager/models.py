#
# Copyright (C) 2019 by frePPLe bv
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

from django.conf import settings
from django.db import models, DEFAULT_DB_ALIAS
from django.utils.translation import gettext as _

from freppledb.common.models import AuditModel, User, MultiDBManager
from freppledb.common.report import create_connection


class SQLReport(AuditModel):
    id = models.AutoField(_("identifier"), primary_key=True)
    name = models.CharField(_("name"), max_length=300, db_index=True)
    sql = models.TextField(_("SQL query"), null=True, blank=True)
    description = models.CharField(
        _("description"), max_length=1000, null=True, blank=True
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        blank=False,
        null=True,
        editable=False,
        related_name="reports",
        on_delete=models.CASCADE,
    )
    public = models.BooleanField(blank=True, default=False)

    def refreshColumns(self):
        from freppledb.common.middleware import _thread_locals

        req = getattr(_thread_locals, "request", None)
        if req:
            db = getattr(req, "database", DEFAULT_DB_ALIAS)
        else:
            db = getattr(_thread_locals, "database", DEFAULT_DB_ALIAS)
        SQLColumn.objects.filter(report=self).using(db).delete()
        if self.sql:
            conn = None
            try:
                conn = create_connection(db)
                with conn.cursor() as cursor:
                    sqlrole = settings.DATABASES[db].get("SQL_ROLE", "report_role")
                    if sqlrole:
                        cursor.execute("set role %s" % (sqlrole,))
                    # The query is wrapped in a dummy filter, to avoid executing the
                    # inner real query. It still generates the list of all columns.
                    cursor.execute("select * from (%s) as Q where false" % self.sql)
                    cols = []
                    seq = 1
                    for f in cursor.description:
                        if f[0] in cols:
                            raise Exception("Duplicate column name '%s'" % f[0])
                        cols.append(f[0])
                        if f[1] == 1700:
                            fmt = "number"
                        elif f[1] == 1184:
                            fmt = "datetime"
                        elif f[1] == 23:
                            fmt = "integer"
                        elif f[1] == 1186:
                            fmt = "duration"
                        elif f[1] == 1043:
                            fmt = "text"
                        else:
                            fmt = "character"
                        SQLColumn(
                            report=self, sequence=seq, name=f[0], format=fmt
                        ).save(using=db)
                        seq += 1
            finally:
                if conn:
                    conn.close()

    def save(self, *args, **kwargs):
        self.refreshColumns()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "reportmanager_report"
        ordering = ("name",)
        verbose_name = _("my report")
        verbose_name_plural = _("my reports")

    def __str__(self):
        return self.name


class SQLColumn(AuditModel):
    id = models.AutoField(_("identifier"), primary_key=True)
    report = models.ForeignKey(
        SQLReport,
        verbose_name="report",
        related_name="columns",
        on_delete=models.CASCADE,
    )
    sequence = models.IntegerField("sequence", default=1)
    name = models.CharField("name", max_length=300)
    format = models.CharField("format", max_length=20, null=True, blank=True)

    class Manager(MultiDBManager):
        def get_by_natural_key(self, report, sequence):
            return self.get(report=report, sequence=sequence)

    def natural_key(self):
        return (self.report, self.sequence)

    def __str__(self):
        return "%s.%s" % (self.report.name if self.report else "", self.name)

    class Meta:
        db_table = "reportmanager_column"
        ordering = ("report", "sequence")
        unique_together = (("report", "sequence"),)
        verbose_name = "report column"
        verbose_name_plural = "report columns"
