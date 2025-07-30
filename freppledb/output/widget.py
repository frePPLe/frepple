#
# Copyright (C) 2014 by frePPLe bv
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

from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.admin.utils import quote
from django.db import DEFAULT_DB_ALIAS, connections
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.utils.formats import date_format
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.models import Parameter
from freppledb.common.report import GridReport, getCurrency, getCurrentDate
from freppledb.input.models import (
    PurchaseOrder,
    DistributionOrder,
    OperationPlanResource,
)


class LateOrdersWidget(Widget):
    name = "late_orders"
    title = _("late orders")
    tooltip = _("Shows orders that will be delivered after their due date")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    url = "/problem/?noautofilter&entity=demand&name=late&sord=asc&sidx=startdate"
    exporturl = True
    limit = 20

    query = """
    select
      demand.name, demand.item_id, demand.location_id, demand.customer_id,
      out_problem.startdate, out_problem.enddate, out_problem.weight
    from out_problem
    inner join demand
      on out_problem.owner = demand.name
    where out_problem.name = 'late' and out_problem.entity = 'demand'
    order by out_problem.startdate, out_problem.weight desc
    limit %s
    """

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        cursor = connections[request.database].cursor()
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="alignleft">%s</th>'
            '<th class="alignleft">%s</th><th class="alignleft">%s</th>'
            '<th class="text-center">%s</th><th class="text-center">%s</th>'
            '<th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("name"))),
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("location"))),
                capfirst(force_str(_("customer"))),
                capfirst(force_str(_("due"))),
                capfirst(force_str(_("planned date"))),
                capfirst(force_str(_("delay"))),
            ),
        ]
        alt = False
        cursor.execute(cls.query, (limit,))
        for rec in cursor.fetchall():
            result.append(
                '<tr%s><td class="text-decoration-underline"><a href="%s/demandpegging/%s/">%s</a></td>'
                '<td class="alignleft">%s</td><td class="alignleft">%s</td>'
                '<td class="alignleft">%s</td><td class="alignleft">%s</td>'
                '<td class="text-center">%s</td><td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    request.prefix,
                    quote(rec[0]),
                    escape(rec[0]),
                    escape(rec[1]),
                    escape(rec[2]),
                    escape(rec[3]),
                    (
                        date_format(rec[4], format="DATE_FORMAT", use_l10n=False)
                        if rec[4]
                        else ""
                    ),
                    (
                        date_format(rec[5], format="DATE_FORMAT", use_l10n=False)
                        if rec[5]
                        else ""
                    ),
                    int(rec[6]),
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(LateOrdersWidget)


class ShortOrdersWidget(Widget):
    name = "short_orders"
    title = _("short orders")
    tooltip = _("Shows orders that are not planned completely")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    # Note the gte filter lets pass "short" and "unplanned", and filters out
    # "late" and "early".
    url = "/problem/?noautofilter&entity=demand&name__gte=short&sord=asc&sidx=startdate"
    exporturl = True
    limit = 20

    query = """
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
        """

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request):
        with connections[request.database].cursor() as cursor:
            limit = int(request.GET.get("limit", cls.limit))
            result = [
                '<div class="table-responsive"><table class="table table-sm table-hover">',
                '<thead><tr><th class="alignleft">%s</th><th class="alignleft">%s</th><th class="alignleft">%s</th>'
                '<th class="alignleft">%s</th><th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
                % (
                    capfirst(force_str(_("name"))),
                    capfirst(force_str(_("item"))),
                    capfirst(force_str(_("location"))),
                    capfirst(force_str(_("customer"))),
                    capfirst(force_str(_("due"))),
                    capfirst(force_str(_("short"))),
                ),
            ]
            alt = False
            cursor.execute(cls.query, (limit,))
            for rec in cursor.fetchall():
                result.append(
                    '<tr%s><td class="text-decoration-underline alignleft"><a href="%s/demandpegging/%s/">%s</a></td><td class="alignleft">%s</td>'
                    '<td class="alignleft">%s</td><td class="alignleft">%s</td><td class="text-center">%s</td>'
                    '<td class="text-center">%s</td></tr>'
                    % (
                        alt and ' class="altRow"' or "",
                        request.prefix,
                        quote(rec[0]),
                        escape(rec[0]),
                        escape(rec[1]),
                        escape(rec[2]),
                        escape(rec[3]),
                        (
                            date_format(rec[4], format="DATE_FORMAT", use_l10n=False)
                            if rec[4]
                            else ""
                        ),
                        int(rec[5]),
                    )
                )
                alt = not alt
            result.append("</table></div>")
            return HttpResponse("\n".join(result))


Dashboard.register(ShortOrdersWidget)


