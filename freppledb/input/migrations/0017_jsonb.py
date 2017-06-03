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
import freppledb.common.fields


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0016_squashed_41'),
  ]

  operations = [
    migrations.AlterField(
      model_name='demand',
      name='plan',
      field=freppledb.common.fields.JSONBField(blank=True, editable=False, default='{}', null=True),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='plan',
      field=freppledb.common.fields.JSONBField(blank=True, editable=False, default='{}', null=True),
    ),
  ]
