#
# Copyright (C) 2022 by frePPLe bv
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

    replaces = [('odoo', '0001_initial'), ('odoo', '0002_parameters'), ('odoo', '0003_parameter'), ('odoo', '0004_parameter'), ('odoo', '0005_parameter')]

    initial = True

    dependencies = [
        ('common', '0014_squashed_60'),
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
