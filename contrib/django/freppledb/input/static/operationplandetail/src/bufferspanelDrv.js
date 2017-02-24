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

angular.module('operationplandetailapp').directive('showbufferspanelDrv', showbufferspanelDrv);

showbufferspanelDrv.$inject = ['$window'];

function showbufferspanelDrv($window) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    var template = '<table class="table"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("buffer")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("quantity")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("onhand")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("date")+'</b>' +
                    '</td></tr></thead>' +
                    '<tbody></tbody>' +
                  '</table>';

    scope.$watch('operationplan.id', function () {
      angular.element(document).find('#attributes-operationflowplans').empty().append(template);
      var rows='<tr><td colspan="3">'+gettext('no movements')+'<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('flowplans')) {
          rows='';
          angular.forEach(scope.operationplan.flowplans, function(theflow) {
            rows += '<tr><td>'+theflow.buffer.name+'</td><td>'+
            theflow.quantity+'</td><td>'+theflow.onhand+'</td><td>'+
            theflow.date+'</td></tr>';
          });
        }
      }

      angular.element(document).find('#attributes-operationflowplans tbody').append(rows);
      //elem.after(transclude());
    }); //watch end
  } //link end
} //directive end
