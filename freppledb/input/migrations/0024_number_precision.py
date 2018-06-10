#
# Copyright (C) 2017 by frePPLe bvba
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

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('input', '0023_transferbatch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buffer',
            name='minimum',
            field=models.DecimalField(blank=True, decimal_places=8, default='0.00', help_text='safety stock', max_digits=20, null=True, verbose_name='minimum'),
        ),
        migrations.AlterField(
            model_name='buffer',
            name='onhand',
            field=models.DecimalField(blank=True, decimal_places=8, default='0.00', help_text='current inventory', max_digits=20, null=True, verbose_name='onhand'),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='defaultvalue',
            field=models.DecimalField(blank=True, decimal_places=8, default='0.00', help_text='Value to be used when no entry is effective', max_digits=20, null=True, verbose_name='default value'),
        ),
        migrations.AlterField(
            model_name='calendarbucket',
            name='value',
            field=models.DecimalField(blank=True, decimal_places=8, default='0.00', max_digits=20, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='demand',
            name='minshipment',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Minimum shipment quantity when planning this demand', max_digits=20, null=True, verbose_name='minimum shipment'),
        ),
        migrations.AlterField(
            model_name='demand',
            name='plannedquantity',
            field=models.DecimalField(blank=True, decimal_places=8, editable=False, help_text='Quantity planned for delivery', max_digits=20, null=True, verbose_name='planned quantity'),
        ),
        migrations.AlterField(
            model_name='demand',
            name='quantity',
            field=models.DecimalField(decimal_places=8, default=1, max_digits=20, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='item',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Cost of the item', max_digits=20, null=True, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='itemdistribution',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Shipping cost per unit', max_digits=20, null=True, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='itemdistribution',
            name='resource_qty',
            field=models.DecimalField(blank=True, decimal_places=8, default='1.0', help_text='Resource capacity consumed per distributed unit', max_digits=20, null=True, verbose_name='resource quantity'),
        ),
        migrations.AlterField(
            model_name='itemdistribution',
            name='sizeminimum',
            field=models.DecimalField(blank=True, decimal_places=8, default='1.0', help_text='A minimum shipping quantity', max_digits=20, null=True, verbose_name='size minimum'),
        ),
        migrations.AlterField(
            model_name='itemdistribution',
            name='sizemultiple',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='A multiple shipping quantity', max_digits=20, null=True, verbose_name='size multiple'),
        ),
        migrations.AlterField(
            model_name='itemsupplier',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Purchasing cost per unit', max_digits=20, null=True, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='itemsupplier',
            name='resource_qty',
            field=models.DecimalField(blank=True, decimal_places=8, default='1.0', help_text='Resource capacity consumed per purchased unit', max_digits=20, null=True, verbose_name='resource quantity'),
        ),
        migrations.AlterField(
            model_name='itemsupplier',
            name='sizeminimum',
            field=models.DecimalField(blank=True, decimal_places=8, default='1.0', help_text='A minimum purchasing quantity', max_digits=20, null=True, verbose_name='size minimum'),
        ),
        migrations.AlterField(
            model_name='itemsupplier',
            name='sizemultiple',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='A multiple purchasing quantity', max_digits=20, null=True, verbose_name='size multiple'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Cost per operationplan unit', max_digits=20, null=True, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='sizemaximum',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='A maximum quantity for operationplans', max_digits=20, null=True, verbose_name='size maximum'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='sizeminimum',
            field=models.DecimalField(blank=True, decimal_places=8, default='1.0', help_text='A minimum quantity for operationplans', max_digits=20, null=True, verbose_name='size minimum'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='sizemultiple',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='A multiple quantity for operationplans', max_digits=20, null=True, verbose_name='size multiple'),
        ),
        migrations.AlterField(
            model_name='operationmaterial',
            name='quantity',
            field=models.DecimalField(decimal_places=8, default='1.00', help_text='Quantity to consume or produce per operationplan unit', max_digits=20, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='operationmaterial',
            name='transferbatch',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Batch size by in which material is produced or consumed', max_digits=20, null=True, verbose_name='transfer batch quantity'),
        ),
        migrations.AlterField(
            model_name='operationplan',
            name='color',
            field=models.DecimalField(blank=True, decimal_places=8, default='0.00', max_digits=20, null=True, verbose_name='color'),
        ),
        migrations.AlterField(
            model_name='operationplan',
            name='criticality',
            field=models.DecimalField(blank=True, decimal_places=8, editable=False, max_digits=20, null=True, verbose_name='criticality'),
        ),
        migrations.AlterField(
            model_name='operationplan',
            name='quantity',
            field=models.DecimalField(decimal_places=8, default='1.00', max_digits=20, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='operationplanmaterial',
            name='onhand',
            field=models.DecimalField(decimal_places=8, max_digits=20, verbose_name='onhand'),
        ),
        migrations.AlterField(
            model_name='operationplanmaterial',
            name='quantity',
            field=models.DecimalField(decimal_places=8, max_digits=20, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='operationplanresource',
            name='quantity',
            field=models.DecimalField(decimal_places=8, max_digits=20, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='operationresource',
            name='quantity',
            field=models.DecimalField(decimal_places=8, default='1.00', max_digits=20, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Cost for using 1 unit of the resource for 1 hour', max_digits=20, null=True, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='maximum',
            field=models.DecimalField(blank=True, decimal_places=8, default='1.00', help_text='Size of the resource', max_digits=20, null=True, verbose_name='maximum'),
        ),
        migrations.AlterField(
            model_name='setuprule',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Cost of the conversion', max_digits=20, null=True, verbose_name='cost'),
        ),
    ]
