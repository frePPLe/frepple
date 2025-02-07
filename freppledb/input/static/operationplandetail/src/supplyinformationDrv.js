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

angular.module('operationplandetailapp').directive('showsupplyinformationDrv', showsupplyinformationDrv);

showsupplyinformationDrv.$inject = ['$window', 'gettextCatalog'];

function showsupplyinformationDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.$watchGroup(['operationplan.id', 'operationplan.attributes.supply.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-supplyinformation').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_supply" aria-expanded="false" aria-controls="widget_supply">' + 
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("supply information") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body collapse' + 
				(scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
				'" id="widget_supply">' +
        '<div class="table-responsive"><table class="table table-hover table-sm"><thead><tr><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("priority") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("types") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("origin") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("lead time") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("cost") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("size minimum") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("size multiple") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("effective start") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("effective end") + '</b>' +
        '</td></tr></thead>' +
        '<tbody></tbody>' +
        '</table></div></div>'
      );
      var rows = '<tr><td colspan="9">' + gettextCatalog.getString('no supply information') + '</td></tr>';

      if (typeof scope.operationplan !== 'undefined' && scope.operationplan.hasOwnProperty('attributes')) {
        if (scope.operationplan.attributes.hasOwnProperty('supply')) {
          rows = '';
          angular.forEach(scope.operationplan.attributes.supply, function (thesupply) {
            rows += '<tr>'
            for (var i in thesupply) {
              rows += '<td>';

              rows += thesupply[i];

              rows += '</td>';
            }
            rows += '</tr>'
          });
        }
      }
      angular.element(document).find('#attributes-supplyinformation tbody').append(rows);
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);
    }); //watch end

  } //link end
} //directive end
