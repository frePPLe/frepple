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
    ('input', '0037_supplier_available'),
  ]

  operations = [
    migrations.RunSQL('''
      update operationplan
      set reference = id
      where reference is null
        or reference in (
          select opplan2.reference
          from operationplan as opplan2
          group by opplan2.reference
          having count(reference) > 1
          )
      '''),
    migrations.RunSQL('''
      delete from operationplan where owner_id is not null
      '''),
    migrations.RunSQL('''
      truncate table operationplanmaterial, operationplanresource
      '''),
    # The hack of 0021_operationplanresource needs to be reverted first.
    # Django's migrations otherwise are confused on the nature of the field.
    migrations.RunSQL(
      'alter table operationplanresource rename column resource_id to resource'
    ),
    migrations.RemoveField(
      model_name='operationplanresource',
      name='resource',
    ),
    migrations.AddField(
      model_name='operationplanresource',
      name='resource',
      field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operationplanresources', to='input.Resource', verbose_name='resource'),
    ),
    migrations.AlterUniqueTogether(
      name='operationplanresource',
      unique_together=set([('resource', 'operationplan')]),
    ),
  ]
