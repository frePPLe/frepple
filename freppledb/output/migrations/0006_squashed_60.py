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

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [("output", "0004_squashed_41"), ("output", "0005_number_precision")]

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
