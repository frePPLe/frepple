/*
 * Copyright (C) 2017 by frePPLe bv
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
 * General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
    var template = '<div class="card-header"><h5 class="card-title" style="text-transform: capitalize">' +
      gettextCatalog.getString("material") +
      '</h5></div>' +
      '<table class="table table-condensed table-hover"><thead><tr><td>' +
      '<b style="text-transform: capitalize;">' + gettextCatalog.getString("item") + '</b>' +
      '</td><td>' +
      '<b style="text-transform: capitalize;">' + gettextCatalog.getString("quantity") + '</b>' +
      '</td><td>' +
      '<b style="text-transform: capitalize;">' + gettextCatalog.getString("onhand") + '</b>' +
      '</td><td>' +
      '<b style="text-transform: capitalize;">' + gettextCatalog.getString("date") + '</b>' +
      '</td></tr></thead>' +
      '<tbody></tbody>' +
      '</table>';

    function redraw() {
      angular.element(document).find('#attributes-operationflowplans').empty().append(template);
      var rows = '<tr><td colspan="3">' + gettextCatalog.getString('no movements') + '<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('flowplans')) {
          rows = '';
          angular.forEach(scope.operationplan.flowplans, function (theflow) {
            rows += ''
            if (!theflow.hasOwnProperty('alternates')) {
              rows += '<tr><td><span ';
              if (theflow.buffer.description)
                rows += ' onmouseenter="$(this).tooltip(\'show\')" title="' + $.jgrid.htmlEncode(theflow.buffer.description) + '"';
              rows += '>' + $.jgrid.htmlEncode(theflow.buffer.item)
                + "<a href=\"" + url_prefix + "/detail/input/item/" + admin_escape(theflow.buffer.item)
                + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
                + '</span></td>'
            }
            else {
              rows += '<td style="white-space: nowrap"><div class="dropdown">'
                + '<button class="btn btn-default" data-bs-toggle="dropdown" type="button" style="text-transform: capitalize; min-width: 150px">'
                + $.jgrid.htmlEncode(theflow.buffer.item)
                + '</button>'
                + '<ul class="dropdown-menu">'
                + '<li><a role="menuitem" class="dropdown-item alternateitem" style="text-transform: capitalize">'
                + $.jgrid.htmlEncode(theflow.buffer.item)
                + '</a></li>';
              angular.forEach(theflow.alternates, function (thealternate) {
                rows += '<li><a role="menuitem" class="dropdown-item alternateitem" style="text-transform: capitalize">'
                  + $.jgrid.htmlEncode(thealternate)
                  + '</a></li>';
              });
              rows += '</ul></td>';
            }
            rows += '<td>' + grid.formatNumber(theflow.quantity)
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
      //elem.after(transclude());
    };
    scope.$watchGroup(['operationplan.id', 'operationplan.flowplans.length'], redraw);
  } //link end
} //directive end
