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

function operationplanCtrl($scope, OperationPlan) {
  $scope.test = "angular controller";
  $scope.operationplan = new OperationPlan();
  $scope.aggregatedopplan = null;

  // This template function will pass the values to the grid, function(id,column,value)
  // will set the row as "edited", and trigger "save undo" buttons.
  // If the function does not exist it makes no sense to watch for changes on the bottom part.
  $scope.displayongrid = displayongrid;

  if (typeof $scope.displayongrid === 'function') {
    //watch is only needed if we can update the grid
    $scope.$watchGroup(['operationplan.id','operationplan.start','operationplan.end','operationplan.quantity','operationplan.status'], function(newValue, oldValue) {
      if (oldValue[0] === newValue[0] && newValue[0] !== -1 && typeof oldValue[0] !== 'undefined') { //is a change to the current operationplan

        if (typeof oldValue[1] !== 'undefined' && typeof newValue[1] !== 'undefined' && oldValue[1] !== newValue[1]) {
          $scope.displayongrid($scope.operationplan.id,"startdate",$scope.operationplan.start);
        }
        if (typeof oldValue[2] !== 'undefined' && typeof newValue[2] !== 'undefined' && oldValue[2] !== newValue[2]) {
          $scope.displayongrid($scope.operationplan.id,"enddate",$scope.operationplan.end);
        }
        if (typeof oldValue[3] !== 'undefined' && typeof newValue[3] !== 'undefined' && oldValue[3] !== newValue[3]) {
          $scope.displayongrid($scope.operationplan.id,"quantity",$scope.operationplan.quantity);
        }
        if (typeof oldValue[4] !== 'undefined' && typeof newValue[4] !== 'undefined' && oldValue[4] !== newValue[4]) {

          if (actions.hasOwnProperty($scope.operationplan.status)) {
            //console.log('actions have status');
            $scope.displayongrid($scope.operationplan.id,"status",$scope.operationplan.status);
          } else if (!actions.hasOwnProperty($scope.operationplan.status) && oldValue[4] === 'proposed') {
            //console.log('will export to OB');
            actions[Object.keys(actions)[0]]();
          } else {
            //console.log('doing nothing');
          }
        }
      }
      oldValue[0] = newValue[0];
    }); //end watchGroup
  }

  function processAggregatedInfo(selectionData, colModel) {
    //console.log(selectionData);
    //console.log(colModel);
    var aggColModel = [];
    var aggregatedopplan = {};
    aggregatedopplan.colmodel = {};
    var temp = 0;
    angular.forEach (colModel, function(value,key) {
      if (value.hasOwnProperty('summaryType')) {
        aggColModel.push([key, value.name, value.summaryType, value.formatter]);
        aggregatedopplan[value.name] = null;
        aggregatedopplan.colmodel[value.name] = {'type': value.summaryType, 'label': value.label};
      }
    });
    //console.log(aggColModel);
    angular.forEach (selectionData, function(opplan) {
      angular.forEach (aggColModel, function(field) {
        if (field[2] === 'sum') {// console.log(field[1],parseFloat(opplan[field[1]]));
          if (!isNaN(parseFloat(opplan[field[1]]))) {
            if (aggregatedopplan[field[1]] === null) {
              aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
            } else {
              aggregatedopplan[field[1]] += parseFloat(opplan[field[1]]);
            }
          }
        } else if (field[2] === 'max') {

          if ( ['color','number','currency'].indexOf(field[3]) !== -1 && opplan[field[1]] !== "") { //console.log(opplan[field[1]]);
            if (parseFloat(opplan[field[1]])) {
              if (aggregatedopplan[field[1]] === null) { //console.log(opplan[field[1]]);
                aggregatedopplan[field[1]] = parseFloat(opplan[field[1]]);
              } else {
                aggregatedopplan[field[1]] = Math.max(aggregatedopplan[field[1]], parseFloat(opplan[field[1]]));
              }
            }
          } else if (field[3] === 'duration') { //console.log(field[1],opplan[field[1]],field[3]);
            temp = new moment.duration(opplan[field[1]]).asSeconds();
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) { //console.log(opplan[field[1]]);
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = Math.max(aggregatedopplan[field[1]], temp);
              }
            }
          } else if (field[3] === 'date') {
            temp = new moment(opplan[field[1]]);
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) { //console.log(opplan[field[1]]);
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = moment.max(aggregatedopplan[field[1]], temp);
              }
            }
          }

        } else if (field[2] === 'min') { //console.log(field[1],opplan[field[1]],field[3]);

          if ( ['color','number'].indexOf(field[3]) !== -1 && opplan[field[1]] !== "") {
            //console.log(field[1],opplan[field[1]],field[3]);
            temp = parseFloat(opplan[field[1]]);
            if (!isNaN(temp)) {
              if (aggregatedopplan[field[1]] === null) { //console.log(opplan[field[1]]);
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = Math.min(aggregatedopplan[field[1]], temp);
              }
              //console.log( Math.min(aggregatedopplan[field[1]], temp));
            }
          }  else if (field[3] === 'duration') { //console.log(field[1],opplan[field[1]],field[3]);
            temp = new moment.duration(opplan[field[1]]).asSeconds();
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) { //console.log(opplan[field[1]]);
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = Math.min(aggregatedopplan[field[1]], temp);
              }
            }
          } else if (field[3] === 'date') {
            temp = new moment(opplan[field[1]]);
            if (temp._d !== 'Invalid Date') {
              if (aggregatedopplan[field[1]] === null) { //console.log(opplan[field[1]]);
                aggregatedopplan[field[1]] = temp;
              } else {
                aggregatedopplan[field[1]] = moment.min(aggregatedopplan[field[1]], temp);
              }
            }
          }

        }
      });
    });
    $scope.operationplan = new OperationPlan();
    aggregatedopplan.start = aggregatedopplan.startdate;
    aggregatedopplan.end = aggregatedopplan.enddate;
    aggregatedopplan.id = -1;
    aggregatedopplan.type = selectionData[0].type;
    $scope.$apply(function(){ $scope.operationplan.extend(aggregatedopplan); });

    //console.log($scope.operationplan);
  }
  $scope.processAggregatedInfo = processAggregatedInfo;

  function displayInfo(row) {
    var rowid=(typeof row === 'undefined')?undefined:row.id;
    $scope.operationplan = new OperationPlan();

    if (typeof row !== 'undefined') {
      if (row.hasOwnProperty('operationplan__id')) {
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

    if (typeof $scope.operationplan.id === 'undefined') {
      $scope.$apply(function(){$scope.operationplan = new OperationPlan();});
    } else {
      $scope.operationplan.get(callback);
    }
  }
  $scope.displayInfo = displayInfo;

  function refreshstatus(value) {
    if (value !== 'no_action') {
      $scope.$apply(function(){  $scope.operationplan.status = value;});
    }
  }
  $scope.refreshstatus = refreshstatus;

  function displayonpanel(rowid,columnid,value) {
    angular.element(document).find("#" + $scope.operationplan.id).removeClass("edited").addClass("edited");
    if (typeof $scope.operationplan.id !== 'undefined' && rowid === $scope.operationplan.id.toString()) {
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
