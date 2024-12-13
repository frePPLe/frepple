/*
 * Copyright (C) 2023 by frePPLe bv
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
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

'use strict';

forecastapp.directive('displayForecastGraph', displayForecastGraph);

displayForecastGraph.$inject = ['$window', 'gettextCatalog'];

function displayForecastGraph($window, gettextCatalog) {
  return {
    restrict: 'EA',
    scope: {
      data: '=',
      label: '@',
      onClick: '&',
      rows: '=rows'
    },
    link: function (scope, elem, attrs) {

      function onresize() {
        scope.$apply();
      }
      $window.onresize = onresize;

      scope.$watch(function () {
        return angular.element($window)[0].innerWidth;
      }, function () {
        scope.render(scope.data);
      });

      scope.$watch('data', function (newData) {
        scope.render(newData);
      }, true);

      function getFirstBucket(graphdata) {
        var nyearsago;
        if (scope.rows.includes("orderstotal3ago") || scope.rows.includes("ordersadjustment3ago")
          || scope.rows.includes("ordersadjustmentvalue3ago") || scope.rows.includes("ordersadjustmentvalue3ago"))
          // Show all buckets
          return graphdata[0].bucket;
        else if (scope.rows.includes("orderstotal2ago") || scope.rows.includes("ordersadjustment2ago")
          || scope.rows.includes("ordersadjustmentvalue2ago") || scope.rows.includes("ordersadjustmentvalue2ago"))
          nyearsago = 2;
        else if (scope.rows.includes("orderstotal1ago") || scope.rows.includes("ordersadjustment1ago")
          || scope.rows.includes("ordersadjustmentvalue1ago") || scope.rows.includes("ordersadjustmentvalue1ago"))
          nyearsago = 1;
        else
          // Show only future periods
          return currentbucket;

        // First find the index of the current bucket
        var currentfcstbucket;
        for (var something in graphdata) {
          if (graphdata[something].bucket == currentbucket) {
            currentfcstbucket = graphdata[something];
            break;
          }
        }

        var startdate = new Date(currentfcstbucket.startdate)
        var enddate = new Date(currentfcstbucket.enddate)
        // Get the date right in the middle between start and end date and remove 365*nyearsago milliseconds
        var middledate = new Date(-365 * 24 * 3600 * 1000 * nyearsago + Math.round(startdate.getTime()
          + (enddate.getTime() - startdate.getTime()) / 2.0))

        for (var something in graphdata) {
          var bucketStart = new Date(graphdata[something].startdate.substring(0, 10))
          var bucketEnd = new Date(graphdata[something].enddate.substring(0, 10))
          if (middledate >= bucketStart && middledate < bucketEnd)
            return graphdata[something].bucket;
        }
      };

      function render(graphdata) {
        if (!graphdata)
          return;

        var margin = {
          top: 0,
          right: 130,
          bottom: 30,
          left: 50
        };
        var width = angular.element(document).find("#forecastgraph").width() - margin.left - margin.right;
        var height = angular.element(document).find("#forecastgraph").height() - margin.top - margin.bottom;
        var i = 0;
        var firstBucket = getFirstBucket(graphdata);

        // Define X-axis
        var domainX = [];
        var bucketnamelength = 0;
        var plancurrentbucket = 0;
        var forecastcurrentbucket = 0;
        var showBucket = false;
        var filteredGraphData = [];
        for (i in graphdata) {
          if (!showBucket && graphdata[i].bucket == firstBucket) {
            plancurrentbucket -= parseInt(i);
            forecastcurrentbucket -= parseInt(i);
            showBucket = true;
          }
          if (showBucket) {
            domainX.push(graphdata[i].bucket);
            bucketnamelength = Math.max(graphdata[i].bucket.length, bucketnamelength);
            filteredGraphData.push(graphdata[i]);
            if (graphdata[i].currentbucket)
              plancurrentbucket += parseInt(i);
            if (graphdata[i].forecast_currentbucket)
              forecastcurrentbucket += parseInt(i);
          }
        }
        var x = d3.scale.ordinal()
          .domain(domainX)
          .rangeRoundBands([0, width], 0);
        var xWidth = x.rangeBand();

        // Define Y-axis
        var y = d3.scale.linear().rangeRound([height, 0]);

        // Create a new SVG element
        angular.element(document).find(angular.element(document).find("#forecastgraph").get(0)).html("");

        var svg = d3.select(angular.element(document).find("#forecastgraph").get(0))
          .append("svg")
          .attr("class", "graphcell")
          .attr("width", width + margin.left + margin.right)
          .attr("height", height + margin.top + margin.bottom)
          .append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Get the maxima of the values
        var maxY = 0;
        var minY = 0;
        i = 0;
        showBucket = false;
        for (i in filteredGraphData) {

          var tmp = filteredGraphData[i];
          if (tmp.orderstotal + tmp.ordersadjustment > maxY) {
            maxY = tmp.orderstotal + tmp.ordersadjustment;
          }
          if (tmp.forecasttotal > maxY) {
            maxY = tmp.forecasttotal;
          }
          if (tmp.orderstotal < minY) {
            minY = tmp.orderstotal;
          }
          if (tmp.forecasttotal < minY) {
            minY = tmp.forecasttotal;
          }
        }

        // Update the scale of the Y-axis by looking for the max value
        y.domain([minY, maxY]);
        var Yzero = y(0);

        var myY;
        svg.selectAll("g")
          .data(filteredGraphData)
          .enter()
          .append("g")
          .attr("transform", function (d) {
            return "translate(" + x(d.bucket) + ",0)";
          })
          .each(function (d, i) {
            var bucket = d3.select(this);

            // Draw open orders bar
            if (d.ordersopen > 0) {
              myY = y(d.ordersopen);
              bucket.append("rect")
                .attr("width", xWidth)
                .attr("height", Yzero - myY)
                .attr("x", xWidth / 2)
                .attr("y", myY)
                .style("fill", "#2B95EC");
            }

            // Draw hovering tooltip
            bucket.append("rect")
              .attr("height", height)
              .attr("width", xWidth)
              .attr("fill-opacity", 0)
              .on("mouseenter", function (d) {
                if (i >= plancurrentbucket)
                  graph.showTooltip('' +
                    '<div style="text-align:center"><strong>' + d.bucket + '</strong></div>' + '<table style="margin: 5px;">' +
                    '<tr><td>' + gettextCatalog.getString("total orders") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.orderstotal) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("open orders") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.ordersopen) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("orders adjustment") + '</td><td style="text-align:right">' +
                    ((d.ordersadjustment === null) ? '' : grid.formatNumber(d.ordersadjustment)) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("forecast baseline") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.forecastbaseline) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("forecast override") + '</td><td style="text-align:right">' +
                    ((!d.hasOwnProperty("forecastoverride") || d.forecastoverride === null) ? '' : grid.formatNumber(d.forecastoverride)) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("forecast total") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.forecasttotal) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("forecast net") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.forecastnet) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("forecast consumed") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.forecastconsumed) +
                    '</td></tr></table>'
                  );
                else if (i < forecastcurrentbucket)
                  graph.showTooltip('' +
                    '<div style="text-align:center"><strong>' + d.bucket + '</strong></div>' + '<table style="margin: 5px;">' +
                    '<tr><td>' + gettextCatalog.getString("total orders") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.orderstotal) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("open orders") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.ordersopen) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("orders adjustment") + '</td><td style="text-align:right">' +
                    ((d.ordersadjustment === null) ? '' : grid.formatNumber(d.ordersadjustment)) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("past forecast") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.forecastbaseline) +
                    '</td></tr></table>'
                  );
                else
                  graph.showTooltip('' +
                    '<div style="text-align:center"><strong>' + d.bucket + '</strong></div>' + '<table style="margin: 5px;">' +
                    '<tr><td>' + gettextCatalog.getString("total orders") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.orderstotal) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("open orders") + '</td><td style="text-align:right">' +
                    grid.formatNumber(d.ordersopen) +
                    '</td></tr><tr><td>' + gettextCatalog.getString("orders adjustment") + '</td><td style="text-align:right">' +
                    ((d.ordersadjustment === null) ? '' : grid.formatNumber(d.ordersadjustment)) +
                    '</td></tr></table>'
                  );
              })
              .on("mouseleave", graph.hideTooltip)
              .on("mousemove", graph.moveTooltip);
          });

        // Create D3 lines - orders
        var line = d3.svg.line()
          .x(function (d) {
            return x(d.bucket) + xWidth / 2;
          })
          .y(function (d) {
            return y(Math.max(0, d.orderstotal + d.ordersadjustment));
          });
        svg.append("svg:path")
          .attr('class', 'graphline')
          .attr("stroke", "#8BBA00")
          .attr("d", line(filteredGraphData));

        // Create D3 lines - total forecast
        line = d3.svg.line()
          .x(function (d) {
            return x(d.bucket) + xWidth / 2;
          })
          .y(function (d, i) {
            return y((i >= plancurrentbucket) ? d.forecasttotal : 0);
          });
        svg.append("svg:path")
          .attr('class', 'graphline')
          .attr("stroke", "#FF0000")
          .attr("d", line(filteredGraphData));

        // Create D3 lines - past forecast
        line = d3.svg.line()
          .x(function (d) {
            return x(d.bucket) + xWidth / 2;
          })
          .y(function (d, i) {
            return y((i < forecastcurrentbucket) ? d.forecasttotal : 0);
          });
        svg.append("svg:path")
          .attr('class', 'graphline')
          .attr("stroke", "#FF7B00")
          .attr("d", line(filteredGraphData));

        // Display Y-Axis
        var yAxis = d3.svg.axis()
          .scale(y)
          .orient("left")
          .tickFormat(d3.format("s"));
        svg.append("g")
          .attr("class", "y axis")
          .call(yAxis);

        // Display X-axis for a single forecast
        var nth = Math.ceil(filteredGraphData.length / width * bucketnamelength * 10);
        var myticks = [];
        for (i in filteredGraphData) {
          if (i % nth === 0) {
            myticks.push(filteredGraphData[i].bucket);
          }
        }
        var xAxis = d3.svg.axis()
          .scale(x)
          .tickValues(myticks)
          .orient("bottom");
        svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis);

        // Display legend
        var legend = svg.append("g");
        var codes = [
          ["open orders", "#2B95EC", 1],
          ["total orders", "#8BBA00", 0],
          ["forecast total", "#FF0000", 5],
          ["past forecast", "#FF7B00", 6]
        ];
        var visible = 0;
        for (i in codes) {
          legend.append("rect")
            .attr("x", width + 82)
            .attr("width", 18)
            .attr("height", 18)
            .style("fill", codes[i][1])
            .attr("transform", "translate(0," + (visible * 20 + 10) + ")");
          legend.append("text")
            .attr("x", width + 76)
            .attr("y", 9)
            .attr("dy", ".35em")
            .style("text-anchor", "end")
            .text(codes[i][0])
            .attr("transform", "translate(0," + (visible * 20 + 10) + ")");
          visible += 1;
        }
      }
      scope.render = render;
    }
  };
}
