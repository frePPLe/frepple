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

from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.admin.utils import quote
from django.db import DEFAULT_DB_ALIAS, connections
from django.http import HttpResponse
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from freppledb.common.middleware import _thread_locals
from freppledb.common.models import Parameter
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.report import GridReport, getCurrency
from freppledb.input.models import PurchaseOrder, DistributionOrder, OperationPlanResource


class LateOrdersWidget(Widget):
  name = "late_orders"
  title = _("late orders")
  tooltip = _("Shows orders that will be delivered after their due date")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/problem/?entity=demand&name=late&sord=asc&sidx=startdate'
  exporturl = True
  limit = 20

  query = '''
    select
      demand.name, demand.item_id, demand.location_id, demand.customer_id,
      out_problem.startdate, out_problem.enddate, out_problem.weight
    from out_problem
    inner join demand
      on out_problem.owner = demand.name
    where out_problem.name = 'late' and out_problem.entity = 'demand'
    order by out_problem.startdate, out_problem.weight desc
    limit %s
    '''

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    cursor = connections[db].cursor()
    result = [
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th class="alignleft">%s</th>'
      '<th class="alignleft">%s</th><th class="alignleft">%s</th>'
      '<th class="aligncenter">%s</th><th class="aligncenter">%s</th>'
      '<th class="aligncenter">%s</th></tr></thead>' % (
        capfirst(force_text(_("name"))), capfirst(force_text(_("item"))),
        capfirst(force_text(_("location"))), capfirst(force_text(_("customer"))),
        capfirst(force_text(_("due"))), capfirst(force_text(_("planned date"))),
        capfirst(force_text(_("delay")))
        )
      ]
    alt = False
    cursor.execute(cls.query, (limit,))
    for rec in cursor.fetchall():
      result.append(
        '<tr%s><td class="underline"><a href="%s/demandpegging/%s/">%s</a></td>'
        '<td class="alignleft">%s</td><td class="alignleft">%s</td>'
        '<td class="alignleft">%s</td><td class="alignleft">%s</td>'
        '<td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
          alt and ' class="altRow"' or '', request.prefix, quote(rec[0]),
          escape(rec[0]), escape(rec[1]), escape(rec[2]), escape(rec[3]),
          rec[4].date(), rec[5].date(), int(rec[6])
        ))
      alt = not alt
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(LateOrdersWidget)


class ShortOrdersWidget(Widget):
  name = "short_orders"
  title = _("short orders")
  tooltip = _("Shows orders that are not planned completely")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  # Note the gte filter lets pass "short" and "unplanned", and filters out
  # "late" and "early".
  url = '/problem/?entity=demand&name__gte=short&sord=asc&sidx=startdate'
  exporturl = True
  limit = 20

  query = '''
    select
      out_problem.owner, demand.item_id, demand.location_id, demand.customer_id,
      out_problem.startdate, out_problem.weight
    from out_problem
    left outer join demand
      on out_problem.owner = demand.name
    where out_problem.name in ('short', 'unplanned') and out_problem.entity = 'demand'
      and demand.name is not null
    order by out_problem.startdate desc
    limit %s
    '''

  def args(self):
    return "?%s" % urlencode({'limit': self.limit})

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    cursor = connections[db].cursor()
    result = [
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th class="alignleft">%s</th><th class="alignleft">%s</th>'
      '<th class="alignleft">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
        capfirst(force_text(_("name"))), capfirst(force_text(_("item"))), capfirst(force_text(_("location"))),
        capfirst(force_text(_("customer"))), capfirst(force_text(_("due"))), capfirst(force_text(_("short")))
        )
      ]
    alt = False
    cursor.execute(cls.query, (limit,))
    for rec in cursor.fetchall():
      result.append(
        '<tr%s><td class="underline alignleft"><a href="%s/demandpegging/%s/">%s</a></td><td class="alignleft">%s</td>'
        '<td class="alignleft">%s</td><td class="alignleft">%s</td><td class="aligncenter">%s</td>'
        '<td class="aligncenter">%s</td></tr>' % (
          alt and ' class="altRow"' or '', request.prefix, quote(rec[0]), escape(rec[0]),
          escape(rec[1]), escape(rec[2]), escape(rec[3]), rec[4].date(), int(rec[5])
        ))
      alt = not alt
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShortOrdersWidget)


