#
# Copyright (C) 2018 by frePPLe bvba
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

    dependencies = [("input", "0034_sizemaximum")]

    operations = [
        migrations.RunSQL(
            """
      insert into common_parameter (name, value, lastmodified, description)
      values (
        'WIP.consume_material', 'true', now(),
        'Determines whether confirmed manufacturing orders consume material or not. Default is true.'
        )
      on conflict (name) do nothing
      """,
            """
      delete from parameter where name = 'WIP.consume_material'
      """,
        ),
        migrations.RunSQL(
            """
      insert into common_parameter (name, value, lastmodified, description)
      values (
        'WIP.consume_capacity', 'true', now(),
        'Determines whether confirmed manufacturing orders, purchase orders and distribution orders consume capacity or not. Default is true.'
        )
      on conflict (name) do nothing
      """,
            """
      delete from parameter where name = 'WIP.consume_capacity'
      """,
        ),
    ]
