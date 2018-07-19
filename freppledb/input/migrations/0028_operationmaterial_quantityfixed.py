#
# Copyright (C) 2018 by frePPLe bvba
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
    ('input', '0027_resource_efficiency_calendar'),
  ]

  operations = [
    migrations.AddField(
      model_name='operationmaterial',
      name='quantity_fixed',
      field=models.DecimalField(blank=True, null=True, decimal_places=8, help_text='Fixed quantity to consume or produce', max_digits=20, verbose_name='fixed quantity'),
    ),
    migrations.AlterField(
      model_name='operationmaterial',
      name='type',
      field=models.CharField(blank=True, choices=[('start', 'Start'), ('end', 'End'), ('transfer_batch', 'Batch transfer')], default='start', help_text='Consume/produce material at the start or the end of the operationplan', max_length=20, null=True, verbose_name='type'),
    ),
    migrations.RunSQL('''
      update operationmaterial
      set type='start', quantity_fixed=quantity, quantity=0
      where type = 'fixed_start'
      '''),
    migrations.RunSQL('''
      update operationmaterial
      set type='end', quantity_fixed=quantity, quantity=0
      where type = 'fixed_end'
      ''')
  ]
