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

from django.db import DEFAULT_DB_ALIAS, connections
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.utils.text import capfirst
from django.utils.http import urlquote

from freppledb.common.middleware import _thread_locals
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.report import GridReport
from freppledb.output.models import LoadPlan, Problem, OperationPlan, Demand


class LateOrdersWidget(Widget):
  name = "late_orders"
  title = _("Late orders")
  permissions = (("view_problem_report", "Can view problem report"),)
  async = True
  url = '/problem/?entity=demand&name=late&sord=asc&sidx=startdate'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try: db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("name"))), capfirst(force_unicode(_("due"))),
        capfirst(force_unicode(_("planned date"))), capfirst(force_unicode(_("delay")))
        )
      ]
    for prob in Problem.objects.using(db).filter(name='late',entity='demand').order_by('startdate','-weight')[:limit]:
      result.append('<tr><td class="underline"><a href="%s/demandpegging/%s/">%s</a></td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          request.prefix, urlquote(prob.owner), prob.owner, prob.startdate.date(), prob.enddate.date(), int(prob.weight)
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
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try: db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("name"))), capfirst(force_unicode(_("due"))), capfirst(force_unicode(_("short")))
        )
      ]
    for prob in Problem.objects.using(db).filter(name__gte='short',entity='demand').order_by('startdate')[:limit]:
      result.append('<tr><td class="underline"><a href="%s/demandpegging/%s/">%s</a></td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          request.prefix, urlquote(prob.owner), prob.owner, prob.startdate.date(), int(prob.weight)
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShortOrdersWidget)


class PurchaseQueueWidget(Widget):
  name = "purchase_queue"
  title = _("Purchase queue")
  permissions = (("view_operation_report", "Can view operation report"),)
  async = True
  url = '/operationplan/?locked=0&sidx=startdate&sord=asc&operation__startswith=Purchase'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try: db = _thread_locals.request.database or DEFAULT_DB_ALIAS
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

Dashboard.register(PurchaseQueueWidget)


class ShippingQueueWidget(Widget):
  name = "shipping_queue"
  title = _("Shipping queue")
  permissions = (("view_operation_report", "Can view operation report"),)
  async = True
  url = '/demandplan/?sidx=plandate&sord=asc'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try: db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("demand"))), capfirst(force_unicode(_("customer"))),
        capfirst(force_unicode(_("item"))), capfirst(force_unicode(_("quantity"))),
        capfirst(force_unicode(_("plan date")))
        )
      ]
    for dmdplan in Demand.objects.using(db).filter(planquantity__gt=0).order_by('plandate')[:limit]:
      result.append('<tr><td class="underline"><a href="%s/demandpegging/%s/">%s</a></td><td>%s</td><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          request.prefix, urlquote(dmdplan.demand), dmdplan.demand, dmdplan.customer, dmdplan.item, int(dmdplan.planquantity), dmdplan.plandate.date()
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShippingQueueWidget)


class ResourceQueueWidget(Widget):
  name = "resource_queue"
  title = _("Resource queue")
  permissions = (("view_resource_report", "Can view resource report"),)
  async = True
  url = '/loadplan/?sidx=startdate&sord=asc'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try: db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("resource"))), capfirst(force_unicode(_("operation"))),
        capfirst(force_unicode(_("startdate"))), capfirst(force_unicode(_("enddate"))),
        capfirst(force_unicode(_("quantity")))
        )
      ]
    for ldplan in LoadPlan.objects.using(db).select_related().order_by('startdate')[:limit]:
      result.append('<tr><td class="underline"><a href="%s/loadplan/?theresource=%s&sidx=startdate&sord=asc">%s</a></td><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          request.prefix, urlquote(ldplan.theresource), ldplan.theresource, ldplan.operationplan.operation, ldplan.startdate, ldplan.enddate, int(ldplan.operationplan.quantity)
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceQueueWidget)


