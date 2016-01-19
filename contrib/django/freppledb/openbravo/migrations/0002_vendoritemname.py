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
from __future__ import unicode_literals

from django.db import models, migrations
import freppledb.common.fields

from freppledb.common.migrate import AttributeMigration


class Migration(AttributeMigration):

  dependencies = [
    ('openbravo', '0001_initial'),
    ]

  extends_app_label = 'input'

  operations = [
     migrations.AddField(
       model_name='itemsupplier',
       name='vendoritemname',
       field=models.CharField(verbose_name='vendor item name', null=True, blank=True, max_length=300, db_index=True)
       )
    ]
