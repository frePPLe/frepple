/*
 * Copyright (C) 2017 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

'use strict';

angular.module('operationplandetailapp').directive('showproblemspanelDrv', showproblemspanelDrv);

showproblemspanelDrv.$inject = ['$window'];

function showproblemspanelDrv($window) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    var rows='';
    var template = '<table class="table"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("problems")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("start")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("end")+'</b>' +
                    '</td></tr></thead>' +
                    '<tbody></tbody>' +
                  '</table>';

    scope.$watch('operationplan.id', function () {
      angular.element(document).find('#attributes-operationproblems').empty().append(template);
      var rows = '<tr><td colspan="3">'+gettext('no problems')+'<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('problems')) {
          rows='';
          angular.forEach(scope.operationplan.problems, function(theproblem) {
            rows += '<tr><td>'+
            theproblem.description+'</td>'+
            theproblem.start+'<td></td>'+
            theproblem.end+'<td></tr>';
          });
        }
      }
      angular.element(document).find('#attributes-operationproblems tbody').append(rows);
      //elem.after(transclude());
    }); //watch end

  } //link end
} //directive end
