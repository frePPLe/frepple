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

from urllib import urlencode, quote

from django.db import DEFAULT_DB_ALIAS, connections
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.utils.text import capfirst

from freppledb.common.middleware import current_request
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.output.models import Problem, OperationPlan


class LateOrdersWidget(Widget):
  name = "late_orders"
  title = _("Late orders")
  permissions = (("view_problem_report", "Can view problem report"),)
  async = True
  url = '/problem/?entity=demand&name=late&sord=asc&sidx=startdate'
  exporturl = True

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = request.GET.get('limit',20)
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("name"))), capfirst(force_unicode(_("due"))),
        capfirst(force_unicode(_("planned date"))), capfirst(force_unicode(_("delay")))
        )
      ]
    for prob in Problem.objects.using(db).filter(name='late',entity='demand').order_by('startdate','-weight')[:limit]:
      result.append('<tr onclick="window.location.href=\'%s/demandpegging/%s/\';"><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          request.prefix, quote(prob.owner), prob.owner, prob.startdate.date(), prob.enddate.date(), int(prob.weight)
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(LateOrdersWidget)


class ShortOrdersWidget(Widget):
  name = "short_orders"
  title = _("Short orders")
  permissions = (("view_problem_report", "Can view problem report"),)
  async = True
  # Note the gte filter lets pass "short" and "unplanned", and filters out
  # "late" and "early".
  url = '/problem/?entity=demand&name__gte=short&sord=asc&sidx=startdate'
  exporturl = True

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = request.GET.get('limit',20)
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("name"))), capfirst(force_unicode(_("due"))), capfirst(force_unicode(_("short")))
        )
      ]
    for prob in Problem.objects.using(db).filter(name__gte='short',entity='demand').order_by('startdate')[:limit]:
      result.append('<tr onclick="window.location.href=\'%s/demandpegging/%s/\';"><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          request.prefix, quote(prob.owner), prob.owner, prob.startdate.date(), int(prob.weight)
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShortOrdersWidget)


class PurchasingQueueWidget(Widget):
  name = "purchasing_queue"
  title = _("Purchasing queue")
  permissions = (("view_operation_report", "Can view operation report"),)
  async = True
  url = '/operationplan/?locked=0&sidx=startdate&sord=asc&operation__startswith=Purchase'
  exporturl = True

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = request.GET.get('limit',20)
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("operation"))), capfirst(force_unicode(_("startdate"))),
        capfirst(force_unicode(_("enddate"))), capfirst(force_unicode(_("quantity")))
        )
      ]
    for opplan in OperationPlan.objects.using(db).filter(operation__startswith='Purchase ', locked=False).order_by('startdate')[:limit]:
      result.append('<tr><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          opplan.operation, opplan.startdate.date(), opplan.enddate.date(), int(opplan.quantity)
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchasingQueueWidget)


class ResourceLoadWidget(Widget):
  name = "resource_load"
  title = _("Resource load")
  permissions = (("view_resource_report", "Can view resource report"),)
  async = True
  url = '/resource/'
  exporturl = True

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit',20))
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("resource"))), capfirst(force_unicode(_("utilization")))
        )
      ]
    #            where out_resourceplan.startdate >= '%s'
    #            and out_resourceplan.startdate < '%s'
    cursor = connections[request.database].cursor()
    query = '''select
                  theresource,
                  ( coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0) )
                   * 100.0 / coalesce(sum(out_resourceplan.available)+0.000001,1) as avg_util
                from out_resourceplan
                group by theresource
                order by 2 desc
              '''
    cursor.execute(query)
    for res in cursor.fetchall():
      limit -= 1
      if limit < 0: break
      result.append('<tr onclick="window.location.href=\'%s/resource/%s/\';"><td>%s</td><td class="aligncenter">%.2f</td></tr>' % (
          request.prefix, quote(res[0]), res[0], res[1]
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceLoadWidget)
