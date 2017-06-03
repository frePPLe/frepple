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

from django.db import migrations


class Migration(migrations.Migration):

  dependencies = [
    ('output', '0001_initial'),
  ]

  operations = [
    migrations.RemoveField(model_name='flowplan', name='operationplan'),
    migrations.RemoveField(model_name='loadplan', name='operationplan'),
    migrations.DeleteModel(name='FlowPlan'),
    migrations.DeleteModel(name='LoadPlan'),
    migrations.DeleteModel(name='OperationPlan'),
    migrations.DeleteModel(name='DemandPegging'),
    migrations.AlterModelOptions(
      name='resourcesummary',
      options={'verbose_name': 'resource summary', 'verbose_name_plural': 'resource summaries', 'ordering': ['resource', 'startdate']},
    ),
    migrations.RenameField('resourcesummary', 'theresource', 'resource'),
    migrations.AlterUniqueTogether(
      name='resourcesummary',
      unique_together=set([('resource', 'startdate')]),
    ),
    migrations.DeleteModel(
      name='Demand',
    ),
  ]
