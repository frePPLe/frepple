#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.core.signals import request_finished
from django.db import DEFAULT_DB_ALIAS
from django.db.models import signals
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from freppledb.common import models as common_models
from freppledb.common.middleware import resetRequest


def removeModelPermissions(app, model, db=DEFAULT_DB_ALIAS, exclude=None):
    q = (
        Permission.objects.all()
        .using(db)
        .filter(content_type__app_label=app, content_type__model=model)
    )
    if exclude:
        q = q.exclude(codename__in=exclude)
    q.delete()


def createExtraPermissions(sender, using=DEFAULT_DB_ALIAS, **kwargs):
    if using != DEFAULT_DB_ALIAS:
        return
    from freppledb.menu import menu
    from freppledb.common.dashboard import Dashboard

    # Create the report permissions for the single menu instance we know about.
    menu.createReportPermissions(sender.name)

    # Create widget permissions
    Dashboard.createWidgetPermissions(sender.name)


def removePermissions(sender, using=DEFAULT_DB_ALIAS, **kwargs):
    removeModelPermissions("admin", "logentry", using)
    removeModelPermissions("contenttypes", "contenttype", using)
    Permission.objects.all().using(using).filter(codename="add_permission").delete()
    Permission.objects.all().using(using).filter(codename="change_permission").delete()
    Permission.objects.all().using(using).filter(codename="delete_permission").delete()
    Permission.objects.all().using(using).filter(codename="view_permission").delete()


signals.post_migrate.connect(removePermissions)
signals.post_migrate.connect(createExtraPermissions)
request_finished.connect(resetRequest)
