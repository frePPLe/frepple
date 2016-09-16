#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from django.core.signals import request_finished
from django.db.models import signals, get_models
from django.db import DEFAULT_DB_ALIAS
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.template.base import add_to_builtins

from freppledb.common import models as common_models
from freppledb.common.middleware import resetRequest


# Make our tags built-in, so we don't have to load them any more in our
# templates with a 'load' tag.
add_to_builtins('freppledb.common.templatetags.base_utils')


def removeModelPermissions(app, model, db=DEFAULT_DB_ALIAS):
  Permission.objects.all().using(db).filter(content_type__app_label=app, content_type__model=model).delete()


def createViewPermissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS, **kwargs):  
  if db != DEFAULT_DB_ALIAS:
    return
  # Create model read permissions
  for m in get_models(app):
    p = Permission.objects.get_or_create(
          codename='view_%s' % m._meta.model_name,
          content_type=ContentType.objects.db_manager(db).get_for_model(m)
          )[0]
    p.name = 'Can view %s' % m._meta.verbose_name_raw
    p.save()


def createExtraPermissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS, **kwargs):
  if db != DEFAULT_DB_ALIAS:
    return
  # Create the report permissions for the single menu instance we know about.
  appname = app.__name__.replace(".models", "")
  from freppledb.menu import menu
  menu.createReportPermissions(appname)
  # Create widget permissions
  from freppledb.common.dashboard import Dashboard
  Dashboard.createWidgetPermissions(appname)


def removePermissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS, **kwargs):
  removeModelPermissions("common", "wizard", db)
  removeModelPermissions("common", "scenario", db)
  removeModelPermissions("admin", "logentry", db)
  removeModelPermissions("contenttypes", "contenttype", db)
  removeModelPermissions("auth", "permission", db)
  
  
signals.post_syncdb.connect(removePermissions)
signals.post_syncdb.connect(createExtraPermissions)
signals.post_syncdb.connect(createViewPermissions, common_models)
request_finished.connect(resetRequest)