#
# Copyright (C) 2016 by frePPLe bv
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
    dependencies = [("odoo", "0001_initial")]

    operations = [migrations.RunPython(add_parameters)]
