#
# Copyright (C) 2025 by frePPLe bv
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
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("execute", "0013_import_skips_audit_log"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataexport",
            name="name",
            field=models.CharField(
                db_index=True, primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="dataexport",
            name="report",
            field=models.CharField(blank=True, null=True, verbose_name="report"),
        ),
        migrations.AlterField(
            model_name="scheduledtask",
            name="data",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="scheduledtask",
            name="email_failure",
            field=models.CharField(blank=True, null=True, verbose_name="email_failure"),
        ),
        migrations.AlterField(
            model_name="scheduledtask",
            name="email_success",
            field=models.CharField(blank=True, null=True, verbose_name="email_success"),
        ),
        migrations.AlterField(
            model_name="scheduledtask",
            name="name",
            field=models.CharField(
                db_index=True, primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="scheduledtask",
            name="tz",
            field=models.CharField(blank=True, null=True, verbose_name="time zone"),
        ),
        migrations.AlterField(
            model_name="scheduledtask",
            name="user",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="schedules",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="arguments",
            field=models.TextField(editable=False, null=True, verbose_name="arguments"),
        ),
        migrations.AlterField(
            model_name="task",
            name="finished",
            field=models.DateTimeField(
                blank=True, editable=False, null=True, verbose_name="finished"
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="logfile",
            field=models.TextField(editable=False, null=True, verbose_name="log file"),
        ),
        migrations.AlterField(
            model_name="task",
            name="message",
            field=models.TextField(editable=False, null=True, verbose_name="message"),
        ),
        migrations.AlterField(
            model_name="task",
            name="name",
            field=models.CharField(db_index=True, editable=False, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.CharField(editable=False, verbose_name="status"),
        ),
        migrations.AlterField(
            model_name="task",
            name="user",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
    ]
