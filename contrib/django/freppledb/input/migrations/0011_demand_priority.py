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
    ('input', '0010_unique_together'),
  ]

  operations = [
    migrations.AlterField(
      model_name='demand',
      name='priority',
      field=models.IntegerField(help_text='Priority of the demand (lower numbers indicate more important demands)', verbose_name='priority', default=10),
    ),
    migrations.AlterField(
      model_name='buffer',
      name='type',
      field=models.CharField(choices=[('default', 'default'), ('infinite', 'infinite')], null=True, default='default', max_length=20, blank=True, verbose_name='type'),
    ),
  ]
