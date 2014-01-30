#
# Copyright (C) 2014 by Johan De Taeye, frePPLe bvba
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

from urllib import urlencode

from django.db import DEFAULT_DB_ALIAS
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from freppledb.common.middleware import current_request
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.output.models import Problem, OperationPlan


class LateOrdersWidget(Widget):
  name = "late_orders"
  title = _("Late orders")
  permissions = (("view_problem_report", "Can view problem report"),)
  async = True
  url = '/problem/?entity=demand&name=late&sord=asc&sidx=startdate'

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = request.GET.get('limit',20)
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = []
    for prob in Problem.objects.using(db).filter(name='late',entity='demand').order_by('startdate','-weight')[:limit]:
      result.append('%s %s %s %s<br/>' % (prob.owner, prob.startdate.date(), prob.enddate.date(), int(prob.weight))) #capfirst(force_unicode(_(entry.content_type.name))) )
    return HttpResponse('\n'.join(result))

Dashboard.register(LateOrdersWidget)


class ShortOrdersWidget(Widget):
  name = "short_orders"
  title = _("Short orders")
  permissions = (("view_problem_report", "Can view problem report"),)
  async = True
  url = '/problem/?entity=demand&name=short&sord=asc&sidx=startdate'

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = request.GET.get('limit',20)
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = []
    for prob in Problem.objects.using(db).filter(name='short',entity='demand').order_by('-startdate')[:limit]:
      result.append('%s %s %s %s<br/>' % (prob.owner, prob.startdate.date(), prob.enddate.date(), int(prob.weight))) #capfirst(force_unicode(_(entry.content_type.name))) )
    return HttpResponse('\n'.join(result))

Dashboard.register(ShortOrdersWidget)


class PurchasingQueueWidget(Widget):
  name = "purchasing_queue"
  title = _("Purchasing queue")
  permissions = (("view_operation_report", "Can view operation report"),)
  async = True
  url = '/operationplan/?locked=0&sidx=startdate&sord=asc&operation__startswith=Purchase'

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = request.GET.get('limit',20)
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = []
    for opplan in OperationPlan.objects.using(db).filter(operation__startswith='Purchase ', locked=False).order_by('startdate')[:limit]:
      result.append('%s %s %s %s<br/>' % (opplan.operation, opplan.startdate.date(), opplan.enddate.date(), int(opplan.quantity))) #capfirst(force_unicode(_(entry.content_type.name))) )
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchasingQueueWidget)
