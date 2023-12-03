#
# Copyright (C) 2020 by frePPLe bv
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

from django.db import migrations, models, connections
import django.db.models.deletion
import django.utils.timezone


def populateColumns(apps, schema_editor):
    reportmodel = apps.get_model("reportmanager", "SQLReport")
    columnmodel = apps.get_model("reportmanager", "SQLColumn")
    db = schema_editor.connection.alias
    for rep in reportmodel.objects.all().using(db):
        try:
            with connections[db].cursor() as cursor:
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
        except Exception:
            print("Error migrating report %s" % rep.name)


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
