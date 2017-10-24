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
