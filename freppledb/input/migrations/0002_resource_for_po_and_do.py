#
# Copyright (C) 2015 by frePPLe bvba
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

from django.db import models, migrations


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0001_initial'),
  ]

  operations = [
    migrations.AddField(
      model_name='itemdistribution',
      name='resource',
      field=models.ForeignKey(verbose_name='resource', help_text='Resource to model the distribution capacity', null=True, related_name='itemdistributions', to='input.Resource', blank=True),
    ),
    migrations.AddField(
      model_name='itemdistribution',
      name='resource_qty',
      field=models.DecimalField(verbose_name='resource quantity', help_text='Resource capacity consumed per distributed unit', null=True, decimal_places=4, blank=True, max_digits=15, default='1.0'),
    ),
    migrations.AddField(
      model_name='itemsupplier',
      name='resource',
      field=models.ForeignKey(verbose_name='resource', help_text='Resource to model the supplier capacity', null=True, related_name='itemsuppliers', to='input.Resource', blank=True),
    ),
    migrations.AddField(
      model_name='itemsupplier',
      name='resource_qty',
      field=models.DecimalField(verbose_name='resource quantity', help_text='Resource capacity consumed per purchased unit', null=True, decimal_places=4, blank=True, max_digits=15, default='1.0'),
    ),
  ]
