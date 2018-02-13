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
    ('input', '0022_demand_due'),
  ]

  operations = [
    migrations.AddField(
        model_name='operationmaterial',
        name='transferbatch',
        field=models.DecimalField(decimal_places=6, help_text='Batch size by in which material is produced or consumed', null=True, blank=True, max_digits=15, verbose_name='transfer batch quantity'),
    ),
  ]