class ManufacturingOrderWidget(Widget):
    name = "manufacturing_orders"
    title = _("manufacturing orders")
    tooltip = _("Shows manufacturing orders by start date")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    url = "/data/input/manufacturingorder/?noautofilter&sord=asc&sidx=startdate&status__in=proposed,confirmed,approved"
    exporturl = True
    fence1 = 7
    fence2 = 30

    def args(self):
        return "?%s" % urlencode({"fence1": self.fence1, "fence2": self.fence2})

    javascript = r"""
    var margin_y = 70;  // Width allocated for the Y-axis

    var svg = d3.select("#mo_chart");
    var svgrectangle = document.getElementById("mo_chart").getBoundingClientRect();

    function numberWithCommas(x) {
    return x.toString().replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",");}

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_value = 0.0;
    var max_units = 0.0;
    var max_count = 0.0;
    var max_length = 0;
    var nth = Math.ceil($("#mo_overview").find("tr").length / (svgrectangle['width'] - margin_y) * 30);
    var myticks = [];

    $("#mo_overview").find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      if (name.text().length > max_length)
            max_length = name.text().length;
      var count = name.next();
      var units = count.next();
      var value = units.next();
      var startdate = value.next();
      var enddate = startdate.next();
      var el = [name.text(), parseFloat(count.text()), parseFloat(units.text()), parseFloat(value.text()), startdate.text(), enddate.text()];
      data.push(el);
      domain_x.push(el[0]);
      if (el[1] > max_count) max_count = el[1];
      if (el[2] > max_units) max_units = el[2];
      if (el[3] > max_value) max_value = el[3];
      if (idx %% nth == 0) myticks.push(name.text());
      });

    var margin_x = 9*max_length;  // Height allocated for the X-axis depends on x-axis titles

    const dropDownButton = document.querySelector('#mo_selectButton span');
    const options = document.querySelectorAll('#moul li a');

    for (const option of options) {
      option.addEventListener('click', event => {
        dropDownButton.textContent = event.target.textContent;

        // recover the option that has been chosen
        var selectedOption = event.target.textContent;
        // run the updateChart function with this selected option

        d3.selectAll('#mo_yaxis').remove();
        d3.selectAll('#mo_bar').remove();
        draw();
      });
    }

    // Define axis domains
    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);

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

    // get position of the first tick in the graph
    var tickposition = 0;
    if (typeof $("#xAxisMO").children()[0].attributes !== 'undefined') {
    tickposition = parseInt($("#xAxisMO").children()[0].attributes.transform.value.slice(10));
    }

    function draw() {
        const selectButtonValue = document.querySelector('#mo_selectButton span').textContent;
        var y_value = d3.scale.linear()
        .range([svgrectangle['height'] - margin_x - 10, 0])
        .domain([0, (selectButtonValue == "value" ? max_value:max_units) + 5]);

        // Draw y-axis
        var yAxis = d3.svg.axis().scale(y_value)
            .orient("left")
            .ticks(Math.min(Math.floor((svgrectangle['height'] - 10 - margin_x) / 20), 5))
            .tickFormat(d3.format("s"));
        svg.append("g")
        .attr("transform", "translate(" + margin_y + ", 10 )")
        .attr("class", "y axis")
        .attr("id","mo_yaxis")
        .call(yAxis);

        // Draw rectangles
        svg.selectAll("g>rect")
        .data(data)
        .enter()
        .append("g")
        .append("rect")
        .attr("id","mo_bar")
        .attr("x",function(d, i) {return tickposition + i*x.rangeBand() - x.rangeBand()/2 + margin_y;})
        .attr("y",function(d, i) {return svgrectangle['height'] - margin_x - (y_value(0) -
        (selectButtonValue == "value" ? y_value(d[3]):y_value(d[2])));})
        .attr("height", function(d, i) {return y_value(0) -
        (selectButtonValue == "value" ? y_value(d[3]):y_value(d[2]));})
        .attr("width", x.rangeBand())
        .attr('fill', '#828915')
        .on("mouseover", function(d) {
            graph.showTooltip(d[0] + '<br>'+ numberWithCommas(d[1]) + " MOs / " + numberWithCommas(d[2]) + ' %s / ' + currency[0] + ' ' + numberWithCommas(d[3]) + currency[1] );
            $("#tooltip").css('background-color','black').css('color','white');
            })
        .on("mousemove", graph.moveTooltip)
        .on("mouseout", graph.hideTooltip)
        .on("click", function(d) {
                if (d3.event.defaultPrevented || y_value(d[3]) == 0)
                    return;
                d3.select("#tooltip").style('display', 'none');

                window.location = url_prefix
                    + "/data/input/manufacturingorder/"
                    + "?noautofilter&startdate__gte=" + d[4]
                    + "&startdate__lt=" + d[5];

                d3.event.stopPropagation();
                });
    }
    draw();

    """ % force_str(
        _("units")
    )

    @classmethod
    def render(cls, request):
        fence1 = int(request.GET.get("fence1", cls.fence1))
        fence2 = int(request.GET.get("fence2", cls.fence2))
        currency = getCurrency()
        current = getCurrentDate(request.database, lastplan=True)
        GridReport.getBuckets(request)
        cursor = connections[request.database].cursor()
        query = """
          select
            0, common_bucketdetail.name, common_bucketdetail.startdate,
            count(operationplan.name), coalesce(round(sum(quantity)),0),
            coalesce(round(sum(quantity * item.cost)),0),
         to_char(common_bucketdetail.startdate, %%s), to_char(common_bucketdetail.enddate, %%s)
          from common_bucketdetail
          left outer join operationplan
            on operationplan.startdate >= common_bucketdetail.startdate
            and operationplan.startdate < common_bucketdetail.enddate
            and status in ('confirmed', 'proposed', 'approved')
            and operationplan.type = 'MO'
          left outer join operation
            on operationplan.operation_id = operation.name
          left outer join item
            on operationplan.item_id = item.name
          where bucket_id = %%s and common_bucketdetail.enddate > %%s
            and common_bucketdetail.startdate < %%s
          and exists (select 1 from operationplan where type = 'MO'
          and status in ('confirmed', 'proposed', 'approved')
          and startdate >= common_bucketdetail.startdate)
          group by common_bucketdetail.name, common_bucketdetail.startdate, common_bucketdetail.enddate
          union all
          select
            1, null, null, count(*),
            coalesce(round(sum(quantity)),0),
            coalesce(round(sum(quantity * cost)),0),null,null
          from operationplan
          inner join operation
            on operationplan.operation_id = operation.name
          where status in ('confirmed', 'approved')
            and operationplan.type = 'MO'
          union all
          select
            2, null, null, count(*),
            coalesce(round(sum(quantity)),0),
            coalesce(round(sum(quantity * cost)),0),null,null
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
            coalesce(round(sum(quantity * cost)),0),null,null
          from operationplan
          inner join operation
            on operationplan.operation_id = operation.name
          where status = 'proposed'
            and startdate < %%s + interval '%s day'
            and operationplan.type = 'MO'
          order by 1, 3
          """ % (
            fence1,
            fence2,
        )
        cursor.execute(
            query,
            (
                "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                request.report_bucket,
                request.report_startdate,
                request.report_enddate,
                current,
                current,
            ),
        )
        result = [
            '<div class="dropdown">',
            '<button id="mo_selectButton" class="form-select form-select-sm d-inline-block w-auto text-capitalize" type="button" data-bs-toggle="dropdown" aria-expanded="false">',
            "<span>value</span>",
            "</button>",
            '<ul id="moul" class="dropdown-menu w-auto" style="min-width: unset" aria-labelledby="mo_selectButton">',
            '<li><a class="dropdown-item text-capitalize">value</a></li>',
            '<li><a class="dropdown-item text-capitalize">unit</a></li>',
            "</ul>",
            "</div>",
            '<svg class="chart mb-2" id="mo_chart" style="width:100%; height: 170px;"></svg>',
            '<table id="mo_overview" style="display: none">',
        ]
        for rec in cursor.fetchall():
            if rec[0] == 0:
                result.append(
                    "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (rec[1], rec[3], rec[4], rec[5], rec[6], rec[7])
                )
            elif rec[0] == 1 and rec[3] > 0:
                result.append(
                    '</table><div class="row"><div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/manufacturingorder/?noautofilter&sord=asc&sidx=startdate&amp;status__in=confirmed,approved" role="button" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        force_str(_("Review")),
                        force_str(_("confirmed orders")),
                    )
                )
            elif rec[0] == 1:
                result.append('</table><div class="row">')
            elif rec[0] == 2 and fence1 and rec[3] > 0:
                limit_fence1 = current + timedelta(days=fence1)
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/manufacturingorder/?noautofilter&sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" role="button" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        limit_fence1.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(
                            _("proposed orders within %(fence)s days")
                            % {"fence": fence1}
                        ),
                    )
                )
            elif rec[0] == 3 and fence2 and rec[3] > 0:
                limit_fence2 = current + timedelta(days=fence2)
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/manufacturingorder/?noautofilter&sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" rol="button" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        limit_fence2.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(
                            _("proposed orders within %(fence)s days")
                            % {"fence": fence2}
                        ),
                    )
                )
        result.append("</div>")
        return HttpResponse("\n".join(result))


