# Copyright (C) 2021 by frePPLe bv
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

    dependencies = [("input", "0055_itemdistribution_batchwindow")]

    operations = [
        migrations.RunSQL(
            """
            insert into common_parameter (name, value, lastmodified, description)
            values (
              'WIP.produce_full_quantity', 'false', now(),
              'Determines whether partially completed manufacturing orders still produce the full quantity. Default is false, i.e. partially completed manufacturing orders produce only the remaining quantity.'
              )
            on conflict (name) do nothing
            """,
            """
            delete from parameter where name = 'WIP.produce_full_quantity'
            """,
        )
    ]
