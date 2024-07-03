#
# Copyright (C) 2024 by frePPLe bv
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

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("execute", "0009_parameter_plansafetystockfirst"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataExport",
            fields=[
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        max_length=300,
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                (
                    "sql",
                    models.TextField(blank=True, null=True, verbose_name="sql"),
                ),
                (
                    "report",
                    models.CharField(
                        blank=True, max_length=300, null=True, verbose_name="report"
                    ),
                ),
                ("arguments", models.JSONField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "execute_exports",
                "verbose_name_plural": "execute_exports",
                "db_table": "execute_export",
            },
        ),
    ]
