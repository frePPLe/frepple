#
# Copyright (C) 2023 by frePPLe bv
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

from urllib.parse import urlencode, quote

from django.db import connections
from django.http import HttpResponse
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.models import Parameter
from freppledb.common.report import getCurrentDate


class ForecastWidget(Widget):
    """
    Forecast overview graph
    """

    name = "forecast"
    title = _("forecast")
    tooltip = _("Show the value of all sales order and forecast")
    permissions = (("view_forecast_report", "Can view forecast report"),)
    asynchronous = True
    history = 12
    future = 12

    def args(self):
        return "?%s" % urlencode({"history": self.history, "future": self.future})

    javascript = r"""


    // Collect the data
    var domain_x = [];
    var data = [];
    var max_val = 0;
    var max_length = 0;

    function getData(d) {

	// Reset variables on redraw
    domain_x = [];
    data = [];
    max_val = 0;
    max_length = 0;

    $("#forecast").next().find("tr").each(function(idx) {
      var name = $(this).children('td').first();
      var fcstvalue = name.next();
      var orderstotalvalue = fcstvalue.next();
      var ordersopenvalue = orderstotalvalue.next();
      var fcst = ordersopenvalue.next();
      var orderstotal = fcst.next();
      var ordersopen = orderstotal.next();
      var el = [];
      if (d==="value")
        el = [name.text(), parseFloat(fcstvalue.text()), parseFloat(orderstotalvalue.text()), parseFloat(ordersopenvalue.text())];
      else
        el = [name.text(), parseFloat(fcst.text()), parseFloat(orderstotal.text()), parseFloat(ordersopen.text())];
      data.push(el);
      domain_x.push(el[0]);
      if (el[0].length > max_length)
            max_length = el[0].length;

      if (el[1] > max_val) max_val = el[1];
      if (el[2] > max_val) max_val = el[2];
      if (el[3] > max_val) max_val = el[3];
      });
    }


    // List of groups
    var allGroup = ["value", "unit"]

    // add the options to the button
    d3.select("#fcst_selectButton")
      .selectAll('myOptions')
     	.data(allGroup)
      .enter()
    	.append('option')
      .text(function (d) { return d; }) // text showed in the menu
      .attr("value", function (d) { return d; }) // corresponding value returned by the button

    getData("value");

    var margin_y = 50;  // Width allocated for the Y-axis
    var margin_x = 9 * max_length;  // Height allocated for the X-axis
    var svg = d3.select("#forecast");
    var svgrectangle = document.getElementById("forecast").getBoundingClientRect();

    // Reduce the number of displayed points if too many
    var nb_of_ticks = (svgrectangle['width'] - margin_y - 10) / 20;

    function draw() {

      var visible=[]
      var step_visible = Math.ceil(domain_x.length / nb_of_ticks);
      for (let x=0; x < domain_x.length; x++){
        if (x==0 || x % step_visible == 0)
          visible.push(domain_x[x]);
      }

      // Define axis
      var x = d3.scale.ordinal()
        .domain(domain_x)
        .rangeBands([0, svgrectangle['width'] - margin_y - 10], 0);
      var x_width = (svgrectangle['width'] - margin_y - 10) / data.length;
      var y = d3.scale.linear()
        .range([svgrectangle['height'] - margin_x - 10, 0])
        .domain([0, max_val]);
      var y_zero = y(0);

      var bar = svg.selectAll("g")
      .data(data)
      .enter()
      .append("g")
      .attr('id','fcst_bar')
      .attr("transform", function(d, i) { return "translate(" + ((i) * x.rangeBand() + margin_y) + ",10)"; });

      // Draw x-axis
      var xAxis = d3.svg.axis().scale(x)
          .orient("bottom").tickValues(visible);

      svg.append("g")
        .attr("transform", "translate(" + margin_y  + ", " + (svgrectangle['height'] - margin_x) +" )")
        .attr("class", "x axis")
        .attr( 'id', 'fcst_xaxis' )
        .call(xAxis)
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.75em")
        .attr("dy", "-.25em")
        .attr("transform", "rotate(-90)" );

      // Draw y-axis
      var yAxis = d3.svg.axis().scale(y)
          .orient("left")
          .ticks(Math.min(Math.floor((svgrectangle['height'] - margin_x - 10) / 20), 5))
          .tickFormat(d3.format("s"));
      svg.append("g")
        .attr("transform", "translate(" + margin_y + ", 10 )")
        .attr("class", "y axis")
        .attr( 'id', 'fcst_yaxis' )
        .call(yAxis);

      // Draw the closed orders
      bar.append("rect")
        .attr("x", 2)
        .attr("y", function(d) {return y(d[2]-d[3]);})
        .attr("height", function(d) {return y_zero - y(d[2]-d[3]);})
        .attr("rx","1")
        .attr("width", Math.max(1, x_width - 2))
        .style("fill", "#828915");

      // Draw the open orders
      bar.append("rect")
        .attr("x", 2)
        .attr("y", function(d) {return y(d[2]);})
        .attr("height", function(d) {return y(d[2] - d[3]) - y(d[2]);})
        .attr("rx","1")
        .attr("width", Math.max(1, x_width - 2))
        .style("fill", "#FFC000");

      // Draw invisible rectangles for the hoverings
      bar.append("rect")
        .attr("height", svgrectangle['height'] - 10 - margin_x)
        .attr("width", x.rangeBand())
        .attr("fill-opacity", 0)
        .on("mouseover", function(d) {
          graph.showTooltip(
            d[0]
            + "<br>"
            + (d3.select("#fcst_selectButton").property("value") == "value" ? currency[0]:"")
            + d[1].toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            + " "
            + (d3.select("#fcst_selectButton").property("value") == "value" ? currency[1]:"units")
            + " forecast<br>"
            + (d3.select("#fcst_selectButton").property("value") == "value" ? currency[0]:"")
            + (d[2]-d[3]).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            + " "
            + (d3.select("#fcst_selectButton").property("value") == "value" ? currency[1]:"units")
            + " closed sales orders<br>"
            + (d3.select("#fcst_selectButton").property("value") == "value" ? currency[0]:"")
            + d[3].toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            + " "
            + (d3.select("#fcst_selectButton").property("value") == "value" ? currency[1]:"units")
            + " open sales orders");
          $("#tooltip").css('background-color','black').css('color','white');
          })
        .on("mousemove", graph.moveTooltip)
        .on("mouseout", graph.hideTooltip);

      // Draw the forecast line
      var line = d3.svg.line()
        .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
        .y(function(d) { return y(d[1]); });

      svg.append("svg:path")
        .attr("transform", "translate(" + margin_y + ", 10 )")
        .attr('class', 'graphline')
        .attr('id','fcst_line')
        .attr("stroke","#8BBA00")
        .attr("d", line(data));
    }
    draw();


    // When the button is changed, update data and redraw()
    d3.select("#fcst_selectButton").on("change", function(d) {
        // recover the option that has been chosen
        var selectedOption = d3.select(this).property("value")
        // run the updateChart function with this selected option

        d3.selectAll('#fcst_bar').remove();
        d3.selectAll('#fcst_xaxis').remove();
        d3.selectAll('#fcst_yaxis').remove();
        d3.selectAll('#fcst_line').remove();
        getData(selectedOption);

        draw();
    })
    """

    @classmethod
    def render(cls, request=None):
        cursor = connections[request.database].cursor()
        curdate = getCurrentDate(request.database, lastplan=True)
        history = int(request.GET.get("history", cls.history))
        future = int(request.GET.get("future", cls.future))

        # get the bucket from the user preferences
        bucketname = request.user.horizonbuckets or Parameter.getValue(
            "forecast.calendar", request.database
        )

        result = [
            '<select class="form-select form-select-sm d-inline-block w-auto" id="fcst_selectButton"></select>',
            '<svg class="chart" id="forecast" style="width:100%; height: 100%"></svg>',
            '<table style="display:none">',
        ]
        cursor.execute(
            """
            select
              common_bucketdetail.name,
              round(sum(greatest((value->>'forecasttotalvalue')::numeric,0))) as fcstvalue,
              round(sum(greatest(0,
                (value->>'orderstotalvalue')::numeric +
                coalesce((value->>'ordersadjustmentvalue')::numeric,0)
                ))) as orderstotalvalue,
              round(sum(greatest((value->>'ordersopenvalue')::numeric,0))) as ordersopenvalue,
              round(sum(greatest((value->>'forecasttotal')::numeric,0))) as fcst,
              round(sum(greatest(0,
                (value->>'orderstotal')::numeric +
                coalesce((value->>'ordersadjustment')::numeric,0)
                ))) as orderstotal,
              round(sum(greatest((value->>'ordersopen')::numeric,0))) as ordersopen
            from common_bucketdetail
            left outer join forecastplan
              on item_id = (select name from item where item.lvl = 0 limit 1)
              and location_id = (select name from location where location.lvl = 0 limit 1)
              and customer_id = (select name from customer where customer.lvl = 0 limit 1)
              and common_bucketdetail.startdate <= forecastplan.startdate
              and forecastplan.startdate < common_bucketdetail.enddate
            where
              common_bucketdetail.bucket_id = %s
              and common_bucketdetail.startdate < %s + interval '%s month'
              and common_bucketdetail.startdate > %s - interval '%s month'
              and common_bucketdetail.startdate >= (
                select min(startdate) from forecastplan
              )
            group by common_bucketdetail.name, common_bucketdetail.startdate
            order by common_bucketdetail.startdate
            """,
            (bucketname, curdate, future, curdate, history),
        )
        for res in cursor.fetchall():
            result.append(
                '<tr><td class="name">%s</td><td>%.1f</td><td>%.1f</td><td>%.1f</td><td>%.1f</td><td>%.1f</td><td>%.1f</td></tr>'
                % (escape(res[0]), res[1], res[2], res[3], res[4], res[5], res[6])
            )
        result.append("</table>")
        return HttpResponse("\n".join(result))


