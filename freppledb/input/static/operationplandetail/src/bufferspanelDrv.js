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

angular.module('operationplandetailapp').directive('showbufferspanelDrv', showbufferspanelDrv);

showbufferspanelDrv.$inject = ['$window', 'gettextCatalog'];

function showbufferspanelDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    var template =  '<div class="panel-heading"><strong style="text-transform: capitalize;">'+
                      gettextCatalog.getString("buffer")+
                    '</strong></div>'+
                    '<table class="table table-condensed table-hover"><thead style="display: none;"><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("name")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("quantity")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("expected onhand")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("date")+'</b>' +
                    '</td></tr></thead>' +
                    '<tbody></tbody>' +
                    '</table>';

    scope.$watchGroup(['operationplan.id','operationplan.flowplans.length'], function (newValue,oldValue) {
      angular.element(document).find('#attributes-operationflowplans').empty().append(template);
      var rows='<tr><td colspan="3">'+gettextCatalog.getString('no movements')+'<td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('flowplans')) {
          rows='';
          angular.forEach(scope.operationplan.flowplans, function(theflow) {
            rows += '<tr><td>'+theflow.buffer.name+'</td><td>'+
            theflow.quantity+'</td><td>'+theflow.onhand+'</td><td>'+
            theflow.date+'</td></tr>';
          });
          angular.element(document).find('#attributes-operationflowplans thead').css('display','table-header-group');
        }
      }

      angular.element(document).find('#attributes-operationflowplans tbody').append(rows);
      //elem.after(transclude());
    }); //watch end
  } //link end
} //directive end
