#
# Copyright (C) 2019 by frePPLe bv
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
    initial = True

    dependencies = [("common", "0008_squashed_41")]

    operations = [
        migrations.CreateModel(
            name="Constraint",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "demand",
                    models.CharField(
                        db_index=True, max_length=300, verbose_name="demand"
                    ),
                ),
                (
                    "entity",
                    models.CharField(
                        db_index=True, max_length=15, verbose_name="entity"
                    ),
                ),
                (
                    "owner",
                    models.CharField(
                        db_index=True, max_length=300, verbose_name="owner"
                    ),
                ),
                (
                    "name",
                    models.CharField(db_index=True, max_length=20, verbose_name="name"),
                ),
                (
                    "description",
                    models.CharField(max_length=1000, verbose_name="description"),
                ),
                (
                    "startdate",
                    models.DateTimeField(db_index=True, verbose_name="start date"),
                ),
                (
                    "enddate",
                    models.DateTimeField(db_index=True, verbose_name="end date"),
                ),
                (
                    "weight",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, verbose_name="weight"
                    ),
                ),
            ],
            options={
                "verbose_name": "constraint",
                "verbose_name_plural": "constraints",
                "db_table": "out_constraint",
                "ordering": ["demand", "startdate"],
            },
        ),
        migrations.CreateModel(
            name="Problem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "entity",
                    models.CharField(
                        db_index=True, max_length=15, verbose_name="entity"
                    ),
                ),
                (
                    "owner",
                    models.CharField(
                        db_index=True, max_length=300, verbose_name="owner"
                    ),
                ),
                (
                    "name",
                    models.CharField(db_index=True, max_length=20, verbose_name="name"),
                ),
                (
                    "description",
                    models.CharField(max_length=1000, verbose_name="description"),
                ),
                (
                    "startdate",
                    models.DateTimeField(db_index=True, verbose_name="start date"),
                ),
                (
                    "enddate",
                    models.DateTimeField(db_index=True, verbose_name="end date"),
                ),
                (
                    "weight",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, verbose_name="weight"
                    ),
                ),
            ],
            options={
                "verbose_name": "problem",
                "verbose_name_plural": "problems",
                "db_table": "out_problem",
                "ordering": ["startdate"],
            },
        ),
        migrations.CreateModel(
            name="ResourceSummary",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("resource", models.CharField(max_length=300, verbose_name="resource")),
                ("startdate", models.DateTimeField(verbose_name="startdate")),
                (
                    "available",
                    models.DecimalField(
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="available",
                    ),
                ),
                (
                    "unavailable",
                    models.DecimalField(
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="unavailable",
                    ),
                ),
                (
                    "setup",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, null=True, verbose_name="setup"
                    ),
                ),
                (
                    "load",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, null=True, verbose_name="load"
                    ),
                ),
                (
                    "free",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, null=True, verbose_name="free"
                    ),
                ),
            ],
            options={
                "verbose_name": "resource summary",
                "verbose_name_plural": "resource summaries",
                "db_table": "out_resourceplan",
                "ordering": ["resource", "startdate"],
                "unique_together": {("resource", "startdate")},
            },
        ),
    ]
