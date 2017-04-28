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
    ('common', '0008_squashed_41'),
  ]

  operations = [
    migrations.AlterField(
      model_name='userpreference',
      name='value',
      field=freppledb.common.fields.JSONBField(max_length=1000),
    ),
  ]
