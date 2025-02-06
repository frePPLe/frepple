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
 */

'use strict';

angular.module('operationplandetailapp').directive('showoperationpeggingpanelDrv', showoperationpeggingpanelDrv);

showoperationpeggingpanelDrv.$inject = ['$window', 'gettextCatalog', '$filter'];

function showoperationpeggingpanelDrv($window, gettextCatalog, $filter) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    var template = '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_demandpegging" aria-expanded="false" aria-controls="widget_demandpegging">' + 
      '<h5 class="card-title text-capitalize fs-5 me-auto">' +
      gettextCatalog.getString("demand") +
      '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
      '<div class="card-body table-responsive collapse show" id="widget_demandpegging" style="max-height:15em; overflow:auto">' +
      '<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("name") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("item") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("due") + '</b>' +
      '</td><td>' +
      '<b class="text-capitalize">' + gettextCatalog.getString("quantity") + '</b>' +
      '</td>' +
      '<tbody></tbody>' +
      '</table>' +
      '</div>';

    scope.$watchGroup(['operationplan.id', 'operationplan.pegging_demand.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-operationdemandpegging').empty().append(template);
      var rows = '<tr><td colspan="2">' + gettextCatalog.getString('no demands') + '</td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('pegging_demand')) {
          rows = '';
          angular.forEach(scope.operationplan.pegging_demand, function (thedemand) {
            rows += '<tr><td>' + $.jgrid.htmlEncode(thedemand.demand.name)
              + "<a href=\"" + url_prefix
              + (thedemand.demand.forecast ? "/detail/forecast/forecast/" : "/detail/input/demand/")
              + admin_escape(thedemand.demand.name)
              + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
              + '</td><td>';
            if (thedemand.demand.item.description)
              rows += '<span onmouseenter="$(this).tooltip(\'show\')" title="'
                + $.jgrid.htmlEncode(thedemand.demand.item.description) + '">'
                + $.jgrid.htmlEncode(thedemand.demand.item.name)
                + "</span>";
            else
              rows += $.jgrid.htmlEncode(thedemand.demand.item.name);
            rows += "<a href=\"" + url_prefix + "/detail/input/item/" + admin_escape(thedemand.demand.item.name)
              + "/\" onclick='event.stopPropagation()'><span class='ps-2 fa fa-caret-right'></span></a>"
              + '</td><td>' + $filter('formatdate')(thedemand.demand.due)
              + '</td><td>' + grid.formatNumber(thedemand.quantity) + '</td></tr>';
          });
        }
      }

      angular.element(document).find('#attributes-operationdemandpegging tbody').append(rows);
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);     
    }); //watch end

  } //link end
} //directive end
