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
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

angular.module('operationplandetailapp').directive('showGanttDrv', showGanttDrv);

showKanbanDrv.$inject = ['$window', 'gettextCatalog', 'OperationPlan', 'PreferenceSvc'];

function showGanttDrv($window, gettextCatalog, OperationPlan, PreferenceSvc) {
  'use strict';

  var directive = {
    restrict: 'EA',
    scope: {
      ganttoperationplans: '=',
      editable: '='
    },
    templateUrl: '/static/operationplandetail/gantt.html',
    link: linkfunc
  };
  return directive;

  function linkfunc($scope, $elem, attrs) {
    $scope.rowheight = 25;
    $scope.curselected = null;
    $scope.colstyle = 'col-md-1';
    $scope.type = 'PO';
    $scope.admin_escape = admin_escape;
    $scope.url_prefix = url_prefix;
    $scope.mode = mode;

    $scope.$watch('ganttoperationplans', function () {
      $scope.drawGantt();
    });

    $scope.opptype = {
      'MO': gettextCatalog.getString('Manufacturing Order'),
      'PO': gettextCatalog.getString('Purchase Order'),
      'DO': gettextCatalog.getString('Distribution Order'),
      'STCK': gettextCatalog.getString('Stock'),
      'DLVR': gettextCatalog.getString('Delivery'),
    };

    function getHeight(gutter) {
      if (preferences && preferences['height'])
        return preferences['height'] - (gutter || 25);
      else
        return 220;
    }
    $scope.getHeight = getHeight;

    function getDirtyCards() {
      console.log("getting changes");
      return 111;
    }
    $scope.getDirtyCards = getDirtyCards;

    function buildtooltip() {
      return $(this).attr("data-reference");
      var extra = '';
      var thedelay = Math.round(parseFloat(parseInt($(this).attr("data-delay"))) / 8640) / 10;
      if (thedelay < 0.1)
        thedelay = "" + (-thedelay) + " days early";
      else if (thedelay > 0.1)
        thedelay = "" + thedelay + " days late";
      else
        thedelay = "on time";
      if ($(this).attr("data-description"))
        extra += gettext('description') + ": " + $(this).attr("data-description") + '<br>';
      if ($(this).attr("data-batch"))
        extra += gettext('batch') + ": " + $(this).attr("data-batch") + '<br>';
      if ($(this).attr("data-type") === 'MO') {
        return gettext('manufacturing order') + '<br>' +
          $(this).attr("data-operation") + '<br>' +
          gettext('reference') + ": " + $(this).attr("data-reference") + '<br>' +
          extra +
          gettext('start') + ": " + $(this).attr("data-startdate") + '<br>' +
          gettext('end') + ": " + $(this).attr("data-enddate") + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-quantity"))) + "<br>" +
          gettext('required quantity') + ": " + grid.formatNumber($(this).attr("data-required_quantity")) + "<br>" +
          gettext('criticality') + ": " + $(this).attr("data-criticality") + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext($(this).attr("data-status")) + "<br>";
      }
      else if ($(this).attr("data-type") === 'PO') {
        return gettext('purchase order') + '<br>' +
          $(this).attr("data-item") + ' @ ' + $(this).attr("data-location") + '<br>' +
          gettext('reference') + ": " + $(this).attr("data-reference") + '<br>' +
          extra +
          gettext('supplier') + ": " + $(this).attr("data-supplier") + '<br>' +
          gettext('start') + ": " + $(this).attr("data-startdate") + '<br>' +
          gettext('end') + ": " + $(this).attr("data-enddate") + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-quantity"))) + "<br>" +
          gettext('required quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-required_quantity"))) + "<br>" +
          gettext('criticality') + ": " + $(this).attr("data-criticality") + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext($(this).attr("data-status")) + "<br>";
      }
      else if ($(this).attr("data-type") === 'DO') {
        return gettext('distribution order') + '<br>' +
          $(this).attr("data-item") + ' @ ' + $(this).attr("data-location") + '<br>' +
          gettext('origin') + ": " + $(this).attr("data-origin") + '<br>' +
          gettext('reference') + ": " + $(this).attr("data-reference") + '<br>' +
          extra +
          gettext('start') + ": " + $(this).attr("data-startdate") + '<br>' +
          gettext('end') + ": " + $(this).attr("data-enddate") + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-quantity"))) + "<br>" +
          gettext('required quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-required_quantity"))) + "<br>" +
          gettext('criticality') + ": " + $(this).attr("data-criticality") + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext($(this).attr("data-status")) + "<br>";
      }
      else if ($(this).attr("data-type") === 'STCK') {
        return gettext('inventory') + '<br>' +
          $(this).attr("data-item") + ' @ ' + $(this).attr("data-location") + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-quantity"))) + "<br>";
      }
      else if ($(this).attr("data-type") === 'DLVR') {
        return gettext('customer delivery') + '<br>' +
          extra +
          $(this).attr("data-item") + ' @ ' + $(this).attr("data-location") + '<br>' +
          gettext('demand') + ": " + $(this).attr("data-demand") + '<br>' +
          gettext('start') + ": " + $(this).attr("data-startdate") + '<br>' +
          gettext('end') + ": " + $(this).attr("data-enddate") + '<br>' +
          gettext('quantity') + ": " + grid.formatNumber(parseFloat($(this).attr("data-quantity"))) + "<br>" +
          gettext('criticality') + ": " + $(this).attr("data-criticality") + "<br>" +
          gettext('delay') + ": " + thedelay + "<br>" +
          gettext('status') + ": " + gettext($(this).attr("data-status")) + "<br>";
      }
    }
    $scope.buildtooltip = buildtooltip;

    function buildcolor(opplan) {
      return "red";
    }
    $scope.buildcolor = buildcolor;

    function time2scale(d) {
      return Math.round((d - horizonstart) / (horizonend - horizonstart) * 1000);
    }
    $scope.time2scale = time2scale;

    function duration2scale(d) {
      return Math.round(d / (horizonend - horizonstart) * 1000);
    }
    $scope.duration2scale = duration2scale;

    function drawGantt() {
      if (!$scope.ganttoperationplans.rows) return;
      var data = '<table class="table"><tr><th>resource</th><th id="ganttheader"></th></tr>';
      var curresource;
      var first = true;
      var layer = [];
      var svgdata = "";
      for (var opplan of $scope.ganttoperationplans.rows) {
        console.log("---", opplan, layer);
        if (opplan.resource != curresource) {
          curresource = opplan.resource;
          if (!first) {
            data += '<svg viewbox="0 0 1000 '
              + (layer.length * $scope.rowheight) + '" width="100%" height="'
              + (layer.length * $scope.rowheight) + 'px">' + svgdata + "</svg></td></tr>";
            console.log(layer);
          }
          first = false;
          data += "<tr><td>" + opplan.resource + '</td><td>';
          layer = [];
          svgdata = "";
        }

        var row = 0;
        for (; row < layer.length; ++row) {
          //console.log("      ", new Date(opplan["startdate"]) >= layer[row], new Date(opplan["startdate"]), layer[row])
          if (new Date(opplan["startdate"]) >= layer[row] && (opplan["enddate"] != opplan["startdate"])) {
            //layer[row] = new Date(opplan["enddate"]);
            console.log("-----reuse");
            break;
          }
        };
        if (row >= layer.length) {
          //console.log("-----new");
          layer.push(new Date(opplan["enddate"]));
        }

        svgdata += '<rect x="' + time2scale(new Date(opplan.startdate))
          + '" y="' + (-row * $scope.rowheight)
          + '" fill="' + buildcolor(opplan)
          + '" width="' + duration2scale(opplan.enddate - opplan.startdate)
          + '" height="' + ($scope.rowheight - 3)
          + '" data-reference="' + encodeURI(opplan.operationplan__reference) + '"';
        if (opplan["status"] == "proposed")
          svgdata += ' fill-opacity="0.5"/>';
        else
          svgdata += '/>';
      }
      if (!first)
        data += '<svg viewbox="0 0 1000 '
          + (layer.length * $scope.rowheight) + '" width="100%" height="'
          + (layer.length * $scope.rowheight) + 'px">' + svgdata + "</svg></td></tr>";
      data += "</table>";
      angular.element(document).find('#ganttgraph').empty().append(data);
      gantt.header("#ganttheader");

      $('svg rect').each(function () {
        bootstrap.Tooltip.getOrCreateInstance($(this)[0], {
          title: $scope.buildtooltip,
          animation: false,
          html: true,
          container: 'body',
          template: `
         <div class="tooltip opacity-100" role="tooltip">
           <div class="tooltip-arrow"></div>
           <div class="tooltip-inner bg-white text-start text-body fs-6 p-3"></div>
         </div>`
        });
      });
    }
    $scope.drawGantt = drawGantt;
  }
}
