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

angular.module('operationplandetailapp').directive('showproblemspanelDrv', showproblemspanelDrv);

showproblemspanelDrv.$inject = ['$window', 'gettextCatalog'];

function showproblemspanelDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: { operationplan: '=data' },
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.$watchGroup(['operationplan.id', 'operationplan.problems.length'], function (newValue, oldValue) {
      angular.element(document).find('#attributes-operationproblems').empty().append(
        '<div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_problems" aria-expanded="false" aria-controls="widget_problems">' + 
        '<h5 class="card-title text-capitalize fs-5 me-auto">' +
        gettextCatalog.getString("problems") +
        '</h5><span class="fa fa-arrows align-middle w-auto widget-handle"></span></div>' +
        '<div class="card-body collapse' + 
        (scope.$parent.widget[1]["collapsed"] ? '' : ' show') +
        '" id="widget_problems">' +
        '<table class="table table-sm table-hover table-borderless"><thead><tr><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("name") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("start") + '</b>' +
        '</td><td>' +
        '<b class="text-capitalize">' + gettextCatalog.getString("end") + '</b>' +
        '</td></tr></thead>' +
        '<tbody></tbody>' +
        '</table></div>'
      );
      var rows = '<tr><td colspan="3">' + gettextCatalog.getString('no problems') + '</td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('problems')) {
          rows = '';
          angular.forEach(scope.operationplan.problems, function (theproblem) {
            rows += '<tr><td>' +
              theproblem.description + '</td><td>' +
              theproblem.start + '</td><td>' +
              theproblem.end + '</td></tr>';
          });
        }
      }
      angular.element(document).find('#attributes-operationproblems tbody').append(rows);
      angular.element(elem).find('.collapse')
        .on("shown.bs.collapse", grid.saveColumnConfiguration)
        .on("hidden.bs.collapse", grid.saveColumnConfiguration);      
    }); //watch end

  } //link end
} //directive end
