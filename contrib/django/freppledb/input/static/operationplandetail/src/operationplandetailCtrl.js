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

angular.module('operationplandetailapp').controller('operationplandetailCtrl', operationplanCtrl);

operationplanCtrl.$inject = ['$scope', 'OperationPlan'];

function operationplanCtrl($scope, OperationPlan) { //console.log("loads controller");
  $scope.test = "angular controller";
  $scope.operationplan = new OperationPlan();

  $scope.$watchGroup(['operationplan.id','operationplan.start','operationplan.end','operationplan.quantity','operationplan.status'], function(newValue, oldValue) {
    //console.log(oldValue); console.log(newValue);
    if (oldValue[0] === newValue[0] && typeof oldValue[0] !== 'undefined') { //is a change to the current operationplan

      angular.element(document).find("#" + $scope.operationplan.id).addClass("edited");

      if (typeof oldValue[1] !== 'undefined' && oldValue[1] !== newValue[1]) {
        angular.element(document).find("#grid").jqGrid("setCell", $scope.operationplan.id, "startdate", $scope.operationplan.start, "dirty-cell");
        $("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
    	  $("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
      }
      if (typeof oldValue[2] !== 'undefined' && oldValue[2] !== newValue[2]) {
        jQuery("#grid").jqGrid("setCell", $scope.operationplan.id, "enddate", $scope.operationplan.end, "dirty-cell");
        $("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
    	  $("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
      }
      if (typeof oldValue[3] !== 'undefined' && oldValue[3] !== newValue[3]) {
        jQuery("#grid").jqGrid("setCell", $scope.operationplan.id, "quantity", $scope.operationplan.quantity, "dirty-cell");
        $("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
    	  $("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
      }
      if (typeof oldValue[4] !== 'undefined' && oldValue[4] !== newValue[4]) {
        jQuery("#grid").jqGrid("setCell", $scope.operationplan.id, "status", $scope.operationplan.status, "dirty-cell");
        $("#save").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
    	  $("#undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
      }
    }
    oldValue[0] = newValue[0];
    oldValue[1] = newValue[1];
    oldValue[2] = newValue[2];
    oldValue[3] = newValue[3];
    oldValue[4] = newValue[4];
  }); //end watchGroup

  function displayInfo(rowid) {
    var row = jQuery("#grid").getRowData(rowid);
    $scope.operationplan = new OperationPlan();
    if (row.hasOwnProperty('buffer') || row.hasOwnProperty('resource')) {
      rowid = row.operationplan__id;
      $scope.operationplan.editable = false;
    } else {
      $scope.operationplan.editable = true;
    }
    $scope.operationplan.id = (typeof rowid === undefined)?undefined:parseInt(rowid);
    $scope.operationplan.get().catch(function (response) {
      errorPopup(response.data);
    });
    //console.log($scope.operationplan);
  }
  $scope.displayInfo = displayInfo;

}