Dashboard.register(ManufacturingOrderWidget)


class DistributionOrderWidget(Widget):
    name = "distribution_orders"
    title = _("distribution orders")
    tooltip = _("Shows distribution orders by start date")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    url = "/data/input/distributionorder/?noautofilter&sord=asc&sidx=startdate&status__in=proposed,confirmed"
    exporturl = True
    fence1 = 7
    fence2 = 30

    def args(self):
        return "?%s" % urlencode({"fence1": self.fence1, "fence2": self.fence2})

    javascript = r"""
    var margin_y = 70;  // Width allocated for the Y-axis
    var svg = d3.select("#do_chart");
    var svgrectangle = document.getElementById("do_chart").getBoundingClientRect();

    function numberWithCommas(x) {
    return x.toString().replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",");}

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_value = 0.0;
    var max_units = 0.0;
    var max_count = 0.0;
    var max_length = 0;

    var nth = Math.ceil($("#do_overview").find("tr").length / (svgrectangle['width'] - margin_y) * 30);
    var myticks = [];

    $("#do_overview").find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      if (name.text().length > max_length)
            max_length = name.text().length;
      var count = name.next();
      var units = count.next();
      var value = units.next();
      var startdate = value.next();
      var enddate = startdate.next();
      var el = [name.text(), parseFloat(count.text()), parseFloat(units.text()), parseFloat(value.text()), startdate.text(), enddate.text()];
      data.push(el);
      domain_x.push(el[0]);
      if (el[1] > max_count) max_count = el[1];
      if (el[2] > max_units) max_units = el[2];
      if (el[3] > max_value) max_value = el[3];
      if (idx %% nth == 0) myticks.push(name.text());
      });

    var margin_x = 9*max_length;  // Height allocated for the X-axis depends on x-axis titles

    const dropDownButton = document.querySelector('#do_selectButton span');
    const options = document.querySelectorAll('#doul li a');

    for (const option of options) {
      option.addEventListener('click', event => {
        dropDownButton.textContent = event.target.textContent;

        // recover the option that has been chosen
        var selectedOption = event.target.textContent;
        // run the updateChart function with this selected option

        d3.selectAll('#do_yaxis').remove();
        d3.selectAll('#do_bar').remove();
        draw();
      });
    }

    // Define axis domains
    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);

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



    // get position of the first tick in the graph
    var tickposition = 0;
    if (typeof $("#xAxisDO").children()[0].attributes !== 'undefined') {
      tickposition = parseInt($("#xAxisDO").children()[0].attributes.transform.value.slice(10));
    }

    function draw() {
        const selectButtonValue = document.querySelector('#do_selectButton span').textContent;
        var y_value = d3.scale.linear()
         .range([svgrectangle['height'] - margin_x - 10, 0])
         .domain([0,
         (selectButtonValue == "value" ? max_value:max_units)
         + 5]);

        // Draw y-axis
        var yAxis = d3.svg.axis().scale(y_value)
        .orient("left")
        .ticks(Math.min(Math.floor((svgrectangle['height'] - 10 - margin_x) / 20), 5))
        .tickFormat(d3.format("s"));
        svg.append("g")
        .attr("transform", "translate(" + margin_y + ", 10 )")
         .attr("class", "y axis")
         .attr("id","do_yaxis")
         .call(yAxis);

        // Draw rectangles
        svg.selectAll("g>rect")
        .data(data)
        .enter()
        .append("g")
        .append("rect")
        .attr("id","do_bar")
        .attr("x",function(d, i) {return tickposition + i*x.rangeBand() - x.rangeBand()/2 + margin_y;})
        .attr("y",function(d, i) {return svgrectangle['height'] - margin_x - (y_value(0) -
        (selectButtonValue == "value" ? y_value(d[3]):y_value(d[2]))
        );})
        .attr("height", function(d, i) {return y_value(0) -
        (selectButtonValue == "value" ? y_value(d[3]):y_value(d[2]))
        ;})
        .attr("width", x.rangeBand())
        .attr('fill', '#828915')
        .on("mouseover", function(d) {
            graph.showTooltip(d[0] + '<br>'+ numberWithCommas(d[1]) + " DOs / " + numberWithCommas(d[2]) + ' %s / ' + currency[0] + ' ' + numberWithCommas(d[3]) + currency[1] );
            $("#tooltip").css('background-color','black').css('color','white');
            })
        .on("mousemove", graph.moveTooltip)
        .on("mouseout", graph.hideTooltip)
        .on("click", function(d) {
                if (d3.event.defaultPrevented || y_value(d[3]) == 0)
                    return;
                d3.select("#tooltip").style('display', 'none');

                window.location = url_prefix
                    + "/data/input/distributionorder/"
                    + "?noautofilter&startdate__gte=" + d[4]
                    + "&startdate__lt=" + d[5];

                d3.event.stopPropagation();
                });
    }
    draw();

    """ % force_str(
        _("units")
    )

    @classmethod
    def render(cls, request):
        fence1 = int(request.GET.get("fence1", cls.fence1))
        fence2 = int(request.GET.get("fence2", cls.fence2))
        currency = getCurrency()
        current = getCurrentDate(request.database, lastplan=True)
        GridReport.getBuckets(request)
        cursor = connections[request.database].cursor()
        query = """
      select
         0, common_bucketdetail.name, common_bucketdetail.startdate,
         count(operationplan.name), coalesce(round(sum(quantity)),0),
         coalesce(round(sum(item.cost * quantity)),0),
         to_char(common_bucketdetail.startdate, %%s), to_char(common_bucketdetail.enddate, %%s)
      from common_bucketdetail
      left outer join operationplan
        on operationplan.startdate >= common_bucketdetail.startdate
        and operationplan.startdate < common_bucketdetail.enddate
        and operationplan.type = 'DO'
        and status in ('confirmed', 'proposed', 'approved')
      left outer join item
        on operationplan.item_id = item.name
      where bucket_id = %%s and common_bucketdetail.enddate > %%s
        and common_bucketdetail.startdate < %%s
      and exists (select 1 from operationplan where type = 'DO'
       and status in ('confirmed', 'proposed', 'approved')
       and startdate >= common_bucketdetail.startdate)
      group by common_bucketdetail.name, common_bucketdetail.startdate, common_bucketdetail.enddate
      union all
      select
        1, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(item.cost * quantity)),0), null, null
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      where status in ('confirmed', 'approved') and operationplan.type = 'DO'
      union all
      select
        2, null, null, count(*),
        coalesce(round(sum(item.cost)),0),
        coalesce(round(sum(item.cost * quantity)),0), null, null
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      where status = 'proposed' and startdate < %%s + interval '%s day'
      and operationplan.type = 'DO'
      union all
      select
        3, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(item.cost * quantity)),0), null, null
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      where status = 'proposed' and startdate < %%s + interval '%s day'
      and operationplan.type = 'DO'
      order by 1, 3
      """ % (
            fence1,
            fence2,
        )
        cursor.execute(
            query,
            (
                "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                request.report_bucket,
                request.report_startdate,
                request.report_enddate,
                current,
                current,
            ),
        )
        result = [
            '<div class="dropdown">',
            '<button id="do_selectButton" class="form-select form-select-sm d-inline-block w-auto text-capitalize" type="button" data-bs-toggle="dropdown" aria-expanded="false">',
            "<span>value</span>",
            "</button>",
            '<ul id="doul" class="dropdown-menu w-auto" style="min-width: unset" aria-labelledby="do_selectButton">',
            '<li><a class="dropdown-item text-capitalize">value</a></li>',
            '<li><a class="dropdown-item text-capitalize">unit</a></li>',
            "</ul>",
            "</div>",
            '<svg class="chart mb-2" id="do_chart" style="width:100%; height: 170px;"></svg>',
            '<table id="do_overview" style="display: none">',
        ]
        for rec in cursor.fetchall():
            if rec[0] == 0:
                result.append(
                    "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (rec[1], rec[3], rec[4], rec[5], rec[6], rec[7])
                )
            elif rec[0] == 1 and rec[3] > 0:
                result.append(
                    '</table><div class="row"><div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/distributionorder/?noautofilter&sord=asc&sidx=startdate&amp;status__in=confirmed,approved" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        force_str(_("Review")),
                        force_str(_("confirmed orders")),
                    )
                )
            elif rec[0] == 1:
                result.append('</table><div class="row">')
            elif rec[0] == 2 and fence1 and rec[3] > 0:
                limit_fence1 = current + timedelta(days=fence1)
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/distributionorder/?noautofilter&sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        limit_fence1.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(
                            _("proposed orders within %(fence)s days")
                            % {"fence": fence1}
                        ),
                    )
                )
            elif rec[0] == 3 and fence2 and rec[3] > 0:
                limit_fence2 = current + timedelta(days=fence2)
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href=%s/data/input/distributionorder/?noautofilter&sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        limit_fence2.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(
                            _("proposed orders within %(fence)s days")
                            % {"fence": fence2}
                        ),
                    )
                )
        result.append("</div>")
        return HttpResponse("\n".join(result))


