#
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

from urllib.parse import urlencode

from django.db import DEFAULT_DB_ALIAS, connections
from django.http import HttpResponse
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from freppledb.common.middleware import _thread_locals
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.report import GridReport
from freppledb.input.models import PurchaseOrder, DistributionOrder
from freppledb.output.models import LoadPlan, Problem, OperationPlan, Demand


class LateOrdersWidget(Widget):
  name = "late_orders"
  title = _("Late orders")
  tooltip = _("Shows orders that will be delivered after their due date")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/problem/?entity=demand&name=late&sord=asc&sidx=startdate'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("name"))), capfirst(force_text(_("due"))),
        capfirst(force_text(_("planned date"))), capfirst(force_text(_("delay")))
        )
      ]
    alt = False
    for prob in Problem.objects.using(db).filter(name='late', entity='demand').order_by('startdate', '-weight')[:limit]:
      result.append('<tr%s><td class="underline"><a href="%s/demandpegging/%s/">%s</a></td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', request.prefix, urlquote(prob.owner), escape(prob.owner), prob.startdate.date(), prob.enddate.date(), int(prob.weight)
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(LateOrdersWidget)


class ShortOrdersWidget(Widget):
  name = "short_orders"
  title = _("Short orders")
  tooltip = _("Shows orders that are not planned completely")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
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
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("name"))), capfirst(force_text(_("due"))), capfirst(force_text(_("short")))
        )
      ]
    alt = False
    for prob in Problem.objects.using(db).filter(name__gte='short', entity='demand').order_by('startdate')[:limit]:
      result.append('<tr%s><td class="underline"><a href="%s/demandpegging/%s/">%s</a></td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', request.prefix, urlquote(prob.owner), escape(prob.owner), prob.startdate.date(), int(prob.weight)
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShortOrdersWidget)


class PurchaseQueueWidget(Widget):
  name = "purchase_queue"
  title = _("Purchase queue")
  tooltip = _("Display a list of new purchase orders")
  permissions = (("view_purchaseorder", "Can view purchase orders"),)
  asynchronous = True
  url = '/data/input/purchaseorder/?status=proposed&sidx=startdate&sord=asc'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("item"))), capfirst(force_text(_("supplier"))),
        capfirst(force_text(_("enddate"))), capfirst(force_text(_("quantity"))),
        capfirst(force_text(_("criticality")))
        )
      ]
    alt = False
    for po in PurchaseOrder.objects.using(db).filter(status='proposed').order_by('startdate')[:limit]:
      result.append('<tr%s><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', escape(po.item.name), escape(po.supplier.name), po.enddate.date(), int(po.quantity), int(po.criticality)
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchaseQueueWidget)


class ShippingQueueWidget(Widget):
  name = "shipping_queue"
  title = _("Shipping queue")
  tooltip = _("Display a list of new distribution orders")
  permissions = (("view_distributionorder", "Can view distribution orders"),)
  asynchronous = True
  url = '/data/input/distributionorder/?sidx=plandate&sord=asc'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("item"))), capfirst(force_text(_("origin"))),
        capfirst(force_text(_("destination"))), capfirst(force_text(_("quantity"))),
        capfirst(force_text(_("start date"))), capfirst(force_text(_("criticality")))
        )
      ]
    alt = False
    for do in DistributionOrder.objects.using(db).filter(status='proposed').order_by('startdate')[:limit]:
      result.append('<tr%s><td>%s</td><td>%s</td><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', escape(do.item), escape(do.origin.name), escape(do.destination),
        int(do.quantity), do.startdate.date(), int(do.criticality)
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShippingQueueWidget)


class ResourceQueueWidget(Widget):
  name = "resource_queue"
  title = _("Resource queue")
  tooltip = _("Display planned activities for the resources")
  permissions = (("view_resource_report", "Can view resource report"),)
  asynchronous = True
  url = '/loadplan/?sidx=startdate&sord=asc'
  exporturl = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("resource"))), capfirst(force_text(_("operation"))),
        capfirst(force_text(_("startdate"))), capfirst(force_text(_("enddate"))),
        capfirst(force_text(_("quantity"))), capfirst(force_text(_("criticality")))
        )
      ]
    alt = False
    for ldplan in LoadPlan.objects.using(db).select_related().order_by('startdate')[:limit]:
      result.append('<tr%s><td class="underline"><a href="%s/loadplan/?theresource=%s&sidx=startdate&sord=asc">%s</a></td><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', request.prefix, urlquote(ldplan.theresource), escape(ldplan.theresource), escape(ldplan.operationplan.operation), ldplan.startdate, ldplan.enddate, int(ldplan.operationplan.quantity), int(ldplan.operationplan.criticality)
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceQueueWidget)