Dashboard.register(ForecastWidget)


class ForecastAccuracyWidget(Widget):
    """
    Calculate the Symmetric Mean Percentage Error (aka SMAPE)
    for all forecasts.
    The result is aggregated per bucket, weighted by the
    forecast quantity.

    This widget considers the forecast accuracy at the level of the planned
    forecasts. Some customers may prefer to measure the error at a different
    level.
    """

    name = "forecast_error"
    title = _("Forecast error")
    tooltip = _("Show the evolution of the SMAPE forecast error")
    permissions = (("view_forecast_report", "Can view forecast report"),)
    asynchronous = True
    history = 12

    def args(self):
        return "?%s" % urlencode({"history": self.history})

    javascript = """
    var margin_y = 30;  // Width allocated for the Y-axis
    var margin_x = 60;  // Height allocated for the X-axis
    var svg = d3.select("#forecast_error");
    var svgrectangle = document.getElementById("forecast_error").getBoundingClientRect();

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_error = 0;
    var min_error = 200;
    $("#forecast_error").next().find("tr").each(function() {
      var nm = $(this).find("td.name").html();
      var val = parseFloat($(this).find("td.val").html());
      domain_x.push(nm);
      data.push( [nm, val] );
      if (val > max_error)
        max_error = val;
      if (val < min_error)
        min_error = val;
      });

    // Reduce the number of displayed points if too many
    var nb_of_ticks = (svgrectangle['width'] - margin_y - 10) / 20;
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
      .domain([min_error - 5, max_error + 5]);

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
        graph.showTooltip(d[0] + " " + d[1] + "%");
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
        .ticks(Math.min(Math.floor((svgrectangle['height'] - 10 - margin_x) / 20), 5))
        .tickFormat(d3.format(".0f%"));
    svg.append("g")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr("class", "y axis")
      .call(yAxis);

    // Draw the line
    var line = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y(d[1]); });

    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#8BBA00")
      .attr("d", line(data));
    """

    @classmethod
    def render(cls, request=None):
        cursor = connections[request.database].cursor()
        curdate = getCurrentDate(request.database, lastplan=True)
        history = int(request.GET.get("history", cls.history))
        result = [
            '<svg class="chart" id="forecast_error" style="width:100%; height: 100%"></svg>',
            '<table style="display:none">',
        ]
        cursor.execute(
            """
            select
              common_bucketdetail.name,
              100 * sum( fcst * abs(fcst - orders) / abs(fcst + orders) * 2) / greatest(sum(fcst),1)
            from
              (
              select
                startdate,
                greatest((value->>'forecasttotal')::numeric,0) fcst,
                greatest((value->>'orderstotal')::numeric + coalesce((value->>'ordersadjustment')::numeric,0),0) orders
              from forecastplan
              inner join forecast
                on forecastplan.item_id = forecast.item_id
                and forecastplan.location_id = forecast.location_id
                and forecastplan.customer_id = forecast.customer_id
                and forecast.planned = true
              where startdate < %s
                and startdate > %s - interval '%s month'
              ) recs
            inner join common_parameter
              on common_parameter.name = 'forecast.calendar'
            inner join common_bucketdetail
              on common_bucketdetail.bucket_id = common_parameter.value
              and common_bucketdetail.startdate = recs.startdate
            where fcst > 0 or orders > 0
            group by common_bucketdetail.name, recs.startdate
            order by recs.startdate
            """,
            (curdate, curdate, history),
        )
        for res in cursor.fetchall():
            result.append(
                '<tr><td class="name">%s</td><td class="val">%.1f</td></tr>'
                % (escape(res[0]), res[1])
            )
        result.append("</table>")
        return HttpResponse("\n".join(result))


