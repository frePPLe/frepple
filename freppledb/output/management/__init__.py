# Copyright (C) 2013-2014 by frePPLe bvba
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

from freppledb.common.management import removeModelPermissions


def removePermissions(using=DEFAULT_DB_ALIAS, **kwargs):
  removeModelPermissions("output", "problem", using)
  removeModelPermissions("output", "constraint", using)
  removeModelPermissions("output", "resourcesummary", using)


signals.post_migrate.connect(removePermissions)
