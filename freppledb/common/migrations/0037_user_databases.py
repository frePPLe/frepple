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

from django.db import DEFAULT_DB_ALIAS
from django.db.models import Q

from django.db import migrations


def populateDatabaseField(apps, schema_editor):
    db = schema_editor.connection.alias
    if db == DEFAULT_DB_ALIAS:
        scenario_model = apps.get_model("common", "Scenario")
        user_model = apps.get_model("common", "User")
        user_scenarios = {}
        for sc in scenario_model.objects.using(db).filter(
            Q(status="In use") & ~Q(name=DEFAULT_DB_ALIAS)
        ):
            for u in (
                user_model.objects.using(sc.name)
                .filter(is_active=True)
                .only("is_active")
            ):
                if u.pk in user_scenarios:
                    user_scenarios[u.pk].append(sc.name)
                else:
                    user_scenarios[u.pk] = [sc.name]
        for u in user_model.objects.using(DEFAULT_DB_ALIAS).filter(is_active=True):
            if u.pk in user_scenarios:
                user_scenarios[u.pk].append(DEFAULT_DB_ALIAS)
            else:
                user_scenarios[u.pk] = [DEFAULT_DB_ALIAS]
            u.databases = user_scenarios[u.pk]
            u.save(update_fields=["databases"], using=DEFAULT_DB_ALIAS)


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0036_user_databases"),
    ]

    operations = [
        migrations.RunPython(
            code=populateDatabaseField, reverse_code=migrations.RunPython.noop
        ),
    ]
