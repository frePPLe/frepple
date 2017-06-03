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
    ('input', '0002_resource_for_po_and_do'),
    ]

  operations = [
    migrations.AddField(
      model_name='itemdistribution',
      name='fence',
      field=freppledb.common.fields.DurationField(help_text='Frozen fence for creating new shipments', null=True, blank=True, verbose_name='fence', decimal_places=4, max_digits=15),
    ),
    migrations.AddField(
      model_name='itemsupplier',
      name='fence',
      field=freppledb.common.fields.DurationField(help_text='Frozen fence for creating new procurements', null=True, blank=True, verbose_name='fence', decimal_places=4, max_digits=15),
    ),
  ]
