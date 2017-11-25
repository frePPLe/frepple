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

angular.module('operationplandetailapp').directive('shownetworkstatusDrv', shownetworkstatusDrv);

shownetworkstatusDrv.$inject = ['$window', 'gettextCatalog'];

function shownetworkstatusDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    var rows='';
    var template =  '<div class="panel-heading"><strong style="text-transform: capitalize;">'+
                      gettextCatalog.getString("network status")+
                    '</strong></div>'+
                    '<table class="table table-condensed table-hover"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("item")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("location")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("onhand")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("purchase orders")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("distribution orders")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("manufacturing orders")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("overdue sales orders")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("sales orders")+'</b>' +
                    '</td></tr></thead>' +
                    '<tbody></tbody>' +
                  '</table>';

    scope.$watchGroup(['operationplan.id','operationplan.network.length'], function (newValue,oldValue) {
      angular.element(document).find('#attributes-networkstatus').empty().append(template);
      var rows = '<tr><td colspan="8">'+gettextCatalog.getString('no network information')+'</td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('network')) {
          rows='';
          angular.forEach(scope.operationplan.network, function(thenetwork) {
            rows += '<tr><td>' + thenetwork[0];
            if (thenetwork[1] === true) {
              rows += '<small>'+gettextCatalog.getString('superseded')+'</small>';
            }
            rows += '</td><td>'+
            thenetwork[2]+'</td><td>'+
            thenetwork[3]+'</td><td>'+
            thenetwork[4]+'</td><td>'+
            thenetwork[5]+'</td><td>'+
            thenetwork[6]+'</td><td>'+
            thenetwork[7]+'</td><td>'+
            thenetwork[8]+'</td></tr>';
          });
        }
      }
      angular.element(document).find('#attributes-networkstatus tbody').append(rows);
    }); //watch end

  } //link end
} //directive end