class PurchaseAnalysisWidget(Widget):
  name = "purchase_order_analysis"
  title = _("Purchase order analysis")
  tooltip = _("Analyse the urgency of existing purchase orders")
  permissions = (("view_purchaseorder", "Can view purchase orders"),)
  asynchronous = True
  url = '/data/input/purchaseorder/?status=confirmed&sidx=criticality&sord=asc'
  limit = 20

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("item"))), capfirst(force_text(_("supplier"))),
        capfirst(force_text(_("enddate"))), capfirst(force_text(_("quantity"))),
        capfirst(force_text(_("criticality")))
        )
      ]
    alt = False
    for po in PurchaseOrder.objects.using(db).filter(status='confirmed').order_by('criticality')[:limit]:
      result.append('<tr%s><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', escape(po.item.name), escape(po.supplier.name), po.enddate.date(), int(po.quantity), int(po.criticality)
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchaseAnalysisWidget)


class AlertsWidget(Widget):
  name = "alerts"
  title = _("Alerts")
  tooltip = _("Overview of all alerts in the plan")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/problem/'

  @classmethod
  def render(cls, request=None):
    result = [
      '<table style="width:100%">',
      '<tr><th class="alignleft">%s</th><th>%s</th><th>%s</th></tr>' % (
        capfirst(force_text(_("resource"))), capfirst(force_text(_("count"))),
        capfirst(force_text(_("weight")))
        )
      ]
    cursor = connections[request.database].cursor()
    query = '''select name, count(*), sum(weight)
      from out_problem
      group by name
      order by name
      '''
    cursor.execute(query)
    alt = False
    for res in cursor.fetchall():
      result.append('<tr%s><td class="underline"><a href="%s/problem/?name=%s">%s</a></td><td class="aligncenter">%d</td><td class="aligncenter">%d</td></tr>' % (
        alt and ' class="altRow"' or '', request.prefix, urlquote(res[0]), res[0], res[1], res[2]
        ))
      alt = not alt
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(AlertsWidget)


class ResourceLoadWidget(Widget):
  name = "resource_utilization"
  title = _("Resource utilization")
  tooltip = _("Shows the resources with the highest utilization")
  permissions = (("view_resource_report", "Can view resource report"),)
  asynchronous = True
  url = '/resource/'
  exporturl = True
  limit = 5
  high = 90
  medium = 80

  def args(self):
    return "?%s" % urlencode({'limit': self.limit, 'medium': self.medium, 'high': self.high})

  javascript = '''
    // Collect the data
    var data = [];
    var max_util = 100.0;
    $("#resLoad").next().find("tr").each(function() {
      var l = $(this).find("a");
      var v = parseFloat($(this).find("td.util").html());
      data.push( [l.attr("href"), l.text(), v] );
      if (v > max_util) max_util = v;
      });
    var barHeight = $("#resLoad").height() / data.length;
    var x = d3.scale.linear().domain([0, max_util]).range([0, $("#resLoad").width()]);
    var resload_high = parseFloat($("#resload_high").html());
    var resload_medium = parseFloat($("#resload_medium").html());

    // Draw the chart
    var bar = d3.select("#resLoad")
     .selectAll("g")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(0," + i * barHeight + ")"; })
     .append("svg:a")
     .attr("xlink:href", function(d) {return d[0];});

    bar.append("rect")
      .attr("width", function(d) {return x(d[2]);})
      .attr("rx","3")
      .attr("height", barHeight - 2)
      .style("fill", function(d) {
        if (d[2] > resload_high) return "#DC3912";
        if (d[2] > resload_medium) return "#FF9900";
        return "#109618";
        });

    bar.append("text")
      .attr("x", "2")
      .attr("y", barHeight / 2)
      .attr("dy", ".35em")
      .text(function(d,i) { return d[1]; })
      .style('text-decoration', 'underline')
      .append("tspan")
      .attr("dx", ".35em")
      .text(function(d,i) { return d[2] + "%"; })
      .attr("class","bold");
    '''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    medium = int(request.GET.get('medium', cls.medium))
    high = int(request.GET.get('high', cls.high))
    result = [
      '<svg class="chart" id="resLoad" style="width:100%%; height: %spx;"></svg>' % (limit * 25 + 30),
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
      if limit < 0:
        break
      result.append('<tr><td><a href="%s/resource/%s/">%s</a></td><td class="util">%.2f</td></tr>' % (
        request.prefix, urlquote(res[0]), res[0], res[1]
        ))
    result.append('</table>')
    result.append('<span id="resload_medium" style="display:none">%s</span>' % medium)
    result.append('<span id="resload_high" style="display:none">%s</span>' % high)
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceLoadWidget)


