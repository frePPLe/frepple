#
# Copyright (C) 2018 by frePPLe bvba
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


class Migration(migrations.Migration):

    replaces = [
        ("execute", "0001_initial"),
        ("execute", "0002_task_logfile"),
        ("execute", "0003_Task_name_size_up"),
        ("execute", "0004_parameter_distribution_solver"),
        ("execute", "0004_task_processid"),
    ]

    initial = True

    dependencies = [("common", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.AutoField(
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="identifier",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        editable=False,
                        max_length=50,
                        verbose_name="name",
                    ),
                ),
                (
                    "submitted",
                    models.DateTimeField(editable=False, verbose_name="submitted"),
                ),
                (
                    "started",
                    models.DateTimeField(
                        blank=True, editable=False, null=True, verbose_name="started"
                    ),
                ),
                (
                    "finished",
                    models.DateTimeField(
                        blank=True, editable=False, null=True, verbose_name="submitted"
                    ),
                ),
                (
                    "arguments",
                    models.TextField(
                        editable=False,
                        max_length=200,
                        null=True,
                        verbose_name="arguments",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        editable=False, max_length=20, verbose_name="status"
                    ),
                ),
                (
                    "message",
                    models.TextField(
                        editable=False,
                        max_length=200,
                        null=True,
                        verbose_name="message",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
                (
                    "logfile",
                    models.TextField(
                        editable=False,
                        max_length=200,
                        null=True,
                        verbose_name="log file",
                    ),
                ),
                (
                    "processid",
                    models.IntegerField(
                        editable=False, null=True, verbose_name="processid"
                    ),
                ),
            ],
            options={
                "db_table": "execute_log",
                "verbose_name": "task",
                "verbose_name_plural": "tasks",
            },
        )
    ]
