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
import django.db.models.deletion


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0026_operationplanmaterial_nullable'),
  ]

  operations = [
    migrations.AddField(
      model_name='resource',
      name='efficiency_calendar',
      field=models.ForeignKey(blank=True, help_text='Calendar defining the efficiency percentage of the resource varying over time', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='input.Calendar', verbose_name='efficiency % calendar'),
    ),
    ]
