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
    ('input', '0011_demand_priority'),
  ]

  operations = [
    migrations.AddField(
      model_name='item',
      name='cost',
      field=models.DecimalField(null=True, blank=True, help_text='Cost of the item', max_digits=15, decimal_places=6, verbose_name='cost'),
    ),
    migrations.RunSQL('''
      update item
      set cost = price
      '''),
    migrations.RemoveField(
      model_name='item',
      name='price',
    )
  ]
