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
from django.core.management import call_command
from django.db import migrations


def loadParameters(apps, schema_editor):
  call_command(
    'loaddata', "parameters.json", app_label="odoo",
    verbosity=0, database=schema_editor.connection.alias
    )


class Migration(migrations.Migration):
  dependencies = [
      ('common', '0001_initial'),
  ]

  operations = [
      migrations.RunPython(loadParameters),
  ]