class AlertsWidget(Widget):
  name = "alerts"
  title = _("Alerts")
  permissions = (("view_problem_report", "Can view problem report"),)
  async = True
  url = '/problem/'

  @classmethod
  def render(cls, request=None):
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_unicode(_("resource"))), capfirst(force_unicode(_("count"))),
        capfirst(force_unicode(_("weight")))
        )
      ]
    cursor = connections[request.database].cursor()
    query = '''select name, count(*), sum(weight)
      from out_problem
      group by name
      order by name
      '''
    cursor.execute(query)
    for res in cursor.fetchall():
      result.append('<tr><td class="underline"><a href="%s/problem/?name=%s">%s</a></td><td class="aligncenter">%d</td><td class="aligncenter">%d</td></tr>' % (
          request.prefix, urlquote(res[0]), res[0], res[1], res[2]
          ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(AlertsWidget)


class ResourceLoadWidget(Widget):
  name = "resource_utilization"
  title = _("Resource utilization")
  permissions = (("view_resource_report", "Can view resource report"),)
  async = True
  url = '/resource/'
  exporturl = True
  limit = 5

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  javascript = '''
    var res = [];
    var data = [];
    var cnt = 100;
    $("#resLoad").next().find("td.name").each(function() {res.push([cnt,$(this).html()]); cnt-=1;});
    cnt = 100;
    $("#resLoad").next().find("td.util").each(function() {data.push([$(this).html(),cnt]); cnt-=1;});
    Flotr.draw($("#resLoad").get(0), [ data ], {
        HtmlText: true,
        bars: {
          show: true, horizontal: true, barWidth: 0.9,
          lineWidth: 0, shadowSize: 0, fillOpacity: 1
        },
        grid: {
          verticalLines: false, horizontalLines: false
          },
        yaxis: {
          ticks: res
          },
        mouse: {
          track: true, relative: true, lineColor: '#D31A00'
        },
        xaxis: {
          min: 0, autoscaleMargin: 1, title: '%'
        },
        colors: ['#D31A00',]
    });
    '''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    result = [
      '<div id="resLoad" style="width:100%%; height: %spx;"></div>' % (limit*25+30),
      '<table style="display:none">'
      ]
    cursor = connections[request.database].cursor()
    GridReport.getBuckets(request)
    query = '''select
                  theresource,
                  ( coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0) )
                   * 100.0 / coalesce(sum(out_resourceplan.available)+0.000001,1) as avg_util,
                  coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0),
                  coalesce(sum(out_resourceplan.free),0)
                from out_resourceplan
                where out_resourceplan.startdate >= '%s'
                  and out_resourceplan.startdate < '%s'
                group by theresource
                order by 2 desc
              ''' % (request.report_startdate, request.report_enddate)
    cursor.execute(query)
    for res in cursor.fetchall():
      limit -= 1
      if limit < 0: break
      result.append('<tr><td class="name"><span class="underline"><a href="%s/resource/%s/">%s</a></span></td><td class="util">%.2f</td></tr>' % (
        request.prefix, urlquote(res[0]), res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceLoadWidget)


class InventoryByLocationWidget(Widget):
  name = "inventory_by_location"
  title = _("Inventory by location")
  async = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  javascript = '''
    var locs = [];
    var data = [];
    var cnt = 0;
    $("#invByLoc").next().find("td.name").each(function() {locs.push([cnt,$(this).html()]); cnt+=1;});
    cnt = 0;
    $("#invByLoc").next().find("td.data").each(function() {data.push([cnt,$(this).html()]); cnt+=1;});
    Flotr.draw($("#invByLoc").get(0), [ data ], {
        HtmlText: false,
        bars: {
          show: true, horizontal: false, barWidth: 0.9,
          lineWidth: 0, shadowSize: 0, fillOpacity: 1
        },
        grid: {
          verticalLines: false, horizontalLines: false,
          },
        xaxis: {
          ticks: locs, labelsAngle: 45
          },
        mouse: {
          track: true, relative: true, lineColor: '#828915'
        },
        yaxis: {
          min: 0, autoscaleMargin: 1
        },
        colors: ['#828915']
    });
    '''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    result = [
      '<div id="invByLoc" style="width:100%; height: 250px;"></div>',
      '<table style="display:none">'
      ]
    cursor = connections[request.database].cursor()
    query = '''select location_id, coalesce(sum(buffer.onhand * item.price),0)
               from buffer
               inner join item on buffer.item_id = item.name
               group by location_id
               order by 2 desc
              '''
    cursor.execute(query)
    for res in cursor.fetchall():
      limit -= 1
      if limit < 0: break
      result.append('<tr><td class="name">%s</td><td class="data">%.2f</td></tr>' % (
        res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(InventoryByLocationWidget)


class InventoryByItemWidget(Widget):
  name = "inventory_by_item"
  title = _("Inventory by item")
  async = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  javascript = '''
    var locs = [];
    var data = [];
    var cnt = 0;
    $("#invByItem").next().find("td.name").each(function() {locs.push([cnt,$(this).html()]); cnt+=1;});
    cnt = 0;
    $("#invByItem").next().find("td.data").each(function() {data.push([cnt,$(this).html()]); cnt+=1;});
    Flotr.draw($("#invByItem").get(0), [ data ], {
        HtmlText: false,
        bars: {
          show: true, horizontal: false, barWidth: 0.9,
          lineWidth: 0, shadowSize: 0, fillOpacity: 1
        },
        grid : {
          verticalLines: false, horizontalLines: false,
          },
        xaxis: {
          ticks: locs, labelsAngle: -45
          },
        mouse : {
          track: true, relative: true, lineColor: '#D31A00'
        },
        yaxis : {
          min: 0, autoscaleMargin: 1
        },
        colors: ['#D31A00']
    });
    '''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    result = [
      '<div id="invByItem" style="width:100%; height: 250px;"></div>',
      '<table style="display:none">'
      ]
    cursor = connections[request.database].cursor()
    query = '''select item.name, coalesce(sum(buffer.onhand * item.price),0)
               from buffer
               inner join item on buffer.item_id = item.name
               group by item.name
               order by 2 desc
              '''
    cursor.execute(query)
    for res in cursor.fetchall():
      limit -= 1
      if limit < 0: break
      result.append('<tr><td class="name">%s</td><td class="data">%.2f</td></tr>' % (
        res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(InventoryByItemWidget)


class DeliveryPerformanceWidget(Widget):
  name = "delivery_performance"
  title = _("Delivery performance")
  async = True
  green = 90
  yellow = 80

  def args(self):
    return "?%s" % urlencode({'green': self.green, 'yellow': self.yellow})

  javascript = '''
    var val = parseFloat($('#otd_value').html());
    var green = parseInt($('#otd_green').html());
    var yellow = parseInt($('#otd_yellow').html());
    new Gauge("otd", {
      size: 120, label: $('#otd_label').html(), min: 0, max: 100, minorTicks: 5,
      greenZones: [{from: green, to: 100}], yellowZones: [{from: yellow, to: green}],
      value: val
      }).render();
    '''

  @classmethod
  def render(cls, request=None):
    green = int(request.GET.get('green', cls.green))
    yellow = int(request.GET.get('yellow', cls.yellow))
    cursor = connections[request.database].cursor()
    GridReport.getBuckets(request)
    query = '''
      select case when count(*) = 0 then 0 else 100 - sum(late) * 100.0 / count(*) end
      from (
        select
          demand, max(case when plandate > due then 1 else 0 end) late
        from out_demand
        where due < '%s'
        group by demand
      ) demands
      ''' % request.report_enddate
    cursor.execute(query)
    val = cursor.fetchone()[0]
    result = [
      '<div style="text-align: center"><span id="otd"></span></div>',
      '<span id="otd_label" style="display:none">%s</span>' % force_unicode(_("On time delivery")),
      '<span id="otd_value" style="display:none">%s</span>' % val,
      '<span id="otd_green" style="display:none">%s</span>' % green,
      '<span id="otd_yellow" style="display:none">%s</span>' % yellow
      ]
    return HttpResponse('\n'.join(result))

Dashboard.register(DeliveryPerformanceWidget)
