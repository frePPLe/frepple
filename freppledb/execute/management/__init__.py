# Copyright (C) 2014 by frePPLe bvba
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

from django.db import DEFAULT_DB_ALIAS
from django.db.models import signals
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from freppledb.common.management import removeModelPermissions


def updatePermissions(using=DEFAULT_DB_ALIAS, **kwargs):
  removeModelPermissions("execute", "task", using)
  p = Permission.objects.get_or_create(
    codename='run_db',
    content_type=ContentType.objects.get(model="permission", app_label="auth")
    )[0]
  p.name = 'Run database operations'
  p.save()


signals.post_migrate.connect(updatePermissions)