class ManufacturingOrderWidget(Widget):
  name = "manufacturing_orders"
  title = _("manufacturing orders")
  tooltip = _("Shows manufacturing orders by start date")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/data/input/manufacturingorder/?sord=asc&sidx=startdate&status__in=proposed,confirmed'
  exporturl = True
  fence1 = 7
  fence2 = 30

  def args(self):
    return "?%s" % urlencode({'fence1': self.fence1, 'fence2': self.fence2})

  javascript = '''
    var margin_y = 70;  // Width allocated for the Y-axis
    var margin_x = 60;  // Height allocated for the X-axis
    var svg = d3.select("#mo_chart");
    var svgrectangle = document.getElementById("mo_chart").getBoundingClientRect();

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_value = 0.0;
    var max_units = 0.0;
    var max_count = 0.0;
    var nth = Math.ceil($("#mo_overview").find("tr").length / (svgrectangle['width'] - margin_y) * 30);
    var myticks = [];
    $("#mo_overview").find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      var count = name.next();
      var units = count.next();
      var value = units.next();
      var el = [name.text(), parseFloat(count.text()), parseFloat(units.text()), parseFloat(value.text())];
      data.push(el);
      domain_x.push(el[0]);
      if (el[1] > max_count) max_count = el[1];
      if (el[2] > max_units) max_units = el[2];
      if (el[3] > max_value) max_value = el[3];
      if (idx %% nth == 0) myticks.push(name.text());
      });

    // Define axis domains
    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);
    var y_value = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([0, max_value + 5]);
    var y_count = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([0, max_count + 5]);

    // Draw x-axis
    var xAxis = d3.svg.axis().scale(x).tickValues(myticks).orient("bottom");
    svg.append("g")
      .attr("id","xAxisMO")
      .attr("transform", "translate(" + margin_y  + ", " + (svgrectangle['height'] - margin_x) +" )")
      .attr("class", "x axis")
      .call(xAxis)
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.75em")
      .attr("dy", "-.25em")
      .attr("transform", "rotate(-90)" );

    // Draw y-axis
    var yAxis = d3.svg.axis().scale(y_value)
        .orient("left")
        .ticks(5)
        .tickFormat(d3.format("s"));
    svg.append("g")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);

    // get position of the first tick in the graph
    var tickposition = 0;
    if (typeof $("#xAxisMO").children()[0].attributes !== 'undefined') {
      tickposition = parseInt($("#xAxisMO").children()[0].attributes.transform.value.slice(10));
    }

    // Draw invisible rectangles for the hoverings
    svg.selectAll("g>rect")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + Math.ceil(tickposition + i*x.rangeBand() - x.rangeBand()/2 + margin_y) + ",10)"; })
     .append("rect")
      .attr("height", svgrectangle['height'] - 10 - margin_x)
      .attr("width", x.rangeBand())
      .attr("fill-opacity", 0)
      .on("mouseover", function(d) {
        graph.showTooltip(d[0] + '<br><span style="color: #FFC000;">'+ d[1] + "</span> / " + d[2] + ' %s / ' + currency[0] + ' <span style="color: #8BBA00;">' + d[3] + currency[1] + "</span>");
        $("#tooltip").css('background-color','black').css('color','white');
        })
      .on("mousemove", graph.moveTooltip)
      .on("mouseout", graph.hideTooltip);

    // Draw the lines
    var line_value = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y_value(d[3]); });
    var line_count = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y_count(d[1]); });

    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#8BBA00")
      .attr("d", line_value(data));
    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#FFC000")
      .attr("d", line_count(data));
    ''' % force_text(_("units"))

  @classmethod
  def render(cls, request=None):
    fence1 = int(request.GET.get('fence1', cls.fence1))
    fence2 = int(request.GET.get('fence2', cls.fence2))
    currency = getCurrency()
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    try:
      current = datetime.strptime(
        Parameter.objects.using(db).get(name="currentdate").value,
        "%Y-%m-%d %H:%M:%S"
        )
    except:
      current = datetime.now()
      current = current.replace(microsecond=0)
    request.database = db
    GridReport.getBuckets(request)
    cursor = connections[db].cursor()
    query = '''
      select
         0, common_bucketdetail.name, common_bucketdetail.startdate,
         count(operationplan.name), coalesce(round(sum(quantity)),0),
         coalesce(round(sum(quantity * cost)),0)
      from common_bucketdetail
      left outer join operationplan
        on operationplan.startdate >= common_bucketdetail.startdate
        and operationplan.startdate < common_bucketdetail.enddate
        and status in ('confirmed', 'proposed')
        and operationplan.type = 'MO'
      left outer join operation
        on operationplan.operation_id = operation.name
      where bucket_id = %%s and common_bucketdetail.enddate > %%s
        and common_bucketdetail.startdate < %%s
      group by common_bucketdetail.name, common_bucketdetail.startdate
      union all
      select
        1, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(quantity * cost)),0)
      from operationplan
      inner join operation
        on operationplan.operation_id = operation.name
      where status = 'confirmed'
        and operationplan.type = 'MO'
      union all
      select
        2, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(quantity * cost)),0)
      from operationplan
      inner join operation
        on operationplan.operation_id = operation.name
      where status = 'proposed'
        and startdate < %%s + interval '%s day'
        and operationplan.type = 'MO'
      union all
      select
        3, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(quantity * cost)),0)
      from operationplan
      inner join operation
        on operationplan.operation_id = operation.name
      where status = 'proposed'
        and startdate < %%s + interval '%s day'
        and operationplan.type = 'MO'
      order by 1, 3
      ''' % (fence1, fence2)
    cursor.execute(query, (request.report_bucket, request.report_startdate, request.report_enddate, current, current))
    result = [
      '<svg class="chart" id="mo_chart" style="width:100%; height: 150px;"></svg>',
      '<table id="mo_overview" style="display: none">',
      ]
    for rec in cursor.fetchall():
      if rec[0] == 0:
        result.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (rec[1], rec[3], rec[4], rec[5]))
      elif rec[0] == 1:
        result.append('</table><div class="row"><div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/manufacturingorder/?sord=asc&sidx=startdate&amp;status=confirmed" role="button" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix,
          force_text(_("Review")),
          force_text(_("confirmed orders"))
          ))
      elif rec[0] == 2 and fence1:
        limit_fence1 = current + timedelta(days=fence1)
        result.append('<div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/manufacturingorder/?sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" role="button" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix, limit_fence1.strftime("%Y-%m-%d"),
          force_text(_("Review")),
          force_text(_("proposed orders within %(fence)s days") % {'fence': fence1})
          ))
      elif fence2:
        limit_fence2 = current + timedelta(days=fence2)
        result.append('<div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/manufacturingorder/?sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" rol="button" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix, limit_fence2.strftime("%Y-%m-%d"),
          force_text(_("Review")),
          force_text(_("proposed orders within %(fence)s days") % {'fence': fence2})
          ))
    result.append('</div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ManufacturingOrderWidget)


class DistributionOrderWidget(Widget):
  name = "distribution_orders"
  title = _("distribution orders")
  tooltip = _("Shows distribution orders by start date")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/data/input/distributionorder/?sord=asc&sidx=startdate&status__in=proposed,confirmed'
  exporturl = True
  fence1 = 7
  fence2 = 30

  def args(self):
    return "?%s" % urlencode({'fence1': self.fence1, 'fence2': self.fence2})

  javascript = '''
    var margin_y = 70;  // Width allocated for the Y-axis
    var margin_x = 60;  // Height allocated for the X-axis
    var svg = d3.select("#do_chart");
    var svgrectangle = document.getElementById("do_chart").getBoundingClientRect();

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_value = 0.0;
    var max_units = 0.0;
    var max_count = 0.0;
    var nth = Math.ceil($("#do_overview").find("tr").length / (svgrectangle['width'] - margin_y) * 30);
    var myticks = [];
    $("#do_overview").find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      var count = name.next();
      var units = count.next();
      var value = units.next()
      var el = [name.text(), parseFloat(count.text()), parseFloat(units.text()), parseFloat(value.text())];
      data.push(el);
      domain_x.push(el[0]);
      if (el[1] > max_count) max_count = el[1];
      if (el[2] > max_units) max_units = el[2];
      if (el[3] > max_value) max_value = el[3];
      if (idx %% nth == 0) myticks.push(name.text());
      });

    // Define axis domains
    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);
    var y_value = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([0, max_value + 5]);
    var y_count = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([0, max_count + 5]);

    // Draw x-axis
    var xAxis = d3.svg.axis().scale(x).tickValues(myticks).orient("bottom");
    svg.append("g")
      .attr("id","xAxisDO")
      .attr("transform", "translate(" + margin_y  + ", " + (svgrectangle['height'] - margin_x) +" )")
      .attr("class", "x axis")
      .call(xAxis)
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.75em")
      .attr("dy", "-.25em")
      .attr("transform", "rotate(-90)" );

    // Draw y-axis
    var yAxis = d3.svg.axis().scale(y_value)
        .orient("left")
        .ticks(5)
        .tickFormat(d3.format("s"));
    svg.append("g")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);

    // get position of the first tick in the graph
    var tickposition = 0;
    if (typeof $("#xAxisDO").children()[0].attributes !== 'undefined') {
      tickposition = parseInt($("#xAxisDO").children()[0].attributes.transform.value.slice(10));
    }

    // Draw invisible rectangles for the hoverings
    svg.selectAll("g>rect")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + Math.ceil(tickposition + i*x.rangeBand() - x.rangeBand()/2 + margin_y) + ",10)"; })
     .append("rect")
      .attr("height", svgrectangle['height'] - 10 - margin_x)
      .attr("width", x.rangeBand())
      .attr("fill-opacity", 0)
      .on("mouseover", function(d) {
        graph.showTooltip(d[0] + '<br><span style="color: #FFC000;">'+ d[1] + "</span> / " + d[2] + ' %s / '+currency[0]+' <span style="color: #8BBA00;">' + d[3] + currency[1] + "</span>");
        $("#tooltip").css('background-color','black').css('color','white');
        })
      .on("mousemove", graph.moveTooltip)
      .on("mouseout", graph.hideTooltip);

    // Draw the lines
    var line_value = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y_value(d[3]); });
    var line_count = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y_count(d[1]); });

    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#8BBA00")
      .attr("d", line_value(data));
    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#FFC000")
      .attr("d", line_count(data));
    ''' % force_text(_("units"))

  @classmethod
  def render(cls, request=None):
    fence1 = int(request.GET.get('fence1', cls.fence1))
    fence2 = int(request.GET.get('fence2', cls.fence2))
    currency = getCurrency()
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    try:
      current = datetime.strptime(
        Parameter.objects.using(db).get(name="currentdate").value,
        "%Y-%m-%d %H:%M:%S"
        )
    except:
      current = datetime.now()
      current = current.replace(microsecond=0)
    request.database = db
    GridReport.getBuckets(request)
    cursor = connections[db].cursor()
    query = '''
      select
         0, common_bucketdetail.name, common_bucketdetail.startdate,
         count(operationplan.name), coalesce(round(sum(quantity)),0),
         coalesce(round(sum(item.cost * quantity)),0)
      from common_bucketdetail
      left outer join operationplan
        on operationplan.startdate >= common_bucketdetail.startdate
        and operationplan.startdate < common_bucketdetail.enddate
      left outer join item
        on operationplan.item_id = item.name
        and status in ('confirmed', 'proposed')
        and type = 'DO'
      where bucket_id = %%s and common_bucketdetail.enddate > %%s
        and common_bucketdetail.startdate < %%s
      group by common_bucketdetail.name, common_bucketdetail.startdate
      union all
      select
        1, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(item.cost * quantity)),0)
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      where status = 'confirmed' and type = 'DO'
      union all
      select
        2, null, null, count(*),
        coalesce(round(sum(item.cost)),0),
        coalesce(round(sum(item.cost * quantity)),0)
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      where status = 'proposed' and startdate < %%s + interval '%s day'
      and type = 'DO'
      union all
      select
        3, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(item.cost * quantity)),0)
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      where status = 'proposed' and startdate < %%s + interval '%s day'
      and type = 'DO'
      order by 1, 3
      ''' % (fence1, fence2)
    cursor.execute(query, (request.report_bucket, request.report_startdate, request.report_enddate, current, current))
    result = [
      '<svg class="chart" id="do_chart" style="width:100%; height: 150px;"></svg>',
      '<table id="do_overview" style="display: none">',
      ]
    for rec in cursor.fetchall():
      if rec[0] == 0:
        result.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (rec[1], rec[3], rec[4], rec[5]))
      elif rec[0] == 1:
        result.append('</table><div class="row"><div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/distributionorder/?sord=asc&sidx=startdate&amp;status=confirmed" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1], request.prefix,
          force_text(_("Review")),
          force_text(_("confirmed orders"))
          ))
      elif rec[0] == 2 and fence1:
        limit_fence1 = current + timedelta(days=fence1)
        result.append('<div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/distributionorder/?sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix, limit_fence1.strftime("%Y-%m-%d"),
          force_text(_("Review")),
          force_text(_("proposed orders within %(fence)s days") % {'fence': fence1})
          ))
      elif fence2:
        limit_fence2 = current + timedelta(days=fence2)
        result.append('<div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href=%s/data/input/distributionorder/?sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix, limit_fence2.strftime("%Y-%m-%d"),
          force_text(_("Review")),
          force_text(_("proposed orders within %(fence)s days") % {'fence': fence2})
          ))
    result.append('</div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(DistributionOrderWidget)


class PurchaseOrderWidget(Widget):
  name = "purchase_orders"
  title = _("purchase orders")
  tooltip = _("Shows purchase orders by ordering date")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/data/input/purchaseorder/?sord=asc&sidx=startdate&status__in=proposed,confirmed'
  exporturl = True
  fence1 = 7
  fence2 = 30
  supplier = None

  def args(self):
    if self.supplier:
      return "?%s" % urlencode({'fence1': self.fence1, 'fence2': self.fence2, 'supplier': self.supplier})
    else:
      return "?%s" % urlencode({'fence1': self.fence1, 'fence2': self.fence2})

  javascript = '''
    var margin_y = 70;  // Width allocated for the Y-axis
    var margin_x = 60;  // Height allocated for the X-axis
    var svg = d3.select("#po_chart");
    var svgrectangle = document.getElementById("po_chart").getBoundingClientRect();

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_value = 0.0;
    var max_units = 0.0;
    var max_count = 0.0;
    var nth = Math.ceil($("#po_overview").find("tr").length / (svgrectangle['width'] - margin_y) * 30);
    var myticks = [];
    $("#po_overview").find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      var count = name.next();
      var units = count.next()
      var value = units.next()
      var el = [name.text(), parseFloat(count.text()), parseFloat(units.text()), parseFloat(value.text())];
      data.push(el);
      domain_x.push(el[0]);
      if (el[1] > max_count) max_count = el[1];
      if (el[2] > max_units) max_units = el[2];
      if (el[3] > max_value) max_value = el[3];
      if (idx %% nth == 0) myticks.push(name.text());
      });

    // Define axis domains
    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);
    var y_value = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([0, max_value + 5]);
    var y_count = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([0, max_count + 5]);

    // Draw x-axis
    var xAxis = d3.svg.axis().scale(x).tickValues(myticks).orient("bottom");
    svg.append("g")
      .attr("id","xAxisPO")
      .attr("transform", "translate(" + margin_y  + ", " + (svgrectangle['height'] - margin_x) +" )")
      .attr("class", "x axis")
      .call(xAxis)
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.75em")
      .attr("dy", "-.25em")
      .attr("transform", "rotate(-90)" );

    // Draw y-axis
    var yAxis = d3.svg.axis().scale(y_value)
        .orient("left")
        .ticks(5)
        .tickFormat(d3.format("s"));
    svg.append("g")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);

    // get position of the first tick in the graph
    var tickposition = 0;
    var thistarget = $("#xAxisPO").children()[0].attributes;
    if (typeof thistarget !== 'undefined') {
      if (typeof thistarget.transform !== 'undefined'){
        tickposition = parseInt(thistarget.transform.value.slice(10));
      }
    }

    // Draw invisible rectangles for the hoverings
    svg.selectAll("g>rect")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + Math.ceil(tickposition + i*x.rangeBand() - x.rangeBand()/2 + margin_y) + ",10)"; })
     .append("rect")
      .attr("height", svgrectangle['height'] - 10 - margin_x)
      .attr("width", x.rangeBand())
      .attr("fill-opacity", 0)
      .on("mouseover", function(d) {
        graph.showTooltip(d[0] + '<br><span style="color: #FFC000;">'+ d[1] + "</span> / " + d[2] + ' %s / ' + currency[0] + ' <span style="color: #8BBA00;">' + d[3] + currency[1] + "</span>");
        $("#tooltip").css('background-color','black').css('color','white');
        })
      .on("mousemove", graph.moveTooltip)
      .on("mouseout", graph.hideTooltip);

    // Draw the lines
    var line_value = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y_value(d[3]); });
    var line_count = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y_count(d[1]); });

    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#8BBA00")
      .attr("d", line_value(data));
    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#FFC000")
      .attr("d", line_count(data));
    ''' % force_text(_("units"))

  @classmethod
  def render(cls, request=None):
    fence1 = int(request.GET.get('fence1', cls.fence1))
    fence2 = int(request.GET.get('fence2', cls.fence2))
    supplier = request.GET.get('supplier', cls.supplier)
    currency = getCurrency()
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    try:
      current = datetime.strptime(
        Parameter.objects.using(db).get(name="currentdate").value,
        "%Y-%m-%d %H:%M:%S"
        )
    except:
      current = datetime.now()
      current = current.replace(microsecond=0)
    request.database = db
    GridReport.getBuckets(request)
    supplierfilter = 'and supplier_id = %s' if supplier else ''
    cursor = connections[db].cursor()
    query = '''
      select
         0, common_bucketdetail.name, common_bucketdetail.startdate,
         count(operationplan.name), coalesce(round(sum(quantity)),0),
         coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0)
      from common_bucketdetail
      left outer join operationplan
        on operationplan.startdate >= common_bucketdetail.startdate
        and operationplan.startdate < common_bucketdetail.enddate
        and status in ('confirmed', 'proposed') %s
      left outer join item
        on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where bucket_id = %%s and common_bucketdetail.enddate > %%s
        and common_bucketdetail.startdate < %%s
      group by common_bucketdetail.name, common_bucketdetail.startdate
      union all
      select
        1, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0)
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status = 'confirmed' %s and type = 'PO'
      union all
      select
        2, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0)
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status = 'proposed' and type = 'PO' and startdate < %%s + interval '%s day' %s
      union all
      select
        3, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0)
      from operationplan
      inner join item
        on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status = 'proposed' and type = 'PO' and startdate < %%s + interval '%s day' %s
      order by 1, 3
      ''' % (
        supplierfilter, supplierfilter, fence1, supplierfilter, fence2, supplierfilter
        )
    if supplier:
      cursor.execute(query, (request.report_bucket, request.report_startdate, request.report_enddate, supplier, supplier, current, supplier, current, supplier))
    else:
      cursor.execute(query, (request.report_bucket, request.report_startdate, request.report_enddate, current, current))
    result = [
      '<svg class="chart" id="po_chart" style="width:100%; height: 150px;"></svg>',
      '<table id="po_overview" style="display: none">',
      ]
    for rec in cursor.fetchall():
      if rec[0] == 0:
        result.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (rec[1], rec[3], rec[4], rec[5]))
      elif rec[0] == 1:
        result.append('</table><div class="row"><div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?sord=asc&sidx=startdate&amp;status=confirmed" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5],
          currency[1], request.prefix,
          force_text(_("Review")),
          force_text(_("confirmed orders"))
          ))
      elif rec[0] == 2 and fence1:
        limit_fence1 = current + timedelta(days=fence1)
        result.append('<div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix, limit_fence1.strftime("%Y-%m-%d"),
          force_text(_("Review")),
          force_text(_("proposed orders within %(fence)s days") % {'fence': fence1})
          ))
      elif fence2:
        limit_fence2 = current + timedelta(days=fence2)
        result.append('<div class="col-xs-4"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-success btn-xs">%s</a></h2><small>%s</small></div>' % (
          rec[3], rec[4], force_text(_("units")),
          currency[0], rec[5], currency[1],
          request.prefix, limit_fence2.strftime("%Y-%m-%d"),
          force_text(_("Review")),
          force_text(_("proposed orders within %(fence)s days") % {'fence': fence2})
          ))
    result.append('</div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchaseOrderWidget)


class PurchaseQueueWidget(Widget):
  name = "purchase_queue"
  title = _("purchase queue")
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
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
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
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchaseQueueWidget)


