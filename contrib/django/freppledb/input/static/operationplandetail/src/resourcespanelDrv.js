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

angular.module('operationplandetailapp').directive('showresourcespanelDrv', showresourcespanelDrv);

showresourcespanelDrv.$inject = ['$window'];

function showresourcespanelDrv($window) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    var template = '<table class="table"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("resource")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("quantity")+'</b>' +
                    '</td>' +
                    '<tbody></tbody>' +
                  '</table>';

    scope.$watch('operationplan.id', function () {
      angular.element(document).find('#attributes-operationresources').empty().append(template);
      var rows='<tr><td colspan="2">'+gettext('no resources')+'<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('loadplans')) {
          rows='';
          angular.forEach(scope.operationplan.loadplans, function(theresource) {
            rows += '<tr><td>'+theresource.resource.name+'</td><td>'+theresource.quantity+'</td></tr>';
          });
        }
      }

      angular.element(document).find('#attributes-operationresources tbody').append(rows);
    }); //watch end

  } //link end
} //directive end