Dashboard.register(DistributionOrderWidget)


class PurchaseOrderWidget(Widget):
    name = "purchase_orders"
    title = _("purchase orders")
    tooltip = _("Shows purchase orders by ordering date")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    url = "/data/input/purchaseorder/?sord=asc&sidx=startdate&status__in=proposed,confirmed,approved"
    exporturl = True
    fence1 = 7
    fence2 = 30
    supplier = None

    def args(self):
        if self.supplier:
            return "?%s" % urlencode(
                {
                    "fence1": self.fence1,
                    "fence2": self.fence2,
                    "supplier": self.supplier,
                }
            )
        else:
            return "?%s" % urlencode({"fence1": self.fence1, "fence2": self.fence2})

    javascript = r"""
    var margin_y = 70;  // Width allocated for the Y-axis
    var svg = d3.select("#po_chart");
    var svgrectangle = document.getElementById("po_chart").getBoundingClientRect();

    function numberWithCommas(x) {
    return x.toString().replace(/\B(?<!\.\d*)(?=(\d{3})+(?!\d))/g, ",");}

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_value = 0.0;
    var max_units = 0.0;
    var max_count = 0.0;
    var max_length = 0;
    var nth = Math.ceil($("#po_overview").find("tr").length / (svgrectangle['width'] - margin_y) * 30);
    var myticks = [];

    $("#po_overview").find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      if (name.text().length > max_length)
            max_length = name.text().length;
      var count = name.next();
      var units = count.next()
      var value = units.next()
      var startdate = value.next();
      var enddate = startdate.next();
      var el = [name.text(), parseFloat(count.text()), parseFloat(units.text()), parseFloat(value.text()), startdate.text(), enddate.text()];
      data.push(el);
      domain_x.push(el[0]);
      if (el[1] > max_count) max_count = el[1];
      if (el[2] > max_units) max_units = el[2];
      if (el[3] > max_value) max_value = el[3];
      if (idx %% nth == 0) myticks.push(name.text());
      });

    var margin_x = 9*max_length;  // Height allocated for the X-axis depends on x-axis titles

    const dropDownButton = document.querySelector('#po_selectButton span');
    const options = document.querySelectorAll('#poul li a');

    for (const option of options) {
      option.addEventListener('click', event => {
        dropDownButton.textContent = event.target.textContent;

        // recover the option that has been chosen
        var selectedOption = event.target.textContent;
        // run the updateChart function with this selected option

        d3.selectAll('#po_yaxis').remove();
        d3.selectAll('#po_bar').remove();
        draw();
      });
    }

    // Define axis domains
    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);

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

    // get position of the first tick in the graph
    var tickposition = 0;
    if (typeof $("#xAxisPO").children()[0].attributes !== 'undefined') {
      tickposition = parseInt($("#xAxisPO").children()[0].attributes.transform.value.slice(10));
    }

    function draw() {
        const selectButtonValue = document.querySelector('#po_selectButton span').textContent;
        var y_value = d3.scale.linear()
        .range([svgrectangle['height'] - margin_x - 10, 0])
        .domain([0, (selectButtonValue == "value" ? max_value:max_units) + 5]);

        // Draw y-axis
         var yAxis = d3.svg.axis().scale(y_value)
        .orient("left")
        .ticks(Math.min(Math.floor((svgrectangle['height'] - 10 - margin_x) / 20), 5))
        .tickFormat(d3.format("s"));
         svg.append("g")
        .attr("transform", "translate(" + margin_y + ", 10 )")
        .attr("class", "y axis")
        .attr("id","po_yaxis")
        .call(yAxis);

        // Draw rectangles
        svg.selectAll("g>rect")
        .data(data)
        .enter()
        .append("g")
        .append("rect")
        .attr("id","po_bar")
        .attr("x",function(d, i) {return tickposition + i*x.rangeBand() - x.rangeBand()/2 + margin_y;})
        .attr("y",function(d, i) {return svgrectangle['height'] - margin_x - (y_value(0) -
        (selectButtonValue == "value" ? y_value(d[3]):y_value(d[2]))
        );})
        .attr("height", function(d, i) {return y_value(0) -
        (selectButtonValue == "value" ? y_value(d[3]):y_value(d[2]))
        ;})
        .attr("width", x.rangeBand())
        .attr('fill', '#828915')
        .on("mouseover", function(d) {
            graph.showTooltip(d[0] + '<br>'+ numberWithCommas(d[1]) + " POs / " + numberWithCommas(d[2]) + ' %s / ' + currency[0] + ' ' + numberWithCommas(d[3]) + currency[1] );
            $("#tooltip").css('background-color','black').css('color','white');
            })
        .on("mousemove", graph.moveTooltip)
        .on("mouseout", graph.hideTooltip)
        .on("click", function(d) {
                if (d3.event.defaultPrevented || y_value(d[3]) == 0)
                    return;
                d3.select("#tooltip").style('display', 'none');

                window.location = url_prefix
                    + "/data/input/purchaseorder/"
                    + "?noautofilter&startdate__gte=" + d[4]
                    + "&startdate__lt=" + d[5];

                d3.event.stopPropagation();
                });
    }
    draw();
    """ % force_str(
        _("units")
    )

    @classmethod
    def render(cls, request):
        fence1 = int(request.GET.get("fence1", cls.fence1))
        fence2 = int(request.GET.get("fence2", cls.fence2))
        supplier = request.GET.get("supplier", cls.supplier)
        currency = getCurrency()
        current = getCurrentDate(request.database, lastplan=True)
        GridReport.getBuckets(request)
        supplierfilter = "and supplier_id = %s" if supplier else ""
        cursor = connections[request.database].cursor()
        query = """
      select
         0, common_bucketdetail.name, common_bucketdetail.startdate,
         count(operationplan.name), coalesce(round(sum(quantity)),0),
         coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0),
         to_char(common_bucketdetail.startdate, %%s), to_char(common_bucketdetail.enddate, %%s)
      from common_bucketdetail
      left outer join operationplan
        on operationplan.startdate >= common_bucketdetail.startdate
        and operationplan.startdate < common_bucketdetail.enddate
        and status in ('confirmed', 'proposed', 'approved')
        and operationplan.type = 'PO' %s
      left outer join item
        on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where bucket_id = %%s and common_bucketdetail.enddate > %%s
        and common_bucketdetail.startdate < %%s
      and exists (select 1 from operationplan where type = 'PO'
       and status in ('confirmed', 'proposed', 'approved')
       and startdate >= common_bucketdetail.startdate)
      group by common_bucketdetail.name, common_bucketdetail.startdate, common_bucketdetail.enddate
      union all
      select
        1, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0), null, null
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status in ('confirmed', 'approved') %s
        and operationplan.type = 'PO'
      union all
      select
        2, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0), null, null
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status = 'proposed' and operationplan.type = 'PO'
        and startdate < %%s + interval '%s day' %s
      union all
      select
        3, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0), null, null
      from operationplan
      inner join item
        on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status = 'proposed' and operationplan.type = 'PO'
        and startdate < %%s + interval '%s day' %s
      union all
      select
        4, null, null, count(*),
        coalesce(round(sum(quantity)),0),
        coalesce(round(sum(coalesce(itemsupplier.cost,item.cost) * quantity)),0), null, null
      from operationplan
      inner join item
      on operationplan.item_id = item.name
      left outer join itemsupplier
        on operationplan.item_id = itemsupplier.item_id
        and operationplan.supplier_id = itemsupplier.supplier_id
        and operationplan.location_id = itemsupplier.location_id
      where status in ('confirmed', 'approved') %s
        and operationplan.type = 'PO'
        and operationplan.enddate < %%s
      order by 1, 3
      """ % (
            supplierfilter,
            supplierfilter,
            fence1,
            supplierfilter,
            fence2,
            supplierfilter,
            supplierfilter,
        )
        if supplier:
            cursor.execute(
                query,
                (
                    "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                    "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                    request.report_bucket,
                    request.report_startdate,
                    request.report_enddate,
                    supplier,
                    supplier,
                    current,
                    supplier,
                    current,
                    supplier,
                    current,
                ),
            )
        else:
            cursor.execute(
                query,
                (
                    "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                    "%s HH24:MI:SS" % (settings.DATE_FORMAT_JS,),
                    request.report_bucket,
                    request.report_startdate,
                    request.report_enddate,
                    current,
                    current,
                    current,
                ),
            )
        result = [
            '<div class="dropdown">',
            '<button id="po_selectButton" class="form-select form-select-sm d-inline-block w-auto text-capitalize" type="button" data-bs-toggle="dropdown" aria-expanded="false">',
            "<span>value</span>",
            "</button>",
            '<ul id="poul" class="dropdown-menu w-auto" style="min-width: unset" aria-labelledby="po_selectButton">',
            '<li><a class="dropdown-item text-capitalize">value</a></li>',
            '<li><a class="dropdown-item text-capitalize">unit</a></li>',
            "</ul>",
            "</div>",
            '<svg class="chart mb-2" id="po_chart" style="width:100%; height: 170px;"></svg>',
            '<table id="po_overview" style="display: none">',
        ]
        for rec in cursor.fetchall():
            if rec[0] == 0:
                result.append(
                    "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (rec[1], rec[3], rec[4], rec[5], rec[6], rec[7])
                )
            elif rec[0] == 1 and rec[3] > 0:
                result.append(
                    '</table><div class="row"><div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?noautofilter&sord=asc&sidx=startdate&amp;status__in=confirmed,approved" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        force_str(_("Review")),
                        force_str(_("confirmed orders")),
                    )
                )
            elif rec[0] == 1:
                result.append('</table><div class="row">')
            elif rec[0] == 2 and fence1 and rec[3] > 0:
                limit_fence1 = current + timedelta(days=fence1)
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?noautofilter&sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        limit_fence1.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(
                            _("proposed orders within %(fence)s days")
                            % {"fence": fence1}
                        ),
                    )
                )
            elif rec[0] == 3 and fence2 and rec[3] > 0:
                limit_fence2 = current + timedelta(days=fence2)
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?noautofilter&sord=asc&sidx=startdate&startdate__lte=%s&amp;status=proposed" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        limit_fence2.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(
                            _("proposed orders within %(fence)s days")
                            % {"fence": fence2}
                        ),
                    )
                )
            elif rec[0] == 4 and rec[3] > 0:
                result.append(
                    '<div class="col"><h2>%s / %s %s / %s%s%s&nbsp;<a href="%s/data/input/purchaseorder/?noautofilter&sord=asc&sidx=enddate&enddate__lte=%s&amp;status__in=confirmed,approved" class="btn btn-primary btn-sm">%s</a></h2><small>%s</small></div>'
                    % (
                        f"{rec[3]:,}",
                        f"{rec[4]:,}",
                        force_str(_("units")),
                        currency[0],
                        f"{rec[5]:,}",
                        currency[1],
                        request.prefix,
                        current.strftime("%Y-%m-%d"),
                        force_str(_("Review")),
                        force_str(_("overdue orders")),
                    )
                )
        result.append("</div>")
        return HttpResponse("\n".join(result))


