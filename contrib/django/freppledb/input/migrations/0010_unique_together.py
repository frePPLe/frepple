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
    ('input', '0009_operationplan_mat_res'),
  ]

  operations = [
    migrations.AlterField(
      model_name='operationplan',
      name='id',
      field=models.AutoField(primary_key=True, serialize=False, verbose_name='identifier', help_text='Unique identifier of an operationplan'),
    ),
    migrations.AlterUniqueTogether(
      name='calendarbucket',
      unique_together=set([('calendar', 'startdate', 'enddate', 'priority')]),
    ),
    migrations.AlterUniqueTogether(
      name='suboperation',
      unique_together=set([('operation', 'priority', 'suboperation')]),
    ),
  ]
