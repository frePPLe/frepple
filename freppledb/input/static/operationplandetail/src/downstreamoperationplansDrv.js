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

angular.module('operationplandetailapp').directive('showdownstreamoperationplansDrv', showdownstreamoperationplansDrv);

showdownstreamoperationplansDrv.$inject = ['$window', 'gettextCatalog'];

function showdownstreamoperationplansDrv($window, gettextCatalog) {

  var directive = {
    restrict: 'EA',
    scope: {operationplan: '=data'},
    link: linkfunc
  };
  return directive;

  function linkfunc(scope, elem, attrs) {
    var template =  '<div class="panel-heading"><h4 class="panel-title" style="text-transform: capitalize">'+
                      gettextCatalog.getString("downstream operations")+
                    '</h4></div>'+
                    '<table class="table table-condensed table-hover"><thead><tr><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("level")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("reference")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("type")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("operation")+'</b>' +
                    '</td><td>' +
                    '<b style="text-transform: capitalize;">'+gettextCatalog.getString("status")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("demands")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("item")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("location")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("start date")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("end date")+'</b>' +
                    '</td><td>' +
                      '<b style="text-transform: capitalize;">'+gettextCatalog.getString("quantity")+'</b>' +
                    '</td></tr></thead>' +
                    '<tbody></tbody>' +
                  '</table>';


    
    scope.$watchGroup(['operationplan.id','operationplan.downstreamoperationplans.length'], function (newValue,oldValue) {
      angular.element(document).find('#attributes-downstreamoperationplans').empty().append(template);
      var rows = '<tr><td colspan="8">'+gettextCatalog.getString('no downstream operationplans information')+'</td></tr>';
      var orderType = "";
      if (typeof scope.operationplan !== 'undefined') {
        if (scope.operationplan.hasOwnProperty('downstreamoperationplans')) {
          rows='';
          angular.forEach(scope.operationplan.downstreamoperationplans, function(thedownstreamoperationplans) {        	  
	  		  if (thedownstreamoperationplans[2] == "MO")
	  			  orderType = "manufacturingorder";
	  		  else if (thedownstreamoperationplans[2] == "PO")
	  			  orderType = "purchaseorder";
	  		  else if (thedownstreamoperationplans[2] == "DO")
	  			  orderType = "distributionorder";
	  		  else if (thedownstreamoperationplans[2] == "DLVR")
	  		  	  orderType = "deliveryorder";
  		  
        	  rows += '<tr><td>'
              + grid.formatNumber(thedownstreamoperationplans[0]) + '</td><td>'
          	  + $.jgrid.htmlEncode(thedownstreamoperationplans[1])
        	  + "<a href=\"" + url_prefix + "/data/input/" + orderType
        	  + "/?noautofilter&parentreference=" + admin_escape(thedownstreamoperationplans[1]) 
              + "\" onclick='event.stopPropagation()'><span class='leftpadding fa fa-caret-right'></span></a>"
              + '</td><td>'
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[2]) + '</td><td>'  
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[3]) + '</td><td>'
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[4]) + '</td><td>'
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[5]) + '</td><td>'
          	  + $.jgrid.htmlEncode(thedownstreamoperationplans[6])
        	  + "<a href=\"" + url_prefix + "/detail/input/item/" + admin_escape(thedownstreamoperationplans[6]) 
              + "/\" onclick='event.stopPropagation()'><span class='leftpadding fa fa-caret-right'></span></a>"
              + '</td><td>'
          	  + $.jgrid.htmlEncode(thedownstreamoperationplans[7])
        	  + "<a href=\"" + url_prefix + "/detail/input/location/" + admin_escape(thedownstreamoperationplans[7]) 
              + "/\" onclick='event.stopPropagation()'><span class='leftpadding fa fa-caret-right'></span></a>"
              + '</td><td>'
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[8]) + '</td><td>'
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[9]) + '</td><td>'
              +  $.jgrid.htmlEncode(thedownstreamoperationplans[10]) + '</td></tr>';
          });
        }
      }
      angular.element(document).find('#attributes-downstreamoperationplans tbody').append(rows);
    }); //watch end

  } //link end
} //directive end
