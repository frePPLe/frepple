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
    ('output', '0002_new_data_model'),
  ]

  operations = [
    migrations.AlterField(
      model_name='constraint',
      name='weight',
      field=models.DecimalField(decimal_places=6, verbose_name='weight', max_digits=15),
    ),
    migrations.AlterField(
      model_name='problem',
      name='weight',
      field=models.DecimalField(decimal_places=6, verbose_name='weight', max_digits=15),
    ),
    migrations.AlterField(
      model_name='resourcesummary',
      name='available',
      field=models.DecimalField(null=True, decimal_places=6, verbose_name='available', max_digits=15),
    ),
    migrations.AlterField(
      model_name='resourcesummary',
      name='free',
      field=models.DecimalField(null=True, decimal_places=6, verbose_name='free', max_digits=15),
    ),
    migrations.AlterField(
      model_name='resourcesummary',
      name='load',
      field=models.DecimalField(null=True, decimal_places=6, verbose_name='load', max_digits=15),
    ),
    migrations.AlterField(
      model_name='resourcesummary',
      name='setup',
      field=models.DecimalField(null=True, decimal_places=6, verbose_name='setup', max_digits=15),
    ),
    migrations.AlterField(
      model_name='resourcesummary',
      name='unavailable',
      field=models.DecimalField(null=True, decimal_places=6, verbose_name='unavailable', max_digits=15),
    ),
  ]
