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
      ('input', '0012_rename_price_to_cost'),
  ]

  operations = [
    migrations.AlterModelOptions(
      name='operationplanmaterial',
      options={'verbose_name_plural': 'operationplan materials', 'ordering': ['item', 'location', 'flowdate'], 'verbose_name': 'operationplan material'},
    ),
    migrations.RemoveField(
      model_name='operationplanmaterial',
      name='buffer',
    ),
    migrations.AddField(
      model_name='operationplanmaterial',
      name='item',
      field=models.ForeignKey(blank=True, to='input.Item', related_name='operationplanmaterials', null=True, verbose_name='item'),
    ),
    migrations.AddField(
      model_name='operationplanmaterial',
      name='location',
      field=models.ForeignKey(blank=True, to='input.Location', related_name='operationplanmaterials', null=True, verbose_name='location'),
    )
  ]
