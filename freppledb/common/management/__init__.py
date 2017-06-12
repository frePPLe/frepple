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
from django.db import DEFAULT_DB_ALIAS
from django.db.models import signals
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from freppledb.common import models as common_models
from freppledb.common.middleware import resetRequest


def removeModelPermissions(app, model, db=DEFAULT_DB_ALIAS):
  Permission.objects.all().using(db).filter(content_type__app_label=app, content_type__model=model).delete()


def createViewPermissions(sender, using=DEFAULT_DB_ALIAS, **kwargs):
  if using != DEFAULT_DB_ALIAS or 'apps' not in kwargs:
    return
  # Create model read permissions
  for m in kwargs['apps'].get_models():
    p = Permission.objects.get_or_create(
           codename='view_%s' % m._meta.model_name,
           content_type=ContentType.objects.db_manager(using).get_for_model(m)
           )[0]
    p.name = 'Can view %s' % m._meta.verbose_name_raw
    p.save()


def createExtraPermissions(sender, using=DEFAULT_DB_ALIAS, **kwargs):
  if using != DEFAULT_DB_ALIAS:
    return
  # Create the report permissions for the single menu instance we know about.
  from freppledb.menu import menu
  menu.createReportPermissions(sender.name)
  # Create widget permissions
  from freppledb.common.dashboard import Dashboard
  Dashboard.createWidgetPermissions(sender.name)


def removePermissions(sender, using=DEFAULT_DB_ALIAS, **kwargs):
  removeModelPermissions("common", "wizard", using)
  removeModelPermissions("common", "scenario", using)
  removeModelPermissions("admin", "logentry", using)
  removeModelPermissions("contenttypes", "contenttype", using)
  Permission.objects.all().using(using).filter(codename="add_permission").delete()
  Permission.objects.all().using(using).filter(codename="change_permission").delete()
  Permission.objects.all().using(using).filter(codename="delete_permission").delete()


signals.post_migrate.connect(removePermissions)
signals.post_migrate.connect(createExtraPermissions)
signals.post_migrate.connect(createViewPermissions)
request_finished.connect(resetRequest)