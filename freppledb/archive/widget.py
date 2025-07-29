#
# Copyright (C) 2020 by frePPLe bv
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

from urllib.parse import urlencode

from django.db import connections
from django.http import HttpResponse
from django.utils.formats import date_format
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from freppledb.common.dashboard import Dashboard, Widget


class ArchivedDemandWidget(Widget):
    """
    This widget displays the total demand history based on the archived tables.
    """

    name = "archived_demand"
    title = _("Demand history")
    tooltip = _("Show the evolution of the open sales orders")
    asynchronous = True
    history = 12

    def args(self):
        return "?%s" % urlencode({"history": self.history})

    javascript = """
    var margin_y = 50;  // Width allocated for the Y-axis
    var margin_x = 80;  // Height allocated for the X-axis
    var svg = d3.select("#archivedemand");
    var svgrectangle = document.getElementById("archivedemand").getBoundingClientRect();

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_val = 0;
    var min_val = 0;
    $("#archivedemand").next().find("tr").each(function() {
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

    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);
    var x_width = (svgrectangle['width'] - margin_y - 10) / data.length;
    var y = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([min_val - 5, max_val + 5]);
    var y_zero = y(0);

    var bar = svg.selectAll("g")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + ((i) * x.rangeBand() + margin_y) + ",10)"; });

    // Draw the overdue orders
    bar.append("rect")
      .attr("x", 2)
      .attr("y", function(d) {return y(d[4]);})
      .attr("height", function(d) {return y_zero - y(d[4]);})
      .attr("rx","1")
      .attr("width", x_width - 2)
      .style("fill", "#FFC000");

    // Draw invisible rectangles for the hoverings
    bar.append("rect")
      .attr("height", svgrectangle['height'] - 10 - margin_x)
      .attr("width", x.rangeBand())
      .attr("fill-opacity", 0)
      .on("mouseover", function(d) {
        graph.showTooltip(
          d[0] + "<br>"
          + currency[0] + d[2] + currency[1] + "open<br>"
          + d[1] + " units open<br>"
          + currency[0] + d[4] + currency[1] + " overdue<br>"
          + d[3] + " units overdue"
        );
        $("#tooltip").css('background-color','black').css('color','white');
      })
      .on("mousemove", graph.moveTooltip)
      .on("mouseout", graph.hideTooltip);

    // Draw x-axis
    var xAxis = d3.svg.axis().scale(x)
        .orient("bottom");
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

    // Draw the line
    var line = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y(d[2]); });

    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#8BBA00")
      .attr("d", line(data));
    """

    @classmethod
    def render(cls, request):
        with connections[request.database].cursor() as cursor:
            history = int(request.GET.get("history", cls.history))
            result = [
                '<svg class="chart" id="archivedemand" style="width:100%; height: 100%"></svg>',
                '<table style="display:none">',
            ]
            cursor.execute(
                """
                select * from (
                select
                  snapshot_date,
                  coalesce(sum(quantity), 0),
                  coalesce(sum(quantity*cost), 0),
                  coalesce(sum(case when due < snapshot_date_id then quantity end), 0),
                  coalesce(sum(case when due < snapshot_date_id then quantity * cost end), 0)
                from ax_manager
                left outer join ax_demand
                  on snapshot_date = snapshot_date_id
                group by snapshot_date
                order by snapshot_date desc
                limit %s
                ) d
                order by snapshot_date asc
                """,
                (history,),
            )
            for res in cursor.fetchall():
                result.append(
                    "<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td>%.1f</td><td>%.1f</td></tr>"
                    % (
                        escape(
                            date_format(res[0], format="DATE_FORMAT", use_l10n=False)
                        ),
                        res[1],
                        res[2],
                        res[3],
                        int(res[4]),
                    )
                )
            result.append("</table>")
            return HttpResponse("\n".join(result))


Dashboard.register(ArchivedDemandWidget)


