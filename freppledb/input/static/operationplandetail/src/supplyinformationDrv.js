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

angular.module('operationplandetailapp').directive('showsupplyinformationDrv', showsupplyinformationDrv);

showsupplyinformationDrv.$inject = ['$window', 'gettextCatalog'];

function showsupplyinformationDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    var rows='';
    var template =  '<div class="panel-heading"><strong style="text-transform: capitalize;">'+
                      gettextCatalog.getString("supply information")+
                    '</strong></div>'+
                    '<div class="table-responsive"><table class="table table-hover table-condensed"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("priority")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("types")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("origin")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("lead time")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("cost")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("size minimum")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("size multiple")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("effective start")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("effective end")+'</b>' +
                    '</td></tr></thead>' +
                    '<tbody></tbody>' +
                  '</table></div>';

    scope.$watchGroup(['operationplan.id','operationplan.attributes.supply.length'], function (newValue,oldValue) {
      angular.element(document).find('#attributes-supplyinformation').empty().append(template);
      var rows = '<tr><td colspan="9">'+gettextCatalog.getString('no supply information')+'</td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.attributes.hasOwnProperty('supply')) {
          rows='';
          angular.forEach(scope.operationplan.attributes.supply, function(thesupply) {
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
    }); //watch end

  } //link end
} //directive end
