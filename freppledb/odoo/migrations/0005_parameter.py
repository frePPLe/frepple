#
# Copyright (C) 2020 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("odoo", "0004_parameter")]

    operations = [
        migrations.RunSQL(
            """
            insert into common_parameter
            (name, value, description, lastmodified)
            values
            ('odoo.allowSharedOwnership','false','Odoo connector: By default records read from odoo aren''t editable in frepple. If this flag is set to true you can override the odoo data if the source field of the records is blanked.', now())
            on conflict(name) do nothing
            """
        ),
        migrations.RunSQL(
            """
            delete from common_parameter
            where name in (
              'odoo.filter_export_purchase_order',
              'odoo.filter_export_manufacturing_order',
              'odoo.filter_export_distribution_order'
              )
            """
        ),
    ]
