/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

'use strict';

angular.module('operationplandetailapp').directive('showoperationpeggingpanelDrv', showoperationpeggingpanelDrv);

showoperationpeggingpanelDrv.$inject = ['$window'];

function showoperationpeggingpanelDrv($window) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    var template = '<table class="table"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("demand")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("quantity")+'</b>' +
                    '</td>' +
                    '<tbody></tbody>' +
                  '</table>';

    scope.$watch('operationplan.id', function () {
      angular.element(document).find('#attributes-operationdemandpegging').empty().append(template);
      var rows='<tr><td colspan="2">'+gettext('no demands')+'<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('pegging_demand')) {
          rows='';
          angular.forEach(scope.operationplan.pegging_demand, function(thedemand) {
            rows += '<tr><td>'+thedemand.demand.name+'</td><td>'+thedemand.quantity+'</td></tr>';
          });
        }
      }

      angular.element(document).find('#attributes-operationdemandpegging tbody').append(rows);
    }); //watch end

  } //link end
} //directive end
