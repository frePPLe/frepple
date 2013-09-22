# Copyright (C) 2013 by Johan De Taeye, frePPLe bvba
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
from django.db.models import get_model, signals
from django.contrib.auth.models import Permission

from freppledb.output import models as output_app

def removeDefaultPermissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS, **kwargs):
  # Delete the default permissions that were created for the models in the output app
  Permission.objects.all().filter(content_type__app_label="output", codename__startswith="change").delete()
  Permission.objects.all().filter(content_type__app_label="output", codename__startswith="add").delete()
  Permission.objects.all().filter(content_type__app_label="output", codename__startswith="delete").delete()

signals.post_syncdb.connect(removeDefaultPermissions, output_app)
