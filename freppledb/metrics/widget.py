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

from django.contrib.admin.utils import quote
from django.db import connections
from django.db.models import F
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.models import UserPreference
from freppledb.common.report import getCurrency
from freppledb.input.models import Item


@Dashboard.register
class AnalysisDemandProblems(Widget):
    name = "analysis_demand_problems"
    title = _("analyze late demands")
    tooltip = _("Spot the top items with many late demands")
    permissions = (("view_demand_report", "Can view demand report"),)
    asynchronous = True
    url = "/demand/?noautofilter&sidx=latedemandvalue%20desc%2C%20latedemandquantity%20desc%2C%20latedemandcount&sord=desc"
    exporturl = True
    size = "lg"
    limit = 20
    orderby = "latedemandvalue"

    def args(self):
        return "?%s" % urlencode({"limit": self.limit, "orderby": self.orderby})

    @classmethod
    def render(cls, request=None):
        limit = int(request.GET.get("limit", cls.limit))
        orderby = request.GET.get("orderby", cls.orderby)
        currency = getCurrency()
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="text-center">%s</th>'
            '<th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("value of late demands"))),
                capfirst(force_str(_("quantity of late demands"))),
                capfirst(force_str(_("number of late demands"))),
            ),
        ]
        if orderby == "latedemandcount":
            topitems = (
                Item.objects.all()
                .using(request.database)
                .order_by("-latedemandcount", "latedemandvalue", "-latedemandquantity")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        elif orderby == "latedemandquantity":
            topitems = (
                Item.objects.all()
                .using(request.database)
                .order_by("-latedemandquantity", "latedemandvalue", "-latedemandcount")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        else:
            topitems = (
                Item.objects.all()
                .using(request.database)
                .order_by("-latedemandvalue", "-latedemandquantity", "-latedemandcount")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        alt = False
        for rec in topitems:
            result.append(
                '<tr%s><td class="text-decoration-underline"><a href="%s/buffer/item/%s/">%s</a></td>'
                '<td class="text-center">%s%s%s</td><td class="text-center">%s</td>'
                '<td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    request.prefix,
                    quote(rec.name),
                    escape(rec.name),
                    currency[0],
                    int(rec.latedemandvalue),
                    currency[1],
                    int(rec.latedemandquantity),
                    rec.latedemandcount,
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))


class DeliveryPerformanceWidget(Widget):
    name = "delivery_performance"
    title = _("delivery performance")
    tooltip = _(
        "Shows the percentage of demands that are planned to be shipped completely on time"
    )
    permissions = (("view_demand", "Can view sales order"),)
    asynchronous = True
    size = "sm"

    javascript = """
        var chart_type = "count";
        var include_fcst = false;

        $("#deliveryPerformanceDropdown a").on("click", function(event) {
            event.preventDefault();
            var selection = $(this).text().toLowerCase();
            $("#deliveryPerformanceChoice span").text(selection);
            include_fcst = (selection == "orders") ? false: true;
            draw();
        });

        function draw() {
            var delivery_data = include_fcst ? [
                { category: "ontime_so", label: "on-time orders", value: 0, count: 0, quantity: 0, cost: 0, color: "#8bba00" },
                { category: "ontime_fcst", label: "on-time forecast", value: 0, count: 0, quantity: 0, cost: 0, color: "#c4dc7d" },
                { category: "late_so", label: "late orders", value: 0, count: 0, quantity: 0, cost: 0, color: "#FFA500" },
                { category: "late_fcst", label: "late forecast", value: 0, count: 0, quantity: 0, cost: 0, color: "#FFD17D" },
                { category: "unplanned_so", label: "unplanned orders", value: 0, count: 0, quantity: 0, cost: 0, color: "#FF0000" },
                { category: "unplanned_fcst", label: "unplanned forecast", value: 0, count: 0, quantity: 0, cost: 0, color: "#FF9797" }
            ] : [
                { category: "ontime_so", label: "on-time orders", value: 0, count: 0, quantity: 0, cost: 0, color: "#8bba00" },
                { category: "late_so", label: "late orders", value: 0, count: 0, quantity: 0, cost: 0, color: "#FFA500" },
                { category: "unplanned_so", label: "unplanned orders", value: 0, count: 0, quantity: 0, cost: 0, color: "#FF0000" }
            ] ;

            // Collect data
            $("#deliveryPerformanceData td").each(function(i, e) {
                var el = $(e);
                var category = el.closest("tr").attr("data-category");
                var metric = el.attr("data-metric");
                for (var e of delivery_data) {
                    if (e.category == category) {
                        if (metric == chart_type) e.value = Number(el.text());
                        if (metric == "count") e.count = Number(el.text());
                        if (metric == "quantity") e.quantity = Number(el.text());
                        if (metric == "cost") e.cost = Number(el.text());
                    }
                }
            });

            // Remove empty cells
            delivery_data = delivery_data.filter(function(row) {return row.value > 0;});
            const total = d3.sum(delivery_data, d => d.value);

            // Clear previous chart
            d3.select('#deliveryPerformanceChart').selectAll("*").remove();

            // Pie chart
            const width = 350;
            const height = 350;
            const radius = Math.min(width, height) / 2;
            const svg = d3.select('#deliveryPerformanceChart')
                .attr('width', width)
                .attr('height', height)
                .append('g')
                .attr('transform', `translate(${width / 2}, ${height / 2})`);
            var color = d3.scale.category10()
                .domain(delivery_data.map(function(d) { return d.category; }));
            const pie = d3.layout.pie()
                .sort(null)
                .startAngle(Math.PI / 2) // Starts at 90 degrees (3 o'clock)
                .endAngle(Math.PI * 2.5) // Must also offset the end angle (2.5 * PI)
                .value(d => d.value);
            const arc = d3.svg.arc()
                .innerRadius(0)
                .outerRadius(radius);
            const slices = svg.selectAll('path')
                .data(pie(delivery_data))
                .enter()
                .append('path')
                .attr('d', arc)
                .attr('fill', d => d.data.color)
                .attr('stroke', 'white')
                .style('stroke-width', '2px')
                .on("mouseover", function(d) {

                    graph.showTooltip(
                        '<span class="text-strong">' + d.data.label + "</span>"
                        + "<br>count: "
                        + + d.data.count.toLocaleString('en-US', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 2  // Round to 2 places if decimals exist
                          })
                        + "<br>quantity: "
                        + d.data.cost.toLocaleString('en-US', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 2  // Round to 2 places if decimals exist
                          })
                        + (d.data.cost ? "<br>cost: "
                        + d.data.cost.toLocaleString('en-US', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 2  // Round to 2 places if decimals exist
                          })
                        + currency[1] : "")
                        );
                    $("#tooltip").css('background-color','black').css('color','white');
                })
                .on("mousemove", graph.moveTooltip)
                .on("mouseout", graph.hideTooltip);
            svg.selectAll('text')
                .data(pie(delivery_data))
                .enter()
                .append('text')
                .attr('transform', function(d) {
                    var center = arc.centroid(d);
                    var rotation = ((d.startAngle + d.endAngle) / 2 * 180 / Math.PI) - 90;
                    if (rotation > 90 && rotation <= 270)
                    // Flip text 180 degrees if it's on the bottom half so it's not upside down
                    rotation += 180;
                    return `translate(${center[0] * 1.8},${center[1] * 1.8}) rotate(${rotation})`;
                    })
                .style('text-anchor', function(d){
                    // Depends whether we are left of right in the chart
                    var rotation = ((d.startAngle + d.endAngle) / 2 * 180 / Math.PI) - 90;
                    return (rotation <= 90 || rotation > 270) ? 'end' : 'start';
                })
                .attr('dy', '.35em')
                .text(d => {
                    const perc = ((d.data.value / total) * 100).toFixed(1);
                    return `${d.data.label} ${perc}%`;
                })
                .attr('class', 'text-capitalize text-body-inverted');
        }
        draw();
        """

    @classmethod
    def render(cls, request):
        result = [
            '<div class="d-flex justify-content-center align-items-center h-100 position-relative">',
            '<svg id="deliveryPerformanceChart"></svg>'
            '<div class="dropdown position-absolute top-0 end-0 m-3">',
            '<button id="deliveryPerformanceChoice" class="form-select form-select-sm d-inline-block w-auto text-capitalize" type="button" data-bs-toggle="dropdown" aria-expanded="false">',
            "<span>orders</span>",
            "</button>",
            '<ul id="deliveryPerformanceDropdown" class="dropdown-menu w-auto" style="min-width: unset" aria-labelledby="fcst_selectButton">',
            '<li><a class="dropdown-item text-capitalize">orders</a></li>',
            '<li><a class="dropdown-item text-capitalize">orders and forecast</a></li>',
            "</ul>",
            "</div>",
            '<div id="deliveryPerformanceData"class="d-none"><table>',
        ]
        try:
            for cat, kv in (
                UserPreference.objects.using(request.database)
                .get(property="widget.deliveryperformance")
                .value.items()
            ):
                result.append(f'<tr data-category="{cat}">')
                for k, v in kv.items():
                    result.append(f'<td data-metric="{k}">{v}</td>')
                result.append("</tr>")
        except UserPreference.DoesNotExist:
            pass
        result.append("</table></div></div>")
        return HttpResponse("\n".join(result))


Dashboard.register(DeliveryPerformanceWidget)
