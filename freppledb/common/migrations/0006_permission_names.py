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


class Migration(migrations.Migration):

  dependencies = [
    ('common', '0003_wizard'),
  ]

  operations = [
    # Irreversible migration
    migrations.RunSQL(
      '''
      update auth_permission
      set content_type_id =
         (select id from django_content_type where app_label = 'auth' and model = 'permission')
      where content_type_id in (select id from django_content_type where model = 'reports')
      '''
    ),
    # Irreversible migration
    migrations.RunSQL(
      '''
      delete from django_content_type where model = 'reports'
      '''
    ),
  ]
