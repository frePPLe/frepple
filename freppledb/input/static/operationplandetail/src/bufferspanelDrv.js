/*
 * Copyright (C) 2017 by frePPLe bv
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

angular.module('operationplandetailapp').directive('showbufferspanelDrv', showbufferspanelDrv);

showbufferspanelDrv.$inject = ['$window', 'gettextCatalog', '$filter'];

function showbufferspanelDrv($window, gettextCatalog, $filter) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    var template = '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_bufferspanel" aria-expanded="false" aria-controls="widget_bufferspanel">' + 
      '<h5 class="card-title text-capitalize fs-5 me-auto">' +
      gettextCatalog.getString("items") +
      '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
      '<div class="card-body collapse show" id="widget_bufferspanel">' +
      '<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("item") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("location") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("quantity") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("onhand") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("date") + '</b>' +
      '</td></tr></thead>' +
      '<tbody></tbody>' +
      '</table></div>';

    function redraw() {
      angular.element(document).find('#attributes-operationflowplans').empty().append(template);
      var rows = '<tr><td colspan="3">' + gettextCatalog.getString('no movements') + '<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('flowplans')) {
          rows = '';
          var firstproducer = true;
          angular.forEach(scope.operationplan.flowplans, function (theflow) {
            if (theflow.quantity > 0 && firstproducer) {
              rows += '<tr class="border-top">';
              firstproducer = false;
            }
            else
              rows += '<tr>';
            if (!theflow.hasOwnProperty('alternates')) {
              rows += '<td><span ';
              if (theflow.buffer.description)
                rows += ' onmouseenter="$(this).tooltip(\'show\')" title="' + $.jgrid.htmlEncode(theflow.buffer.description) + '"';
              rows += '>' + $.jgrid.htmlEncode(theflow.buffer.item)
                + "<a href=\"" + url_prefix + "/detail/input/item/" + admin_escape(theflow.buffer.item)
                + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
                + '</span></td>'
            }
            else {
              rows += '<td style="white-space: nowrap"><div class="dropdown">'
                + '<button class="btn btn-primary text-capitalize" data-bs-toggle="dropdown" type="button" style="min-width: 150px">'
                + $.jgrid.htmlEncode(theflow.buffer.item)
                + '</button>'
                + '<ul class="dropdown-menu">'
                + '<li><a role="menuitem" class="dropdown-item alternateitem text-capitalize">'
                + $.jgrid.htmlEncode(theflow.buffer.item)
                + '</a></li>';
              angular.forEach(theflow.alternates, function (thealternate) {
                rows += '<li><a role="menuitem" class="dropdown-item alternateitem text-capitalize">'
                  + $.jgrid.htmlEncode(thealternate)
                  + '</a></li>';
              });
              rows += '</ul></td>';
            }
            rows += '<td>' + $.jgrid.htmlEncode(theflow.buffer.location)
              + '</td><td>' + grid.formatNumber(theflow.quantity)
              + '</td><td>' + grid.formatNumber(theflow.onhand)
              + '</td><td style="white-space: nowrap">' + $filter('formatdatetime')(theflow.date)
              + '</td></tr>';
          });
          angular.element(document).find('#attributes-operationflowplans thead').css('display', 'table-header-group');
        }
      }
      angular.element(document).find('#attributes-operationflowplans tbody').append(rows);
      angular.element(document).find('#attributes-operationflowplans a.alternateitem').bind('click', function () {
        var newitem = $(this).html();
        var curitem = $(this).parent().parent().prev().html();
        if (newitem != curitem) {
          angular.forEach(scope.operationplan.flowplans, function (theflow) {
            if (theflow.buffer.item == curitem) {
              // Update the assigned item
              theflow.buffer.item = newitem;
              // Redraw the directive
              redraw();
              // Update the grid
              var grid = angular.element(document).find("#grid");
              var selrow = grid.jqGrid('getGridParam', 'selarrrow');
              var colmodel = grid.jqGrid('getGridParam', 'colModel').find(function (i) { return i.name == "material" });
              var cell = grid.jqGrid('getCell', selrow, 'material');
              if (colmodel.formatter == 'detail' && cell == curitem) {
                grid.jqGrid("setCell", selrow, "material", newitem, "dirty-cell");
                grid.jqGrid("setRowData", selrow, false, "edited");
                angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
                angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
              }
              else if (colmodel.formatter == 'listdetail') {
                var items = [];
                angular.forEach(scope.operationplan.flowplans, function (theflowplan) {
                  items.push([theflowplan.buffer.item, theflowplan.quantity]);
                });
                grid.jqGrid("setCell", selrow, "material", items, "dirty-cell");
                grid.jqGrid("setRowData", selrow, false, "edited");
                angular.element(document).find("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
                angular.element(document).find("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
              }
              return false;
            }
          });
        }
      });
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);
    };
    scope.$watchGroup(['operationplan.id', 'operationplan.flowplans.length'], redraw);
  } //link end
} //directive end
