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
    var template = '<table class="table table-hover table-condensed"><thead><tr><td>' +
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
