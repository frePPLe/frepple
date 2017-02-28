/*
 * Copyright (C) 2017 by frePPLe bvba
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

angular.module('operationplandetailapp').directive('showresourcespanelDrv', showresourcespanelDrv);

showresourcespanelDrv.$inject = ['$window'];

function showresourcespanelDrv($window) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    var template = '<table class="table"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("resource")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettext("quantity")+'</b>' +
                    '</td>' +
                    '<tbody></tbody>' +
                  '</table>';

    scope.$watchGroup(['operationplan.id','operationplan.loadplans.length'], function (newValue,oldValue) {
      //console.log(oldValue);
      //console.log(newValue);
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