class InventoryByLocationWidget(Widget):
  name = "inventory_by_location"
  title = _("Inventory by location")
  tooltip = _("Display the locations with the highest inventory value")
  asynchronous = True
  limit = 5

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  javascript = '''
    var margin = 50;  // Space allocated for the Y-axis

    // Collect the data
    var invmax = 0;
    var data = [];
    $("#invByLoc").next().find("tr").each(function() {
      var l = parseFloat($(this).find("td:eq(1)").html());
      data.push( [
         $(this).find("td").html(),
         l
         ] );
      if (l > invmax) invmax = l;
      });
    var x_width = ($("#invByLoc").width()-margin) / data.length;
    var y = d3.scale.linear().domain([0, invmax]).range([$("#invByLoc").height() - 20, 0]);
    var y_zero = y(0);

    // Draw the chart
    var bar = d3.select("#invByLoc")
     .selectAll("g")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + (i * x_width + margin) + ",0)"; });

    bar.append("rect")
      .attr("y", function(d) {return y(d[1]) + 10;})
      .attr("height", function(d) {return y_zero - y(d[1]);})
      .attr("rx","3")
      .attr("width", x_width - 2)
      .style("fill", "#828915");

    bar.append("text")
      .attr("y", y_zero - 3)
      .text(function(d,i) { return d[0]; })
      .style("text-anchor", "end")
      .attr("transform","rotate(90 " + (x_width/2 - 5) + "," + y_zero + ")");

    // Draw the Y-axis
    var yAxis = d3.svg.axis()
      .scale(y)
      .ticks(4)
      .orient("left");
    d3.select("#invByLoc")
      .append("g")
      .attr("transform", "translate(" + margin + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);
    '''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    result = [
      '<svg class="chart" id="invByLoc" style="width:100%; height: 250px;"></svg>',
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
      if limit < 0:
        break
      result.append('<tr><td>%s</td><td>%.2f</td></tr>' % (
        res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(InventoryByLocationWidget)


class InventoryByItemWidget(Widget):
  name = "inventory_by_item"
  title = _("Inventory by item")
  tooltip = _("Display the items with the highest inventory value")
  asynchronous = True
  limit = 20

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  javascript = '''
    var margin = 50;  // Space allocated for the Y-axis

    // Collect the data
    var invmax = 0;
    var data = [];
    $("#invByItem").next().find("tr").each(function() {
      var l = parseFloat($(this).find("td:eq(1)").html());
      data.push( [
         $(this).find("td").html(),
         l
         ] );
      if (l > invmax) invmax = l;
      });
    var x_width = ($("#invByItem").width()-margin) / data.length;
    var y = d3.scale.linear().domain([0, invmax]).range([$("#invByItem").height() - 20, 0]);
    var y_zero = y(0);

    // Draw the chart
    var bar = d3.select("#invByItem")
     .selectAll("g")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + (i * x_width + margin) + ",0)"; });

    bar.append("rect")
      .attr("y", function(d) {return y(d[1]) + 10;})
      .attr("height", function(d) {return y_zero - y(d[1]);})
      .attr("rx","3")
      .attr("width", x_width - 2)
      .style("fill", "#D31A00");

    bar.append("text")
      .attr("y", y_zero - 3)
      .text(function(d,i) { return d[0]; })
      .style("text-anchor", "end")
      .attr("transform","rotate(90 " + (x_width/2 - 5) + "," + y_zero + ")");

    // Draw the Y-axis
    var yAxis = d3.svg.axis()
      .scale(y)
      .ticks(4)
      .orient("left");
    d3.select("#invByItem")
      .append("g")
      .attr("transform", "translate(" + margin + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);
    '''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    result = [
      '<svg class="chart" id="invByItem" style="width:100%; height: 250px;"></svg>',
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
      if limit < 0:
        break
      result.append('<tr><td>%s</td><td>%.2f</td></tr>' % (
        res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(InventoryByItemWidget)


class DeliveryPerformanceWidget(Widget):
  name = "delivery_performance"
  title = _("Delivery performance")
  tooltip = _("Shows the percentage of demands that are planned to be shipped completely on time")
  asynchronous = True
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
      '<span id="otd_label" style="display:none">%s</span>' % force_text(_("On time delivery")),
      '<span id="otd_value" style="display:none">%s</span>' % val,
      '<span id="otd_green" style="display:none">%s</span>' % green,
      '<span id="otd_yellow" style="display:none">%s</span>' % yellow
      ]
    return HttpResponse('\n'.join(result))

Dashboard.register(DeliveryPerformanceWidget)
