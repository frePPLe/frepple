#
# Copyright (C) 2022 by frePPLe bv
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

from django.core.management import call_command
from django.db import migrations


def loadParameters(apps, schema_editor):
    from django.core.management.commands.loaddata import Command

    call_command(
        Command(),
        "parameters.json",
        app_label="odoo",
        verbosity=0,
        database=schema_editor.connection.alias,
    )


def add_parameters(apps, schema_editor):
    Parameter = apps.get_model("common", "Parameter")
    # New parameter: odoo.filter_export_purchase_order
    param, created = Parameter.objects.get_or_create(
        name="odoo.filter_export_purchase_order"
    )
    if created:
        param.value = "True"
        param.description = (
            "Odoo connector: filter purchase orders for automatic exports"
        )
        param.save()
    # New parameter: odoo.filter_export_manufacturing_order
    param, created = Parameter.objects.get_or_create(
        name="odoo.filter_export_manufacturing_order"
    )
    if created:
        param.value = "True"
        param.description = (
            "Odoo connector: filter manufacturing orders for automatic exports"
        )
        param.save()
    # New parameter: odoo.filter_export_distribution_order
    param, created = Parameter.objects.get_or_create(
        name="odoo.filter_export_distribution_order"
    )
    if created:
        param.value = "True"
        param.description = (
            "Odoo connector: filter distribution orders for automatic exports"
        )
        param.save()


class Migration(migrations.Migration):

    replaces = [
        ("odoo", "0001_initial"),
        ("odoo", "0002_parameters"),
        ("odoo", "0003_parameter"),
        ("odoo", "0004_parameter"),
        ("odoo", "0005_parameter"),
    ]

    initial = True

    dependencies = [
        ("common", "0014_squashed_60"),
    ]

    operations = [
        migrations.RunPython(
            code=loadParameters,
        ),
        migrations.RunPython(
            code=add_parameters,
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter\n            (name, value, description, lastmodified)\n            values\n            ('odoo.loglevel','0','Odoo connector: Set to non-zero to get a verbose log. Default is 0.', now())\n            on conflict(name) do nothing\n            ",
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter\n            (name, value, description, lastmodified)\n            values\n            ('odoo.singlecompany','0','Odoo connector: When false (the default) the connector downloads all allowed companies. When true the connector only downloads the data of the configured odoo.company.', now())\n            on conflict(name) do nothing\n            ",
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter\n            (name, value, description, lastmodified)\n            values\n            ('odoo.allowSharedOwnership','false','Odoo connector: By default records read from odoo aren''t editable in frepple. If this flag is set to true you can override the odoo data if the source field of the records is blanked.', now())\n            on conflict(name) do nothing\n            ",
        ),
        migrations.RunSQL(
            sql="\n            delete from common_parameter\n            where name in (\n              'odoo.filter_export_purchase_order',\n              'odoo.filter_export_manufacturing_order',\n              'odoo.filter_export_distribution_order'\n              )\n            ",
        ),
    ]
