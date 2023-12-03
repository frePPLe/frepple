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

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
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
