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

import os

import django.contrib.postgres.fields
from django.db import migrations, transaction, models, connection

from ..models import defaultdatabase


def updateScenarioInfo(apps, schema_editor):
    from ...execute.models import ScheduledTask

    if not connection.settings_dict.get("TEST", False):
        try:
            with transaction.atomic():
                ScheduledTask.updateScenario(schema_editor.connection.alias)
        except Exception as e:
            # On a new schema, the execute app may not be installed yet.
            # This is not a problem as it won't have any scheduled tasks then.
            pass


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("common", "0037_user_databases"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scenario",
            name="lastrefresh",
        ),
        migrations.AddField(
            model_name="scenario",
            name="info",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="databases",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=300, verbose_name="databases"),
                default=defaultdatabase,
                null=True,
                size=None,
            ),
        ),
        migrations.RunPython(
            code=updateScenarioInfo,
            reverse_code=migrations.RunPython.noop,
            hints={"allow_atomic": False},
        ),
    ]
