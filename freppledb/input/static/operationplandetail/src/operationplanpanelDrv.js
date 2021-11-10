/*
 * Copyright (C) 2017 by frePPLe bv
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

angular.module('operationplandetailapp').directive('showoperationplanDrv', showoperationplanDrv);

showoperationplanDrv.$inject = ['$window', 'gettextCatalog'];

function showoperationplanDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: true,
    templateUrl: '/static/operationplandetail/operationplanpanel.html',
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    scope.actions = actions;
    scope.opptype = { //just a translation
      'MO': gettextCatalog.getString('manufacturing order'),
      'PO': gettextCatalog.getString('purchase order'),
      'DO': gettextCatalog.getString('distribution order'),
      'STCK': gettextCatalog.getString('stock'),
      'DLVR': gettextCatalog.getString('delivery'),
    }

    scope.$on("cardChanged", function (event, field, oldvalue, newvalue) {
      if (field === "startdate")
        scope.operationplan["start"] = newvalue;
      else if (field === "enddate")
        scope.operationplan["end"] = newvalue;
      else
        scope.operationplan[field] = newvalue;
    });

    //need to watch all of these because a webservice may change them on the fly
    scope.$watchGroup(['operationplan.id', 'operationplan.start', 'operationplan.end', 'operationplan.quantity', 'operationplan.completed_quantity', 'operationplan.criticality', 'operationplan.delay', 'operationplan.status'], function (newValue, oldValue) {
      if (scope.operationplan === undefined)
        return;
      else if (scope.operationplan.id == -1 || scope.operationplan.type === 'STCK') {
        // Multiple operationplans selected
        angular.element(elem).find('input').attr('disabled', 'disabled');
        angular.element(elem).find('#statusrow .btn').removeClass('active').attr('disabled', 'disabled');
      }
      else if (typeof scope.operationplan.id !== 'undefined') {
        // Single operationplan selected
        angular.element(elem).find('input[disabled]').attr('disabled', false);
        if (typeof actions !== 'undefined' && actions.hasOwnProperty('proposed')) {
          angular.element(elem).find('button[disabled]').attr('disabled', false);
        }
        angular.element(elem).find('#statusrow .btn').removeClass('active');

        if (scope.operationplan.hasOwnProperty('start'))
          angular.element(elem).find("#setStart").val(moment(scope.operationplan.start).format('YYYY-MM-DD HH:mm:ss'));
        if (scope.operationplan.hasOwnProperty('end'))
          angular.element(elem).find("#setEnd").val(moment(scope.operationplan.end).format('YYYY-MM-DD HH:mm:ss'));

        if (scope.operationplan.hasOwnProperty('status')) {
          angular.element(elem).find('#statusrow .btn').removeClass('active');
          angular.element(elem).find('#' + scope.operationplan.status + 'Btn').addClass('active');
        }
      }
      else {
        // No operationplan selected
        angular.element(elem).find('input').attr('disabled', 'disabled');
        angular.element(elem).find('#statusrow .btn').removeClass('active').attr('disabled', 'disabled');
        angular.element(elem).find("#setStart").val('');
        angular.element(elem).find("#setEnd").val('');
      }
      angular.element(elem).find("#statusrow").css(
        "display", (scope.operationplan.status && scope.operationplan.type !== 'STCK') ? "table-row" : "none"
      );
    }); //watch end

  } //link end
} //directive end
