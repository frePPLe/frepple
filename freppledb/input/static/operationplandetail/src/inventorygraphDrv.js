/*
 * Copyright (C) 2024 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 *
 */

'use strict';

angular.module('operationplandetailapp')
  .directive('showinventorygraphDrv', showinventorygraphDrv);

showinventorygraphDrv.$inject = ['$window', '$filter', 'gettextCatalog', 'd3service'];

function showinventorygraphDrv($window, $filter, gettextCatalog) {
  return {
    restrict: 'EA', scope: {operationplan: '=data'}, link: linkfunc
  };

  function linkfunc(scope, elem, attrs, d3service) {
    let template = [
      '<div class="card-header">',
      '<h5 class="card-title text-capitalize">' + gettextCatalog.getString("inventory") + '</h5></div>',
      '<div class="card-body">',
      '<table class="table table-sm table-borderless">',
      '<thead id="grid_graph"></thead>',
      '<tbody><tr><td role="gridcell" aria-describedby="grid_graph">',
      '<div class="graph" style="height:'+ $("#attributes-operationplan .card-body").height() +'"></div>',
      '</td></tr></tbody>',
      '</table>',
      '</div>'];

    scope.$watchGroup(['operationplan.id', 'operationplan.inventoryreport.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-inventorygraph').empty().append(template.join("\n"));
      let domain_x = [];

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('inventoryreport')) {
          const timebuckets = scope.operationplan.inventoryreport;

          let margin = {top: 10, right: 10, bottom: 0, left: 40};
          let width = Math.max($("#attributes-operationplan .card-body").width() - margin.left - margin.right, 0);
          let height = $("#attributes-operationplan .card-body").height() - margin.top - margin.bottom;

          // Define X-axis
          let bucketnamelength = 0;
          for (let i of timebuckets) {
            domain_x.push(i[0]);
            bucketnamelength = Math.max(i[0].length, bucketnamelength);
          }
          let x = d3.scale.ordinal()
            .domain(domain_x)
            .rangeRoundBands([0, width], 0);
          let x_width = x.rangeBand();

          // // Build the data for d3
          let max_y = 0;
          let min_y = 0;
          let data = [];          
          for (const bctk of timebuckets) {
            data.push({
              'bucket': bctk[0],
              'startinv': bctk[4],
              'safetystock': bctk[5],
              'consumed_total': bctk[6],
              'consumed_proposed': bctk[7],
              'consumed_confirmed': bctk[8],
              'produced_total': bctk[9],
              'produced_proposed': bctk[10],
              'produced_confirmed': bctk[11],
              'endinv': bctk[12],
              });

            //slice the first 4 strings from array to determine min and max
            let slicedbucket = bctk.slice(4 - bctk.length);
            var tmp = Math.min(...slicedbucket);
            if (tmp < min_y) min_y = tmp;
            tmp = Math.max(...slicedbucket);
            if (tmp > max_y) max_y = tmp;
          }

          // Define Y-axis
          let y = d3.scale.linear().rangeRound([height, 0]);

          // Create a new SVG element
          $($(".graph").get(0)).html("");
          let svg = d3.select($(".graph").get(0))
            .append("svg")
            .attr("class", "graphcell")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

          // Update the scale of the Y-axis by looking for the max value
          y.domain([min_y, max_y, data]);
          let y_zero = y(0);

          // Draw the bars
          let y_top, y_top_low;

          svg.selectAll("g")
            .data(data)
            .enter()
            .append("g")
            .attr("transform", function (d) {
              return "translate(" + x(d['bucket']) + ",0)";
            })
            .each(function (d) {
              let bucket = d3.select(this);
              if (d['produced_total'] > 0) {
                y_top = y(d['produced_total']);
                y_top_low = y(d['produced_confirmed']);
                if (d['produced_confirmed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_zero - y_top_low)
                  .attr("x", x_width / 2)
                  .attr("y", y_top_low)
                  .style("fill", "#113C5E");
                if (d['produced_proposed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_top_low - y_top)
                  .attr("x", x_width / 2)
                  .attr("y", y_top)
                  .style("fill", "#2B95EC");
              }
              if (d['consumed_total'] > 0) {
                y_top = y(d['consumed_total']);
                y_top_low = y(d['consumed_confirmed']);
                if (d['consumed_confirmed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_zero - y_top_low)
                  .attr("y", y_top_low)
                  .style("fill", "#7B5E08");
                if (d['consumed_proposed'] > 0) bucket.append("rect")
                  .attr("width", x_width / 2)
                  .attr("height", y_top_low - y_top)
                  .attr("y", y_top)
                  .style("fill", "#F6BD0F");
              }
              bucket.append("rect")
                .attr("height", height)
                .attr("width", x_width)
                .attr("fill-opacity", function (d) {
                  if (d["startinv"] >= 0 && (d["startinv"] >= d["safetystock"] || d["safetystock"] === 0)) return 0; else return 0.2;
                })
                .attr("fill", function (d) {
                  let gradient_idx = undefined;
                  if (d["startinv"] < 0) gradient_idx = 0; else if (d["startinv"] >= d["safetystock"] || d["safetystock"] === 0) return null; else gradient_idx = Math.round(d["startinv"] / d["safetystock"] * 165);
                  let grad = d3.selectAll("#gradient_" + gradient_idx);
                  if (grad.size() === 0) {
                    let newgrad = d3.select("#gradients")
                      .append("linearGradient")
                      .attr("id", "gradient_" + gradient_idx)
                      .attr("x1", 0)
                      .attr("x2", 0)
                      .attr("y1", 0)
                      .attr("y2", 1);
                    newgrad.append("stop")
                      .attr("offset", "0%")
                      .attr("stop-color", "white")
                      .attr("stop-opacity", 1);
                    newgrad.append("stop")
                      .attr("offset", "40%")
                      .attr("stop-color", "rgb(255," + gradient_idx + ",0)")
                      .attr("stop-opacity", 1);
                    newgrad.append("stop")
                      .attr("offset", "60%")
                      .attr("stop-color", "rgb(255," + gradient_idx + ",0)")
                      .attr("stop-opacity", 1);
                    newgrad.append("stop")
                      .attr("offset", "100%")
                      .attr("stop-color", "white")
                      .attr("stop-opacity", 0);
                  }
                  return "url(#gradient_" + gradient_idx + ")";
                })
                .on("click", function (d) {
                  if (d3.event.defaultPrevented || (d['produced_total'] === 0 && d['consumed_total'] === 0)) return;
                  d3.select("#tooltip").style('display', 'none');

                  window.location = url_prefix + "/data/input/operationplanmaterial/buffer/" + admin_escape(d['buffer']) + "/?noautofilter&flowdate__gte=" + timebuckets[d['bucket']]['startdate'] + "&flowdate__lt=" + timebuckets[d['bucket']]['enddate'];

                  d3.event.stopPropagation();
                })
                .on("mouseenter", function (d) {
                  let tiptext = [];
                  if (d['history']) {
                    tiptext = [
                      '<div style="text-align:center; font-style:italic">',
                      gettextCatalog.getString('Archived'),
                      d['bucket'],
                      '</div><table><tr><td class="text-capitalize">',
                      gettextCatalog.getString('start inventory'),
                      '</td><td style="text-align:right">',
                      $filter("number")(d['startinv']),
                      '</td></tr><tr><td class="text-capitalize">',
                      gettextCatalog.getString('safety stock'),
                      '</td><td style="text-align:right">',
                      $filter("number")(d['safetystock']),
                      '</td></tr></table>'
                    ].join("\n");
                  } else {
                    tiptext = [
                      '<div style="text-align:center; font-weight:bold">',
                      d['bucket'],
                      '</div><table><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('start inventory'),
                      '</td><td class="text-end">',
                      $filter('number')(d['startinv']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('produced total'),
                      '</td><td class="text-end">+&nbsp;',
                      $filter('number')(d['produced_total']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('produced proposed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['produced_proposed']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('produced confirmed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['produced_confirmed']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('consumed total'),
                      '</td><td class="text-end">-&nbsp;',
                      $filter('number')(d['consumed_total']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('consumed proposed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['consumed_proposed']),
                      '</td></tr><tr><td class="text-capitalize pe-3 px-3">',
                      gettextCatalog.getString('consumed confirmed'),
                      '</td><td class="text-end">',
                      $filter('number')(d['consumed_confirmed']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('end inventory'),
                      '</td><td class="text-end">=&nbsp;',
                      $filter('number')(d['endinv']),
                      '</td></tr><tr><td class="text-capitalize pe-3">',
                      gettextCatalog.getString('safety stock'),
                      '</td><td class="text-end">',
                      $filter('number')(d['safetystock']),
                      '</td></tr></table>'
                    ].join("\n");
                  }
                  graph.showTooltip(tiptext);
                })
                .on("mouseleave", graph.hideTooltip)
                .on("mousemove", graph.moveTooltip)
            })
          
          // Draw axis
          var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .tickFormat(d3.format("s"));          
          svg.append("g")
            .attr("class", "miniaxis")
            .call(graph.miniAxis.bind(yAxis));

          // Draw startoh line
          var line = d3.svg.line()
            .x(function(d) { return x(d['bucket']) + x_width / 2; })
            .y(function(d) { return y(d['startinv']); });
          svg.append("svg:path")
            .attr('class', 'graphline')
            .attr("stroke","#8BBA00")
            .attr("d", line(data));

          // Draw safety stock line
          var line = d3.svg.line()
            .x(function(d) { return x(d['bucket']) + x_width / 2; })
            .y(function(d) { return y(d['safetystock']); });
          svg.append("svg:path")
            .attr('class', 'graphline')
            .attr("stroke","#FF0000")
            .attr("d", line(data));        

          // Draw header
          const el = $("#grid_graph");
          el.html("");
          const scale_stops = x.range();
          const scale_width = x.rangeBand();
          const svg_header = d3.select(el.get(0)).append("svg");
          svg_header.attr('height', '15px');
          svg_header.attr('width', Math.max(el.width(), 0));
          let wt = 0;
          for (const i in timebuckets) {
            const w = margin.left + scale_stops[i] + scale_width / 2;
            if (wt <= w) {
              const t = svg_header.append('text')
                .attr('class', timebuckets[i][3] ? 'svgheaderhistory' : 'svgheadertext')
                .attr("font-weight", 700)
                .attr('x', w)
                .attr('y', '12')
                .attr('data-bucket', i)
                .text(timebuckets[i][0])
                .on("mouseenter", function (d) {
                  graph.showTooltip(
                    $filter('formatdate')(timebuckets[i][1]) + ' - ' + $filter('formatdate')(timebuckets[i][2])
                  );
                })
                .on("mouseleave", graph.hideTooltip)
                .on("mousemove", graph.moveTooltip);
              wt = w + t.node().getComputedTextLength() + 12;
            }
          }

          let widgetTooltipTriggerList = document.querySelectorAll('#attributegraph [data-bs-toggle="tooltip"]');
          let widgetTooltipList = [...widgetTooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
      }
    })//watch end

    const graphjs = {

      header: function (margin, scale) {
        const el = $("#grid_graph");
        el.html("");
        const scale_stops = scale.range();
        const scale_width = scale.rangeBand();
        const svg = d3.select(el.get(0)).append("svg");
        svg.attr('height', '15px');
        svg.attr('width', Math.max(el.width(), 0));
        let wt = 0;
        const timebuckets = scope.operationplan.inventoryreport;

        for (const i in timebuckets) {
          const w = margin + scale_stops[i] + scale_width / 2;
          if (wt <= w) {
            const t = svg.append('text')
              .attr('class', timebuckets[3] ? 'svgheaderhistory' : 'svgheadertext')
              .attr('x', w)
              .attr('y', '12')
              .attr('data-bucket', i)
              .text(timebuckets[i]['name'])
              .on("mouseenter", function (d) {
                const tiptext = "&nbsp;" + $filter('formatdate')(timebuckets[1]) + ' - ' + $filter('formatdate')(timebuckets[2]) + "&nbsp;";
                graph.showTooltip(tiptext);
              })
              .on("mouseleave", graph.hideTooltip)
              .on("mousemove", graph.moveTooltip);
            wt = w + t.node().getComputedTextLength() + 12;
          }
        }
      },

      showTooltip: function (txt) {
        // Find or create the tooltip div
        let tt = d3.select("#tooltip");
        if (tt.empty())
          tt = d3.select("body")
            .append("div")
            .attr("id", "tooltip")
            .attr("role", "tooltip")
            .attr("class", "card p-2")
            .style("position", "absolute");

        // Update content and display
        tt.html('' + txt)
          .style('display', 'block');
        graph.moveTooltip();
      },

      hideTooltip: function () {
        d3.select("#tooltip").style('display', 'none');
        d3.event.stopPropagation();
      },

      moveTooltip: function () {
        if (d3.event == null) return;
        let xpos = d3.event.pageX + 5;
        let ypos = d3.event.pageY - 28;
        const xlimit = $(window).width() - $("#tooltip").width() - 20;
        const ylimit = $(window).height() - $("#tooltip").height() - 20;
        if (xpos > xlimit) {
          // Display tooltip under the mouse
          xpos = xlimit;
          ypos = d3.event.pageY + 5;
        }
        if (ypos > ylimit)
          // Display tooltip above the mouse
          ypos = d3.event.pageY - $("#tooltip").height() - 25;
        d3.select("#tooltip")
          .style({
            'left': xpos + "px",
            'top': ypos + "px"
          });
        d3.event.stopPropagation();
      },

      miniAxis: function (s) {
        const sc = this.scale().range();
        const dm = this.scale().domain();
        // Draw the scale line
        s.append("path")
          .attr("class", "domain")
          .attr("d", "M-10 0 H0 V" + (sc[0] - 2) + " H-10");
        // Draw the maximum value
        s.append("text")
          .attr("x", -2)
          .attr("y", 13) // Depends on font size...
          .attr("text-anchor", "end")
          .text($filter("number")(Math.round(dm[1])));
        // Draw the minimum value
        s.append("text")
          .attr("x", -2)
          .attr("y", sc[0] - 5)
          .attr("text-anchor", "end")
          .text(Math.round(dm[0]));
      }
    };

  } //link end
} //directive end