class ArchivedPurchaseOrderWidget(Widget):
    """
    This widget displays the total purchase order history based on the archived tables.
    """

    name = "archived_purchase_order"
    title = _("Purchase order history")
    tooltip = _("Show the evolution of the open purchase orders")
    asynchronous = True
    history = 12

    def args(self):
        return "?%s" % urlencode({"history": self.history})

    javascript = """
    var margin_y = 50;  // Width allocated for the Y-axis
    var margin_x = 80;  // Height allocated for the X-axis
    var svg = d3.select("#archivepurchaseorder");
    var svgrectangle = document.getElementById("archivepurchaseorder").getBoundingClientRect();

    // Collect the data
    var domain_x = [];
    var data = [];
    var max_val = 0;
    var min_val = 0;
    $("#archivepurchaseorder").next().find("tr").each(function() {
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

    var x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, svgrectangle['width'] - margin_y - 10], 0);
    var x_width = (svgrectangle['width'] - margin_y - 10) / data.length;
    var y = d3.scale.linear()
      .range([svgrectangle['height'] - margin_x - 10, 0])
      .domain([min_val - 5, max_val + 5]);
    var y_zero = y(0);

    var bar = svg.selectAll("g")
     .data(data)
     .enter()
     .append("g")
     .attr("transform", function(d, i) { return "translate(" + ((i) * x.rangeBand() + margin_y) + ",10)"; });

    // Draw the overdue orders
    bar.append("rect")
      .attr("x", 2)
      .attr("y", function(d) {return y(d[4]);})
      .attr("height", function(d) {return y_zero - y(d[4]);})
      .attr("rx","1")
      .attr("width", x_width - 2)
      .style("fill", "#FFC000");

    // Draw invisible rectangles for the hoverings
    bar.append("rect")
      .attr("height", svgrectangle['height'] - 10 - margin_x)
      .attr("width", x.rangeBand())
      .attr("fill-opacity", 0)
      .on("mouseover", function(d) {
        graph.showTooltip(
          d[0] + "<br>"
          + currency[0] + d[2] + currency[1] + "open<br>"
          + d[1] + " units open<br>"
          + currency[0] + d[4] + currency[1] + " overdue<br>"
          + d[3] + " units overdue"
        );
        $("#tooltip").css('background-color','black').css('color','white');
      })
      .on("mousemove", graph.moveTooltip)
      .on("mouseout", graph.hideTooltip);

    // Draw x-axis
    var xAxis = d3.svg.axis().scale(x)
        .orient("bottom");
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

    // Draw the line
    var line = d3.svg.line()
      .x(function(d) { return x(d[0]) + x.rangeBand() / 2; })
      .y(function(d) { return y(d[2]); });

    svg.append("svg:path")
      .attr("transform", "translate(" + margin_y + ", 10 )")
      .attr('class', 'graphline')
      .attr("stroke","#8BBA00")
      .attr("d", line(data));
    """

    @classmethod
    def render(cls, request):
        with connections[request.database].cursor() as cursor:
            history = int(request.GET.get("history", cls.history))
            result = [
                '<svg class="chart" id="archivepurchaseorder" style="width:100%; height: 100%"></svg>',
                '<table style="display:none">',
            ]
            cursor.execute(
                """
            select * from (
            select
              snapshot_date,
              coalesce(sum(quantity), 0),
              coalesce(sum(quantity * item_cost), 0),
              coalesce(sum(case when enddate < snapshot_date_id then quantity end), 0),
              coalesce(sum(case when enddate < snapshot_date_id then quantity * item_cost end), 0)
            from ax_manager
            left outer join ax_operationplan
              on snapshot_date = snapshot_date_id
              and type = 'PO'
            group by snapshot_date
            order by snapshot_date desc
            limit %s
            ) d
            order by snapshot_date
            """,
                (history,),
            )
            for res in cursor.fetchall():
                result.append(
                    "<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td>%.1f</td><td>%.1f</td></tr>"
                    % (
                        escape(
                            date_format(res[0], format="DATE_FORMAT", use_l10n=False)
                        ),
                        res[1],
                        res[2],
                        res[3],
                        res[4],
                    )
                )
            result.append("</table>")
            return HttpResponse("\n".join(result))


Dashboard.register(ArchivedPurchaseOrderWidget)