class DistributionQueueWidget(Widget):
  name = "distribution_queue"
  title = _("distribution queue")
  tooltip = _("Display a list of new distribution orders")
  permissions = (("view_distributionorder", "Can view distribution orders"),)
  asynchronous = True
  url = '/data/input/distributionorder/?status=proposed&sidx=startdate&sord=asc'
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
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
        capfirst(force_text(_("item"))), capfirst(force_text(_("origin"))),
        capfirst(force_text(_("destination"))), capfirst(force_text(_("enddate"))),
        capfirst(force_text(_("quantity"))), capfirst(force_text(_("criticality")))
        )
      ]
    alt = False
    for po in DistributionOrder.objects.using(db).filter(status='proposed').order_by('startdate')[:limit]:
      result.append('<tr%s><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', escape(po.item.name), escape(po.origin.name if po.origin else ''), escape(po.destination.name), po.enddate.date(), int(po.quantity), int(po.criticality)
        ))
      alt = not alt
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(DistributionQueueWidget)


class ShippingQueueWidget(Widget):
  name = "shipping_queue"
  title = _("shipping queue")
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
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
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
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ShippingQueueWidget)


class ResourceQueueWidget(Widget):
  name = "resource_queue"
  title = _("resource queue")
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
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr>'
      '<th class="alignleft">%s</th>'
      '<th>%s</th><th class="aligncenter">%s</th>'
      '<th class="aligncenter">%s</th>'
      '<th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
        capfirst(force_text(_("resource"))), capfirst(force_text(_("operation"))),
        capfirst(force_text(_("startdate"))), capfirst(force_text(_("enddate"))),
        capfirst(force_text(_("quantity"))), capfirst(force_text(_("criticality")))
        )
      ]
    alt = False
    for ldplan in OperationPlanResource.objects.using(db).select_related().order_by('startdate')[:limit]:
      result.append('<tr%s><td class="underline"><a href="%s/loadplan/?resource=%s&sidx=startdate&sord=asc">%s</a></td><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td></tr>' % (
        alt and ' class="altRow"' or '', request.prefix, quote(ldplan.resource), escape(ldplan.resource), escape(ldplan.operationplan.operation), ldplan.startdate, ldplan.enddate, int(ldplan.operationplan.quantity), int(ldplan.operationplan.criticality)
        ))
      alt = not alt
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceQueueWidget)


