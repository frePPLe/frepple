#
# Copyright (C) 2024 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
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
