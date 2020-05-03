#
# Copyright (C) 2020 by frePPLe bvba
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

from django.db import migrations, models, connections
import django.db.models.deletion
import django.utils.timezone
from ..models import SQLReport


def populateColumns(apps, schema_editor):
    reportmodel = apps.get_model("reportmanager", "SQLReport")
    columnmodel = apps.get_model("reportmanager", "SQLColumn")
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        for rep in reportmodel.objects.all().using(db):
            # The query is wrapped in a dummy filter, to avoid executing the
            # inner real query. It still generates the list of all columns.
            cursor.execute("select * from (%s) as Q where false" % rep.sql)
            seq = 1
            for f in cursor.description:
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
                columnmodel(report=rep, sequence=seq, name=f[0], format=fmt).save(
                    using=db
                )
                seq += 1


class Migration(migrations.Migration):

    dependencies = [("reportmanager", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="SQLColumn",
            fields=[
                (
                    "source",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=300,
                        null=True,
                        verbose_name="source",
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="last modified",
                    ),
                ),
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                ("sequence", models.IntegerField(default=1, verbose_name="sequence")),
                ("name", models.CharField(max_length=300, verbose_name="name")),
                (
                    "format",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="format"
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="columns",
                        to="reportmanager.SQLReport",
                        verbose_name="report",
                    ),
                ),
            ],
            options={
                "verbose_name": "report column",
                "verbose_name_plural": "report columns",
                "db_table": "reportmanager_column",
                "ordering": ("report", "sequence"),
                "unique_together": {("report", "sequence")},
            },
        ),
        migrations.RunPython(populateColumns),
    ]
