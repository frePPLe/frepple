#
# Copyright (C) 2019 by frePPLe bvba
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
import django.db.models.deletion


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0038_operationplanreference'),
  ]

  operations = [
    migrations.RemoveField(
      model_name='operationplan',
      name='id',
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='reference',
      field=models.CharField(help_text='Unique identifier', max_length=300, primary_key=True, serialize=False, verbose_name='reference'),
    ),
    migrations.RemoveField(
      model_name='operationplanmaterial',
      name='operationplan',
    ),
    migrations.RemoveField(
      model_name='operationplanresource',
      name='operationplan',
    ),
    migrations.AddField(
      model_name='operationplanmaterial',
      name='operationplan',
      field=models.ForeignKey(verbose_name='operationplan', related_name='materials', to='input.OperationPlan')
    ),
    migrations.AddField(
      model_name='operationplanresource',
      name='operationplan',
      field=models.ForeignKey(verbose_name='operationplan', related_name='resources', to='input.OperationPlan')
    ),

    # Remaining migrations are just catching up on python-side model
    # changes without impact on the database schema. Just adding them
    # get a clean slate of migrations.

    migrations.AlterField(
      model_name='buffer',
      name='minimum_calendar',
      field=models.ForeignKey(blank=True, help_text='Calendar storing a time-dependent safety stock profile', null=True, on_delete=django.db.models.deletion.SET_NULL, to='input.Calendar', verbose_name='minimum calendar'),
    ),
    migrations.AlterField(
      model_name='location',
      name='available',
      field=models.ForeignKey(blank=True, help_text='Calendar defining the working hours and holidays', null=True, on_delete=django.db.models.deletion.SET_NULL, to='input.Calendar', verbose_name='available'),
    ),
    migrations.AlterField(
      model_name='operation',
      name='available',
      field=models.ForeignKey(blank=True, help_text='Calendar defining the working hours and holidays', null=True, on_delete=django.db.models.deletion.SET_NULL, to='input.Calendar', verbose_name='available'),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='type',
      field=models.CharField(choices=[('STCK', 'inventory'), ('MO', 'manufacturing order'), ('PO', 'purchase order'), ('DO', 'distribution order'), ('DLVR', 'delivery order')], db_index=True, default='MO', help_text='Order type', max_length=5, verbose_name='type'),
    ),
    migrations.AlterField(
      model_name='operationplanmaterial',
      name='status',
      field=models.CharField(blank=True, choices=[('proposed', 'proposed'), ('confirmed', 'confirmed'), ('closed', 'closed')], help_text='status of the material production or consumption', max_length=20, null=True, verbose_name='status'),
    ),
    migrations.AlterField(
      model_name='operationplanresource',
      name='status',
      field=models.CharField(blank=True, choices=[('proposed', 'proposed'), ('confirmed', 'confirmed'), ('closed', 'closed')], help_text='Status of the OperationPlanResource', max_length=20, null=True, verbose_name='status'),
    ),
    migrations.AlterField(
      model_name='operationresource',
      name='quantity',
      field=models.DecimalField(decimal_places=8, default='1.00', help_text='Required quantity of the resource', max_digits=20, verbose_name='quantity'),
    ),
    migrations.AlterField(
      model_name='operationresource',
      name='quantity_fixed',
      field=models.DecimalField(blank=True, decimal_places=8, help_text='constant part of the capacity consumption (bucketized resources only)', max_digits=20, null=True, verbose_name='quantity fixed'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='available',
      field=models.ForeignKey(blank=True, help_text='Calendar defining the working hours and holidays', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='input.Calendar', verbose_name='available'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='efficiency',
      field=models.DecimalField(blank=True, decimal_places=8, help_text='Efficiency percentage of the resource', max_digits=20, null=True, verbose_name='efficiency %'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='efficiency_calendar',
      field=models.ForeignKey(blank=True, help_text='Calendar defining the efficiency percentage of the resource varying over time', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='input.Calendar', verbose_name='efficiency %% calendar'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='maximum_calendar',
      field=models.ForeignKey(blank=True, help_text='Calendar defining the resource size varying over time', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='input.Calendar', verbose_name='maximum calendar'),
    ),
    migrations.AlterField(
      model_name='resource',
      name='type',
      field=models.CharField(blank=True, choices=[('default', 'default'), ('buckets', 'buckets'), ('buckets_day', 'buckets_day'), ('buckets_week', 'buckets_week'), ('buckets_month', 'buckets_month'), ('infinite', 'infinite')], default='default', max_length=20, null=True, verbose_name='type'),
    ),
    migrations.AlterField(
      model_name='setuprule',
      name='id',
      field=models.AutoField(primary_key=True, serialize=False, verbose_name='identifier'),
    ),
    migrations.AlterModelOptions(
      name='deliveryorder',
      options={'verbose_name': 'delivery order', 'verbose_name_plural': 'delivery orders'},
    ),
    migrations.AlterField(
      model_name='operationplanmaterial',
      name='periodofcover',
      field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True, verbose_name='period of cover'),
    ),
  ]