class PurchaseAnalysisWidget(Widget):
  name = "purchase_order_analysis"
  title = _("purchase order analysis")
  tooltip = _("Analyse the urgency of existing purchase orders")
  permissions = (("view_purchaseorder", "Can view purchase orders"),)
  asynchronous = True
  url = '/data/input/purchaseorder/?status=confirmed&sidx=color&sord=asc'
  limit = 20

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
        capfirst(force_text(_("item"))), capfirst(force_text(_("supplier"))),
        capfirst(force_text(_("enddate"))), capfirst(force_text(_("quantity"))),
        capfirst(force_text(_("inventory status")))
        )
      ]
    alt = False
    for po in PurchaseOrder.objects.using(db).filter(status='confirmed').exclude(criticality=999).order_by('color','enddate')[:limit]:
      result.append('<tr%s><td>%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s</td><td class="aligncenter">%s%%</td></tr>' % (
        alt and ' class="altRow"' or '', escape(po.item.name if po.item else ''),
        escape(po.supplier.name if po.supplier else ''),
        po.enddate.date() if po.enddate else '',
        int(po.quantity) if po.quantity else '',
        int(po.color) if po.color is not None else ''
        ))
      alt = not alt
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(PurchaseAnalysisWidget)


class AlertsWidget(Widget):
  name = "alerts"
  title = _("alerts")
  tooltip = _("Overview of all alerts in the plan")
  permissions = (("view_problem_report", "Can view problem report"),)
  asynchronous = True
  url = '/problem/'
  entities = 'material,capacity,demand,operation'

  @classmethod
  def render(cls, request=None):
    entities = request.GET.get('entities', cls.entities).split(',')
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    result = [
      '<div class="table-responsive"><table class="table table-condensed table-hover">',
      '<thead><tr><th class="alignleft">%s</th><th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>' % (
        capfirst(force_text(_("type"))), capfirst(force_text(_("count"))),
        capfirst(force_text(_("weight")))
        )
      ]
    cursor = connections[db].cursor()
    query = '''select name, count(*), sum(weight)
      from out_problem
      where entity in (%s)
      group by name
      order by name
      ''' % (', '.join(['%s']*len(entities)))
    cursor.execute(query, entities)
    alt = False
    for res in cursor.fetchall():
      result.append('<tr%s><td class="underline"><a href="%s/problem/?name=%s">%s</a></td><td class="aligncenter">%d</td><td class="aligncenter">%d</td></tr>' % (
        alt and ' class="altRow"' or '', request.prefix, quote(res[0]), res[0], res[1], res[2]
        ))
      alt = not alt
    result.append('</table></div>')
    return HttpResponse('\n'.join(result))

