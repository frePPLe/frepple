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

from django.db import migrations


class Migration(migrations.Migration):

  dependencies = [
    ('common', '0011_username'),
  ]

  operations = [

    migrations.RunSQL(
      "insert into common_parameter (name, value, description, lastmodified) values ('plan.administrativeLeadtime','0','Specifies the number of days (value can be decimal) sales orders should be planned ahead of their due date to take into account for an administrative lead time. Default: 0',to_date('05/08/2017','DD/MM/YYYY')) ON CONFLICT (name) DO NOTHING",
      ),
  ]
