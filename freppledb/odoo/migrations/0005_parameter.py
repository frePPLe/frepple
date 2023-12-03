#
# Copyright (C) 2020 by frePPLe bv
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