Dashboard.register(AlertsWidget)


class DemandAlertsWidget(AlertsWidget):
  name = "demand_alerts"
  title = _("demand alerts")
  url = '/problem/?entity=demand'
  entities = 'demand'

Dashboard.register(DemandAlertsWidget)


class CapacityAlertsWidget(AlertsWidget):
  name = "capacity_alerts"
  title = _("capacity alerts")
  url = '/problem/?entity=capacity'
  entities = 'capacity'

Dashboard.register(CapacityAlertsWidget)


class MaterialAlertsWidget(AlertsWidget):
  name = "material_alerts"
  title = _("material alerts")
  url = '/problem/?entity=material'
  entities = 'material'

Dashboard.register(MaterialAlertsWidget)


class ResourceLoadWidget(Widget):
  name = "resource_utilization"
  title = _("resource utilization")
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
    var svgrectangle = document.getElementById("resLoad").getBoundingClientRect();
    var barHeight = svgrectangle['height'] / data.length;
    var x = d3.scale.linear().domain([0, max_util]).range([0, svgrectangle['width']]);
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
                  resource,
                  ( coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0) )
                   * 100.0 / coalesce(sum(out_resourceplan.available)+0.000001,1) as avg_util,
                  coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0),
                  coalesce(sum(out_resourceplan.free),0)
                from out_resourceplan
                where out_resourceplan.startdate >= %s
                  and out_resourceplan.startdate < %s
                group by resource
                order by 2 desc
                limit %s
              '''
    cursor.execute(query, (request.report_startdate, request.report_enddate, limit))
    for res in cursor.fetchall():
      result.append('<tr><td><a href="%s/resource/%s/">%s</a></td><td class="util">%.2f</td></tr>' % (
        request.prefix, quote(res[0]), res[0], res[1]
        ))
    result.append('</table>')
    result.append('<span id="resload_medium" style="display:none">%s</span>' % medium)
    result.append('<span id="resload_high" style="display:none">%s</span>' % high)
    return HttpResponse('\n'.join(result))

Dashboard.register(ResourceLoadWidget)


class InventoryByLocationWidget(Widget):
  name = "inventory_by_location"
  title = _("inventory by location")
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
    var svgrectangle = document.getElementById("invByLoc").getBoundingClientRect();
    var x_width = (svgrectangle['width']-margin) / data.length;
    var y = d3.scale.linear().domain([0, invmax]).range([svgrectangle['height'] - 20, 0]);
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

// Location label
    bar.append("text")
      .attr("y", y_zero)
      .attr("x", x_width/2)
      .text(function(d,i) { return d[0]; })
      .style("text-anchor", "end")
      .attr("transform","rotate(90 " + (x_width/2) + " " + y_zero + ")  ");


    // Draw the Y-axis
    var yAxis = d3.svg.axis()
      .scale(y)
      .ticks(4)
      .orient("left")
      .tickFormat(d3.format("s"));
    d3.select("#invByLoc")
      .append("g")
      .attr("transform", "translate(" + margin + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);
    '''

  query = '''select location_id, coalesce(sum(buffer.onhand * item.cost),0)
             from buffer
             inner join item on buffer.item_id = item.name
             group by location_id
             order by 2 desc
             limit %s'''

  @classmethod
  def render(cls, request=None):
    limit = int(request.GET.get('limit', cls.limit))
    result = [
      '<svg class="chart" id="invByLoc" style="width:100%; height: 250px;"></svg>',
      '<table style="display:none">'
      ]
    cursor = connections[request.database].cursor()
    cursor.execute(cls.query, (limit,))
    for res in cursor.fetchall():
      result.append('<tr><td>%s</td><td>%.2f</td></tr>' % (
        res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(InventoryByLocationWidget)


class InventoryByItemWidget(Widget):
  name = "inventory_by_item"
  title = _("inventory by item")
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
    var svgrectangle = document.getElementById("invByItem").getBoundingClientRect();
    var x_width = (svgrectangle['width']-margin) / data.length;
    var y = d3.scale.linear().domain([0, invmax]).range([svgrectangle['height'] - 20, 0]);
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
      .orient("left")
      .tickFormat(d3.format("s"));
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
    query = '''select item.name, coalesce(sum(buffer.onhand * item.cost),0)
               from buffer
               inner join item on buffer.item_id = item.name
               group by item.name
               order by 2 desc
               limit %s
              '''
    cursor.execute(query, (limit,))
    for res in cursor.fetchall():
      result.append('<tr><td>%s</td><td>%.2f</td></tr>' % (
        res[0], res[1]
        ))
    result.append('</table>')
    return HttpResponse('\n'.join(result))

Dashboard.register(InventoryByItemWidget)


class DeliveryPerformanceWidget(Widget):
  name = "delivery_performance"
  title = _("delivery performance")
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
          demand_id, max(case when enddate > operationplan.due then 1 else 0 end) late
        from operationplan
        left outer join demand
          on operationplan.demand_id = demand.name
        where demand.due < '%s'
        group by demand_id
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
