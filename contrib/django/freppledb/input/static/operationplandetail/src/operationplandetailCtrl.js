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

  // This template function will pass the values to the grid, function(id,column,value)
  // will set the row as "edited", and trigger "save undo" buttons.
  // If the function does not exist it makes no sense to watch for changes on the bottom part.
  $scope.displayongrid = displayongrid;

  if (typeof $scope.displayongrid === 'function') {
    //watch is only needed if we can update the grid
    $scope.$watchGroup(['operationplan.id','operationplan.start','operationplan.end','operationplan.quantity','operationplan.status'], function(newValue, oldValue) {
      //console.log(oldValue); console.log(newValue);
      if (oldValue[0] === newValue[0] && typeof oldValue[0] !== 'undefined') { //is a change to the current operationplan

        if (typeof oldValue[1] !== 'undefined' && typeof newValue[1] !== 'undefined' && oldValue[1] !== newValue[1]) {
          //console.log(oldValue[1]);console.log(newValue[1]);
          $scope.displayongrid($scope.operationplan.id,"startdate",$scope.operationplan.start);
        }
        if (typeof oldValue[2] !== 'undefined' && typeof newValue[2] !== 'undefined' && oldValue[2] !== newValue[2]) {
          //console.log(oldValue[2]);console.log(newValue[2]);
          $scope.displayongrid($scope.operationplan.id,"enddate",$scope.operationplan.end);
        }
        if (typeof oldValue[3] !== 'undefined' && typeof newValue[3] !== 'undefined' && oldValue[3] !== newValue[3]) {
          //console.log(oldValue[3]);console.log(newValue[3]);
          $scope.displayongrid($scope.operationplan.id,"quantity",$scope.operationplan.quantity);
        }
        if (typeof oldValue[4] !== 'undefined' && typeof newValue[4] !== 'undefined' && oldValue[4] !== newValue[4]) {
          //console.log(oldValue[4]);console.log(newValue[4]);
          $scope.displayongrid($scope.operationplan.id,"status",$scope.operationplan.status);
        }
      }
      oldValue[0] = newValue[0];
    }); //end watchGroup
  }

  function displayInfo(row) {
    //console.log(row);
    var rowid=(typeof row === 'undefined')?undefined:row.id;
    $scope.operationplan = new OperationPlan();

    if (typeof row !== 'undefined') {
      if (row.hasOwnProperty('buffer') || row.hasOwnProperty('resource')) {
        rowid = row.operationplan__id;
        $scope.operationplan.editable = false;
      } else {
        $scope.operationplan.editable = true;
      }
    }

    $scope.operationplan.id = (typeof rowid === 'undefined')?undefined:parseInt(rowid);
    function callback(opplan) {
      if (row === undefined) {
        return opplan;
      }
      // load previous changes from grid
      if (row.startdate !== undefined && row.startdate !== '') {
        opplan.start = row.startdate;
      }
      if (row.enddate !== undefined && row.enddate !== '') {
        opplan.end = row.enddate;
      }
      if (row.quantity !== undefined && row.quantity !== '') {
        opplan.quantity = parseInt(row.quantity);
      }

      if (row.status !== undefined && row.status !== '') {
        opplan.status = row.status;
      }
    }

    $scope.operationplan.get(callback).catch(function (response) {
      errorPopup(response.data);
    });
  }
  $scope.displayInfo = displayInfo;

  function refreshstatus(value) {

    if (value !== 'no_action') {
      $scope.$apply(function(){  $scope.operationplan.status = value;});
    }
  }
  $scope.refreshstatus = refreshstatus;

  function displayonpanel(rowid,columnid,value) {
    //console.log(rowid,columnid,value);
    angular.element(document).find("#" + $scope.operationplan.id).removeClass("edited").addClass("edited");
    if (rowid === $scope.operationplan.id.toString()) {
      if (columnid === "startdate") {
        $scope.$apply(function() {$scope.operationplan.start = value;});
      }
      if (columnid === "enddate") {
        $scope.$apply(function() {$scope.operationplan.end = value;});
      }
      if (columnid === "quantity") {
        $scope.$apply(function() {$scope.operationplan.quantity = parseInt(value);});
      }
      if (columnid === "status") {
        $scope.refreshstatus(value);
      }
    }
  }
  $scope.displayonpanel = displayonpanel;

  }
}
