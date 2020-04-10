#
# Copyright (C) 2020 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import freppledb.common.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("execute", "0006_meta"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="user",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
        migrations.CreateModel(
            name="ScheduledTask",
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
                    "next_run",
                    models.DateTimeField(
                        blank=True, db_index=True, null=True, verbose_name="nextrun"
                    ),
                ),
                (
                    "email_failure",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        null=True,
                        verbose_name="email_failure",
                    ),
                ),
                (
                    "email_success",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        null=True,
                        verbose_name="email_success",
                    ),
                ),
                (
                    "data",
                    freppledb.common.fields.JSONBField(
                        blank=True, default="{}", null=True
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedules",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "scheduled task",
                "verbose_name_plural": "scheduled tasks",
                "db_table": "execute_schedule",
            },
        ),
    ]
