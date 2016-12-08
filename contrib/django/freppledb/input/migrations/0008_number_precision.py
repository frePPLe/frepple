#
# Copyright (C) 2016 by frePPLe bvba
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
    ('input', '0007_wizard'),
  ]

  operations = [
    migrations.AlterField(
      model_name='buffer',
      name='minimum',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='minimum', blank=True, max_digits=15, default='0.00', help_text='safety stock'),
    ),
    migrations.AlterField(
      model_name='buffer',
      name='onhand',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='onhand', blank=True, max_digits=15, default='0.00', help_text='current inventory'),
    ),
    migrations.AlterField(
      model_name='calendar',
      name='defaultvalue',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='default value', blank=True, max_digits=15, default='0.00', help_text='Value to be used when no entry is effective'),
    ),
    migrations.AlterField(
        model_name='calendarbucket',
        name='calendar',
        field=models.ForeignKey(verbose_name='calendar', to='input.Calendar', related_name='buckets'),
    ),
    migrations.AlterField(
      model_name='calendarbucket',
      name='value',
      field=models.DecimalField(default='0.00', decimal_places=6, verbose_name='value', blank=True, max_digits=15),
    ),
    migrations.AlterField(
      model_name='demand',
      name='minshipment',
      field=models.DecimalField(decimal_places=6, verbose_name='minimum shipment', blank=True, max_digits=15, null=True, help_text='Minimum shipment quantity when planning this demand'),
    ),
    migrations.AlterField(
      model_name='demand',
      name='quantity',
      field=models.DecimalField(decimal_places=6, verbose_name='quantity', max_digits=15),
    ),
    migrations.AlterField(
      model_name='demand',
      name='status',
      field=models.CharField(max_length=10, choices=[('inquiry', 'inquiry'), ('quote', 'quote'), ('open', 'open'), ('closed', 'closed'), ('canceled', 'canceled')], verbose_name='status', blank=True, default='open', null=True, help_text='Status of the demand. Only "open" demands are planned'),
    ),
    migrations.AlterField(
      model_name='item',
      name='price',
      field=models.DecimalField(decimal_places=6, verbose_name='price', blank=True, max_digits=15, null=True, help_text='Selling price of the item'),
    ),
    migrations.AlterField(
      model_name='itemdistribution',
      name='cost',
      field=models.DecimalField(decimal_places=6, verbose_name='cost', blank=True, max_digits=15, null=True, help_text='Shipping cost per unit'),
    ),
    migrations.AlterField(
      model_name='itemdistribution',
      name='resource_qty',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='resource quantity', blank=True, max_digits=15, default='1.0', help_text='Resource capacity consumed per distributed unit'),
    ),
    migrations.AlterField(
      model_name='itemdistribution',
      name='sizeminimum',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='size minimum', blank=True, max_digits=15, default='1.0', help_text='A minimum shipping quantity'),
    ),
    migrations.AlterField(
      model_name='itemdistribution',
      name='sizemultiple',
      field=models.DecimalField(decimal_places=6, verbose_name='size multiple', blank=True, max_digits=15, null=True, help_text='A multiple shipping quantity'),
    ),
    migrations.AlterField(
      model_name='itemsupplier',
      name='cost',
      field=models.DecimalField(decimal_places=6, verbose_name='cost', blank=True, max_digits=15, null=True, help_text='Purchasing cost per unit'),
    ),
    migrations.AlterField(
      model_name='itemsupplier',
      name='resource_qty',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='resource quantity', blank=True, max_digits=15, default='1.0', help_text='Resource capacity consumed per purchased unit'),
    ),
    migrations.AlterField(
      model_name='itemsupplier',
      name='sizeminimum',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='size minimum', blank=True, max_digits=15, default='1.0', help_text='A minimum purchasing quantity'),
    ),
    migrations.AlterField(
      model_name='itemsupplier',
      name='sizemultiple',
      field=models.DecimalField(decimal_places=6, verbose_name='size multiple', blank=True, max_digits=15, null=True, help_text='A multiple purchasing quantity'),
    ),
    migrations.AlterField(
      model_name='operation',
      name='cost',
      field=models.DecimalField(decimal_places=6, verbose_name='cost', blank=True, max_digits=15, null=True, help_text='Cost per operationplan unit'),
    ),
    migrations.AlterField(
      model_name='operation',
      name='sizemaximum',
      field=models.DecimalField(decimal_places=6, verbose_name='size maximum', blank=True, max_digits=15, null=True, help_text='A maximum quantity for operationplans'),
    ),
    migrations.AlterField(
      model_name='operation',
      name='sizeminimum',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='size minimum', blank=True, max_digits=15, default='1.0', help_text='A minimum quantity for operationplans'),
    ),
    migrations.AlterField(
      model_name='operation',
      name='sizemultiple',
      field=models.DecimalField(decimal_places=6, verbose_name='size multiple', blank=True, max_digits=15, null=True, help_text='A multiple quantity for operationplans'),
    ),
    migrations.AlterField(
      model_name='operationmaterial',
      name='name',
      field=models.CharField(null=True, max_length=300, help_text='Optional name of this operation material', verbose_name='name', blank=True),
    ),
    migrations.AlterField(
      model_name='operationmaterial',
      name='priority',
      field=models.IntegerField(default=1, null=True, help_text='Priority of this operation material in a group of alternates', verbose_name='priority', blank=True),
    ),
    migrations.AlterField(
      model_name='operationmaterial',
      name='quantity',
      field=models.DecimalField(default='1.00', decimal_places=6, help_text='Quantity to consume or produce per operationplan unit', verbose_name='quantity', max_digits=15),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='criticality',
      field=models.DecimalField(decimal_places=6, editable=False, verbose_name='criticality', blank=True, max_digits=15, null=True),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='due',
      field=models.DateTimeField(null=True, help_text='Due date of the demand/forecast', verbose_name='due', blank=True),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='name',
      field=models.CharField(null=True, max_length=1000, db_index=True, verbose_name='name', blank=True),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='quantity',
      field=models.DecimalField(default='1.00', decimal_places=6, verbose_name='quantity', max_digits=15),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='type',
      field=models.CharField(max_length=5, db_index=True, choices=[('STCK', 'inventory'), ('MO', 'manufacturing order'), ('PO', 'purchase order'), ('DO', 'distribution order'), ('DLVR', 'customer shipment')], verbose_name='type', default='MO', help_text='Order type'),
    ),
    migrations.AlterField(
      model_name='operationplanmaterial',
      name='onhand',
      field=models.DecimalField(decimal_places=6, verbose_name='onhand', max_digits=15),
    ),
    migrations.AlterField(
      model_name='operationplanmaterial',
      name='quantity',
      field=models.DecimalField(decimal_places=6, verbose_name='quantity', max_digits=15),
    ),
    migrations.AlterField(
      model_name='operationplanresource',
      name='quantity',
      field=models.DecimalField(decimal_places=6, verbose_name='quantity', max_digits=15),
    ),
    migrations.AlterField(
      model_name='operationresource',
      name='quantity',
      field=models.DecimalField(default='1.00', decimal_places=6, verbose_name='quantity', max_digits=15),
    ),
    migrations.AlterField(
      model_name='resource',
      name='cost',
      field=models.DecimalField(decimal_places=6, verbose_name='cost', blank=True, max_digits=15, null=True, help_text='Cost for using 1 unit of the resource for 1 hour'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='maximum',
      field=models.DecimalField(decimal_places=6, null=True, verbose_name='maximum', blank=True, max_digits=15, default='1.00', help_text='Size of the resource'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='type',
      field=models.CharField(max_length=20, choices=[('default', 'default'), ('buckets', 'buckets'), ('infinite', 'infinite')], verbose_name='type', blank=True, default='default', null=True),
    ),
    migrations.AlterField(
      model_name='setuprule',
      name='cost',
      field=models.DecimalField(decimal_places=6, verbose_name='cost', blank=True, max_digits=15, null=True, help_text='Cost of the conversion'),
    ),
  ]
