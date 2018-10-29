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

angular.module('operationplandetailapp').directive('showoperationpeggingpanelDrv', showoperationpeggingpanelDrv);

showoperationpeggingpanelDrv.$inject = ['$window', 'gettextCatalog'];

function showoperationpeggingpanelDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs, transclude) {
    var template =  '<div class="panel-heading"><strong style="text-transform: capitalize;">'+
                      gettextCatalog.getString("demand")+
                    '</strong></div>'+
                    '<table class="table table-condensed table-hover"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("name")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("item")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("due")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("quantity")+'</b>' +
                    '</td>' +
                    '<tbody></tbody>' +
                    '</table>';

    scope.$watchGroup(['operationplan.id','operationplan.pegging_demand.length'], function (newValue,oldValue) {
      angular.element(document).find('#attributes-operationdemandpegging').empty().append(template);
      var rows='<tr><td colspan="2">'+gettextCatalog.getString('no demands')+'</td></tr>';

      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('pegging_demand')) {
          rows='';
          angular.forEach(scope.operationplan.pegging_demand, function(thedemand) {
            rows += '<tr><td>' + thedemand.demand.name +
              '</td><td>' + thedemand.demand.item.name +
              '</td><td>' + thedemand.demand.due +
              '</td><td>' + thedemand.quantity + '</td></tr>';
          });
        }
      }

      angular.element(document).find('#attributes-operationdemandpegging tbody').append(rows);
    }); //watch end

  } //link end
} //directive end
