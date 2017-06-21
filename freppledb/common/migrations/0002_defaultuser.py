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
from datetime import datetime

from django.db import migrations


def createAdminUser(apps, schema_editor):
  if not schema_editor.connection.alias == 'default':
    return
  from django.contrib.auth import get_user_model
  User = get_user_model()
  usr = User.objects.create_superuser('admin', 'your@company.com', 'admin')
  usr.first_name = 'admin'
  usr.last_name = 'admin'
  usr.date_joined = datetime(2000, 1, 1)
  usr.horizontype = True
  usr.horizonlength = 12
  usr.horizonunit = "month"
  usr.language = "auto"
  usr.save()


class Migration(migrations.Migration):
  dependencies = [
      ('common', '0001_initial'),
      ('execute', '0001_initial'),
  ]

  operations = [
      migrations.RunPython(createAdminUser),
  ]
