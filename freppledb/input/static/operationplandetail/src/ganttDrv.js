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

    $scope.curselected = null;
    $scope.colstyle = 'col-md-1';
    $scope.type = 'PO';
    $scope.admin_escape = admin_escape;
    $scope.url_prefix = url_prefix;
    $scope.mode = mode;

    console.log($scope, "scope")
    $scope.$watch('ganttoperationplans', function () {
      console.log("new data received ", $scope.ganttoperationplans);
    });

    $scope.opptype = {
      'MO': gettextCatalog.getString('Manufacturing Order'),
      'PO': gettextCatalog.getString('Purchase Order'),
      'DO': gettextCatalog.getString('Distribution Order'),
      'STCK': gettextCatalog.getString('Stock'),
      'DLVR': gettextCatalog.getString('Delivery'),
    };

    function getDirtyCards() {
      console.log("getting changes");
      return 111;
    }
    $scope.getDirtyCards = getDirtyCards;
  }
}