Dashboard.register(ForecastAccuracyWidget)


class OutliersWidget(Widget):
    name = "outliers"
    title = _("Demand history outliers")
    tooltip = _("Displays outliers detected in the demand history")
    permissions = (("view_problem_report", "Can view problem report"),)
    asynchronous = True
    url = "/problem/?name=outlier"
    exporturl = True
    limit = 20

    query = """
        select
          forecast.item_id, forecast.location_id, forecast.customer_id,
          date(startdate), weight, forecast.name
        from out_problem
        inner join forecast on forecast.name = (regexp_split_to_array(out_problem.owner, E' - '))[1]
        where out_problem.entity = 'forecast' and out_problem.name = 'outlier' limit %s
        """

    def args(self):
        return "?%s" % urlencode({"limit": self.limit})

    @classmethod
    def render(cls, request=None):
        limit = int(request.GET.get("limit", cls.limit))
        cursor = connections[request.database].cursor()
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("location"))),
                capfirst(force_str(_("customer"))),
                capfirst(force_str(_("date"))),
                capfirst(force_str(_("quantity"))),
            ),
        ]
        alt = False
        cursor.execute(cls.query % limit)
        for rec in cursor.fetchall():
            result.append(
                '<tr%s><td class="alignleft">%s</td><td class="alignleft">%s</td><td class="alignleft">%s</td><td class="alignleft">%s</td><td class="text-decoration-underline"><a href="%s/forecast/editor/%s/">%s</a></td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    escape(rec[0]),
                    escape(rec[1]),
                    escape(rec[2]),
                    rec[3],
                    request.prefix,
                    quote(rec[0], safe="/"),
                    int(rec[4]),
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(OutliersWidget)
