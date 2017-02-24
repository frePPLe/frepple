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
    var row = jQuery("#grid").getRowData(rowid); //console.log(rowid);console.log(row.id);
    if (typeof parseInt(row.id) === 'number') { //console.log(row.id);
      $scope.operationplan.id = parseInt(row.id);
      $scope.operationplan.get().catch(function (response) {
        errorPopup(response.data);
      });
    } else {
      $scope.operationplan = new OperationPlan(); console.log(operationplan.id);
      $("#save").removeClass("btn-primary btn-danger").addClass("btn-primary").prop("disabled", "disabled");
  	  $("#undo").removeClass("btn-primary btn-danger").addClass("btn-primary").prop("disabled", "disabled");
    }
    //$scope.operationplan.reference = row.reference;
    //$scope.operationplan.status = row.status;
    //console.log($scope.operationplan);
  }
  $scope.displayInfo = displayInfo;

}