Dashboard.register(PurchaseOrderWidget)


class PurchaseQueueWidget(Widget):
    name = "purchase_queue"
    title = _("purchase queue")
    tooltip = _("Display a list of new purchase orders")
    permissions = (("view_purchaseorder", "Can view purchase orders"),)
    asynchronous = True
    url = "/data/input/purchaseorder/?noautofilter&status=proposed&sidx=startdate&sord=asc"
    exporturl = True
    limit = 20

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("supplier"))),
                capfirst(force_str(_("enddate"))),
                capfirst(force_str(_("quantity"))),
                capfirst(force_str(_("criticality"))),
            ),
        ]
        alt = False
        for po in (
            PurchaseOrder.objects.using(request.database)
            .filter(status="proposed")
            .order_by("startdate")[:limit]
        ):
            result.append(
                '<tr%s><td>%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    escape(po.item.name),
                    escape(po.supplier.name),
                    (
                        date_format(po.enddate, format="DATE_FORMAT", use_l10n=False)
                        if po.enddate
                        else ""
                    ),
                    int(po.quantity),
                    int(po.criticality),
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(PurchaseQueueWidget)


class DistributionQueueWidget(Widget):
    name = "distribution_queue"
    title = _("distribution queue")
    tooltip = _("Display a list of new distribution orders")
    permissions = (("view_distributionorder", "Can view distribution order"),)
    asynchronous = True
    url = "/data/input/distributionorder/?noautofilter&status=proposed&sidx=startdate&sord=asc"
    exporturl = True
    limit = 20

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("origin"))),
                capfirst(force_str(_("destination"))),
                capfirst(force_str(_("enddate"))),
                capfirst(force_str(_("quantity"))),
                capfirst(force_str(_("criticality"))),
            ),
        ]
        alt = False
        for po in (
            DistributionOrder.objects.using(request.database)
            .filter(status="proposed")
            .order_by("startdate")[:limit]
        ):
            result.append(
                '<tr%s><td>%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    escape(po.item.name),
                    escape(po.origin.name if po.origin else ""),
                    escape(po.destination.name),
                    (
                        date_format(po.enddate, format="DATE_FORMAT", use_l10n=False)
                        if po.enddate
                        else ""
                    ),
                    int(po.quantity),
                    int(po.criticality),
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(DistributionQueueWidget)


class ShippingQueueWidget(Widget):
    name = "shipping_queue"
    title = _("shipping queue")
    tooltip = _("Display a list of new distribution orders")
    permissions = (("view_distributionorder", "Can view distribution order"),)
    asynchronous = True
    url = "/data/input/distributionorder/?noautofilter&sidx=plandate&sord=asc"
    exporturl = True
    limit = 20

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("origin"))),
                capfirst(force_str(_("destination"))),
                capfirst(force_str(_("quantity"))),
                capfirst(force_str(_("start date"))),
                capfirst(force_str(_("criticality"))),
            ),
        ]
        alt = False
        for do in (
            DistributionOrder.objects.using(request.database)
            .filter(status="proposed")
            .order_by("startdate")[:limit]
        ):
            result.append(
                '<tr%s><td>%s</td><td>%s</td><td>%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    escape(do.item),
                    escape(do.origin.name),
                    escape(do.destination),
                    int(do.quantity),
                    (
                        date_format(do.enddate, format="DATE_FORMAT", use_l10n=False)
                        if do.enddate
                        else ""
                    ),
                    int(do.criticality),
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(ShippingQueueWidget)


class ResourceQueueWidget(Widget):
    name = "resource_queue"
    title = _("resource queue")
    tooltip = _("Display planned activities for the resources")
    permissions = (("view_resource_report", "Can view resource report"),)
    asynchronous = True
    url = "/data/input/operationplanresource/?sidx=operatiopnplan__startdate&sord=asc"
    exporturl = True
    limit = 20

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            "<thead><tr>"
            '<th class="alignleft">%s</th>'
            '<th>%s</th><th class="text-center">%s</th>'
            '<th class="text-center">%s</th>'
            '<th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("resource"))),
                capfirst(force_str(_("operation"))),
                capfirst(force_str(_("startdate"))),
                capfirst(force_str(_("enddate"))),
                capfirst(force_str(_("quantity"))),
                capfirst(force_str(_("criticality"))),
            ),
        ]
        alt = False
        for ldplan in (
            OperationPlanResource.objects.using(request.database)
            .select_related()
            .order_by("operationplan__startdate")[:limit]
        ):
            result.append(
                '<tr%s><td class="text-decoration-underline"><a href="%s/data/input/operationplanresource/?noautofilter&resource=%s&sidx=startdate&sord=asc">%s</a></td><td>%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    request.prefix,
                    quote(ldplan.resource),
                    escape(ldplan.resource),
                    escape(ldplan.operationplan.operation),
                    (
                        date_format(
                            ldplan.operationplan.startdate,
                            format="DATE_FORMAT",
                            use_l10n=False,
                        )
                        if ldplan.operationplan.startdate
                        else ""
                    ),
                    (
                        date_format(
                            ldplan.operationplan.enddate,
                            format="DATE_FORMAT",
                            use_l10n=False,
                        )
                        if ldplan.operationplan.enddate
                        else ""
                    ),
                    int(ldplan.operationplan.quantity),
                    int(ldplan.operationplan.criticality),
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(ResourceQueueWidget)


class PurchaseAnalysisWidget(Widget):
    name = "purchase_order_analysis"
    title = _("purchase order analysis")
    tooltip = _("Analyse the urgency of existing purchase orders")
    permissions = (("view_purchaseorder", "Can view purchase orders"),)
    asynchronous = True
    url = "/data/input/purchaseorder/?noautofilter&status=confirmed&sidx=color&sord=asc"
    limit = 20

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("supplier"))),
                capfirst(force_str(_("enddate"))),
                capfirst(force_str(_("quantity"))),
                capfirst(force_str(_("inventory status"))),
            ),
        ]
        alt = False
        for po in (
            PurchaseOrder.objects.using(request.database)
            .filter(status="confirmed")
            .exclude(criticality=999)
            .order_by("color", "enddate")[:limit]
        ):
            result.append(
                '<tr%s><td>%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s</td><td class="text-center">%s%%</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    escape(po.item.name if po.item else ""),
                    escape(po.supplier.name if po.supplier else ""),
                    (
                        date_format(po.enddate, format="DATE_FORMAT", use_l10n=False)
                        if po.enddate
                        else ""
                    ),
                    int(po.quantity) if po.quantity else "",
                    int(po.color) if po.color is not None else "",
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(PurchaseAnalysisWidget)


class AlertsWidget(Widget):
    name = "alerts"
    title = _("alerts")
    tooltip = _("Overview of all alerts in the plan")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    url = "/problem/"
    entities = "material,capacity,demand,operation"

    @classmethod
    def render(cls, request):
        entities = request.GET.get("entities", cls.entities).split(",")
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("type"))),
                capfirst(force_str(_("count"))),
                capfirst(force_str(_("weight"))),
            ),
        ]
        cursor = connections[request.database].cursor()
        query = """
            select name, count(*), sum(weight)
            from out_problem
            where entity in (%s)
            group by name
            order by name
        """ % (
            ", ".join(["%s"] * len(entities))
        )
        cursor.execute(query, entities)
        alt = False
        for res in cursor.fetchall():
            result.append(
                '<tr%s><td class="text-decoration-underline"><a href="%s/problem/?noautofilter&name=%s">%s</a></td><td class="text-center">%d</td><td class="text-center">%d</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    request.prefix,
                    quote(res[0]),
                    res[0],
                    res[1],
                    res[2],
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(AlertsWidget)


class DemandAlertsWidget(AlertsWidget):
    name = "demand_alerts"
    title = _("demand alerts")
    url = "/problem/?noautofilter&entity=demand"
    entities = "demand"


Dashboard.register(DemandAlertsWidget)


class CapacityAlertsWidget(AlertsWidget):
    name = "capacity_alerts"
    title = _("capacity alerts")
    url = "/problem/?noautofilter&entity=capacity"
    entities = "capacity"


Dashboard.register(CapacityAlertsWidget)


class MaterialAlertsWidget(AlertsWidget):
    name = "material_alerts"
    title = _("material alerts")
    url = "/problem/?noautofilter&entity=material"
    entities = "material"


Dashboard.register(MaterialAlertsWidget)


class ResourceLoadWidget(Widget):
    name = "resource_utilization"
    title = _("resource utilization")
    tooltip = _("Shows the resources with the highest utilization")
    permissions = (("view_resource_report", "Can view resource report"),)
    asynchronous = True
    url = "/resource/"
    exporturl = True
    limit = 5
    high = 90
    medium = 80

    def args(self):
        return "?%s" % urlencode(
            {"limit": self.limit, "medium": self.medium, "high": self.high}
        )

    javascript = """
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
    """

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        medium = int(request.GET.get("medium", cls.medium))
        high = int(request.GET.get("high", cls.high))
        result = [
            '<svg class="chart" id="resLoad" style="width:100%%; height: %spx;"></svg>'
            % (limit * 25 + 30),
            '<table style="display:none">',
        ]
        cursor = connections[request.database].cursor()
        GridReport.getBuckets(request)
        query = """select
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
              """
        cursor.execute(query, (request.report_startdate, request.report_enddate, limit))
        for res in cursor.fetchall():
            result.append(
                '<tr><td><a href="%s/resource/%s/?noautofilter">%s</a></td><td class="util">%.2f</td></tr>'
                % (request.prefix, quote(res[0]), res[0], res[1])
            )
        result.append("</table>")
        result.append(
            '<span id="resload_medium" style="display:none">%s</span>' % medium
        )
        result.append('<span id="resload_high" style="display:none">%s</span>' % high)
        return HttpResponse("\n".join(result))


Dashboard.register(ResourceLoadWidget)


class InventoryByLocationWidget(Widget):
    name = "inventory_by_location"
    title = _("inventory by location")
    tooltip = _("Display the locations with the highest inventory value")
    asynchronous = True
    limit = 5

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    javascript = """
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
      .ticks(Math.min(Math.floor((svgrectangle['height'] - 20) / 20), 8))
      .orient("left")
      .tickFormat(d3.format("s"));
    d3.select("#invByLoc")
      .append("g")
      .attr("transform", "translate(" + margin + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);
    """

    query = """select location_id, coalesce(sum(buffer.onhand * item.cost),0)
             from buffer
             inner join item on buffer.item_id = item.name
             group by location_id
             order by 2 desc
             limit %s"""

    @classmethod
    def render(cls, request):
        limit = int(request.GET.get("limit", cls.limit))
        result = [
            '<svg class="chart" id="invByLoc" style="width:100%; height: 250px;"></svg>',
            '<table style="display:none">',
        ]
        cursor = connections[request.database].cursor()
        cursor.execute(cls.query, (limit,))
        for res in cursor.fetchall():
            result.append("<tr><td>%s</td><td>%.2f</td></tr>" % (res[0], res[1]))
        result.append("</table>")
        return HttpResponse("\n".join(result))


Dashboard.register(InventoryByLocationWidget)


class InventoryByItemWidget(Widget):
    name = "inventory_by_item"
    title = _("inventory by item")
    tooltip = _("Display the items with the highest inventory value")
    asynchronous = True
    limit = 20

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    javascript = """
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
      .ticks(Math.min(Math.floor((svgrectangle['height'] - 20) / 20), 8))
      .orient("left")
      .tickFormat(d3.format("s"));
    d3.select("#invByItem")
      .append("g")
      .attr("transform", "translate(" + margin + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);
    """

    @classmethod
    def render(cls, request):
        with connections[request.database].cursor() as cursor:
            limit = int(request.GET.get("limit", cls.limit))
            result = [
                '<svg class="chart" id="invByItem" style="width:100%; height: 250px;"></svg>',
                '<table style="display:none">',
            ]
            query = """select item.name, coalesce(sum(buffer.onhand * item.cost),0)
               from buffer
               inner join item on buffer.item_id = item.name
               group by item.name
               order by 2 desc
               limit %s
              """
            cursor.execute(query, (limit,))
            for res in cursor.fetchall():
                result.append("<tr><td>%s</td><td>%.2f</td></tr>" % (res[0], res[1]))
            result.append("</table>")
            return HttpResponse("\n".join(result))


Dashboard.register(InventoryByItemWidget)


class DeliveryPerformanceWidget(Widget):
    name = "delivery_performance"
    title = _("delivery performance")
    tooltip = _(
        "Shows the percentage of demands that are planned to be shipped completely on time"
    )
    permissions = (("view_demand", "Can view sales order"),)
    asynchronous = True
    green = 90
    yellow = 80

    def args(self):
        return "?%s" % urlencode({"green": self.green, "yellow": self.yellow})

    javascript = """
    var val = parseFloat($('#otd_value').html());
    var green = parseInt($('#otd_green').html());
    var yellow = parseInt($('#otd_yellow').html());
    new Gauge("otd", {
      size: 120, label: $('#otd_label').html(), min: 0, max: 100, minorTicks: 5,
      greenZones: [{from: green, to: 100}], yellowZones: [{from: yellow, to: green}],
      value: val
      }).render();
    """

    @classmethod
    def render(cls, request):
        green = int(request.GET.get("green", cls.green))
        yellow = int(request.GET.get("yellow", cls.yellow))
        GridReport.getBuckets(request)
        query = (
            """
            select case when count(*) = 0 then 0 else 100 - sum(late) * 100.0 / count(*) end
            from (
              select
                demand_id, max(case when enddate > operationplan.due then 1 else 0 end) late
              from operationplan
              inner join demand
                on operationplan.demand_id = demand.name
              where demand.due < '%s'
              group by demand_id
            ) demands
            """
            % request.report_enddate
        )
        with connections[request.database].cursor() as cursor:
            cursor.execute(query)
            val = cursor.fetchone()[0]
            result = [
                '<div style="text-align: center"><span id="otd"></span></div>',
                '<span id="otd_label" style="display:none">%s</span>'
                % force_str(_("On time delivery")),
                '<span id="otd_value" style="display:none">%s</span>' % val,
                '<span id="otd_green" style="display:none">%s</span>' % green,
                '<span id="otd_yellow" style="display:none">%s</span>' % yellow,
            ]
        return HttpResponse("\n".join(result))


Dashboard.register(DeliveryPerformanceWidget)


class InventoryEvolutionWidget(Widget):
    """
    This widget displays the on hand history (based on the archive app) and forecasted future on hand.
    """

    name = "inventory_evolution"
    title = _("Inventory evolution")
    tooltip = _("Show the history and forecasted future of the on hand")
    asynchronous = True
    history = 12

    def args(self):
        return "?%s" % urlencode({"history": self.history})

    javascript = """
    var margin_y = 50;  // Width allocated for the Y-axis
    var margin_x = 80;  // Height allocated for the X-axis
    var svg = d3.select("#inventory_evolution");
    var svgrectangle = document.getElementById("inventory_evolution").getBoundingClientRect();

    // Reduce the number of displayed points if too many
    var nb_of_ticks = (svgrectangle['width'] - margin_y - 10) / 20;


    // Collect the data
    var domain_x = [];
    var data = [];
    var max_val = 0;
    var min_val = 0;
    $("#inventory_evolution").next().find("tr").each(function() {
      var row = [];
      $("td", this).each(function() {
        if (row.length == 0) {
          domain_x.push($(this).html());
          row.push($(this).html());
        }
        else {
          var val = parseFloat($(this).html());
          row.push(val);
          if (val > max_val)
            max_val = val;
        }
      });
      data.push(row);
    });

    var visible=[]
      var step_visible = Math.ceil(domain_x.length / nb_of_ticks);
      for (let x=0; x < domain_x.length; x++){
        if (x==0 || x % step_visible == 0)
          visible.push(domain_x[x]);
      }

    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);
    var y = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([min_val - 5, max_val + 5]);

    // Draw invisible rectangles for the hoverings
    svg.selectAll("g")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + ((i) * x.rangeBand() + margin_y) + ",10)"; })
     .append("rect")
      .attr("height", svgrectangle['height'] - 10 - margin_x)
      .attr("width", x.rangeBand())
      .attr("fill-opacity", 0)
      .on("mouseover", function(d) {
        const formattedUnits = Number(d[1]).toLocaleString();
        const formattedAmount = Number(d[2]).toLocaleString();
        graph.showTooltip(d[0] + "<br>" + currency[0]
          + formattedAmount + currency[1] + "<br>" + formattedUnits + " units");
        $("#tooltip").css('background-color','black').css('color','white');
      })
      .on("mousemove", graph.moveTooltip)
      .on("mouseout", graph.hideTooltip);

    // Draw x-axis
    var xAxis = d3.svg.axis().scale(x)
        .orient("bottom").tickValues(visible);
    svg.append("g")
      .attr("transform", "translate(" + margin_y  + ", " + (svgrectangle['height'] - margin_x) +" )")
      .attr("class", "x axis")
      .call(xAxis)
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.75em")
      .attr("dy", "-.25em")
      .attr("transform", "rotate(-90)" );

    // Draw y-axis
    var yAxis = d3.svg.axis().scale(y)
        .orient("left")
        .ticks(Math.min(Math.floor((svgrectangle['height'] - margin_x - 20) / 20), 5))
        .tickFormat(d3.format("s"));
    svg.append("g")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);

    var line = d3.svg.line()
  .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
  .y(function(d) { return y(d[2]); });

    // Group data into segments with the same d[3] value
    var segments = [];
    var currentSegment = [data[0]];
    for (var i = 1; i < data.length; i++) {
      if (data[i][3] === data[i - 1][3]) {
        currentSegment.push(data[i]);
      } else {
        segments.push({ values: currentSegment, type: data[i - 1][3] });
        currentSegment = [data[i - 1], data[i]]; // duplicate the transition point
      }
    }
    segments.push({ values: currentSegment, type: currentSegment[currentSegment.length-1][3] });

    // Append each segment as a separate path with color based on d[3]
    segments.forEach(function(segment) {
      svg.append("svg:path")
        .attr("transform", "translate(" + margin_y + ", 10 )")
        .attr("class", "graphline")
        .attr("stroke", segment.type === 1 ? "#FF0000" : "#8BBA00")
        .attr("fill", "none")
        .attr("d", line(segment.values));
    });
    """

    @classmethod
    def render(cls, request):
        with connections[request.database].cursor() as cursor:
            history = int(request.GET.get("history", cls.history))
            archiveFrequency = Parameter.getValue(
                "archive.frequency", request.database, "week"
            )
            currentDate = getCurrentDate(request.database, True)
            result = [
                '<svg class="chart" id="inventory_evolution" style="width:100%; height: 100%"></svg>',
                '<table style="display:none">',
            ]
            cursor.execute(
                """
                select * from (
                (select
                  cb.startdate,
                  coalesce(sum(onhand), 0),
                  coalesce(sum(onhand * cost), 0),
                  0 as future
                from ax_manager
                inner join common_bucketdetail cb on cb.bucket_id = %s
                and cb.startdate <= snapshot_date and cb.enddate > snapshot_date
                left outer join ax_buffer
                  on snapshot_date = snapshot_date_id
                where snapshot_date < (select startdate from common_bucketdetail where bucket_id = cb.bucket_id
                                      and startdate <= %s and enddate > %s)
                group by cb.startdate
                order by cb.startdate desc
                limit %s)
                union all
                (
                with cte as(
                with buffers as
                (select distinct item_id, location_id from operationplanmaterial),
                buckets as
                (select startdate from common_bucketdetail where bucket_id = %s and enddate > %s
                and startdate < (select max(flowdate) from operationplanmaterial))
                select
                buffers.item_id,
                buffers.location_id,
                buckets.startdate,
                coalesce((select onhand
                from operationplanmaterial
                where item_id = buffers.item_id and location_id = buffers.location_id
                and flowdate < buckets.startdate order by flowdate desc, id limit 1),0) as onhand
                from buffers
                cross join buckets
                )
                select cte.startdate, sum(cte.onhand), sum(cte.onhand*coalesce(item.cost,0)), 1 as future
                from cte
                inner join item on item.name = cte.item_id
                group by cte.startdate
                )
                ) d
                order by future, startdate asc
                """,
                (
                    archiveFrequency,
                    currentDate,
                    currentDate,
                    history,
                    archiveFrequency,
                    currentDate,
                ),
            )
            for res in cursor.fetchall():
                result.append(
                    "<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td>%s</td></tr>"
                    % (
                        escape(
                            date_format(res[0], format="DATE_FORMAT", use_l10n=False)
                        ),
                        res[1],
                        res[2],
                        int(res[3]),
                    )
                )
            result.append("</table>")
            return HttpResponse("\n".join(result))


Dashboard.register(InventoryEvolutionWidget)
