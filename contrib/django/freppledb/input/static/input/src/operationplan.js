/*
 * Copyright (C) 2017 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module('frepple.input').factory('OperationPlan', OperationPlanFactory);

OperationPlanFactory.$inject = ['$http', 'getURLprefix', 'Operation', 'Location', 'Item'];

function OperationPlanFactory($http, getURLprefix, Operation, Location, Item) {

  var debug = true;

  function OperationPlan(data) {
    if (data) {
      this.extend(data);
    }
  }

  function extend(data) {
    angular.forEach(data, function(value, key) {
      switch (key) {
        case "operation":
          if (value && !value instanceof Operation) {
            data['operation'] = new Operation(value);
          }
          break;

        case "location":
          if (value && !value instanceof Location) {
            data['demand'] = new Location(value);
          }
          break;

        case "item":
          if (value && !value instanceof Item) {
            data['item'] = new Item(value);
          }
          break;
      }
    });
    angular.extend(this, data);
  }

  //REST API GET
  function get() {
    var operplan = this;//console.log(getURLprefix() + '/operationplan/?encodeURIComponent(operplan.id)');
    return $http
      .get(getURLprefix() + '/operationplan/?id=' + encodeURIComponent(operplan.id))
      .then(
        function (response) {
          if (debug) {
            console.log("Operation get '" + operplan.id + "': ", response.data);
          }
          operplan.extend(response.data[0]);
          return operplan;
        }
      );
  }

  // REST API PUT
  function save() {
    var operplan = this;
    return $http
      .put(getURLprefix() + '/api/input/operationplan/?id=' + encodeURIComponent(operplan.name), operplan)
      .then(
        function (response) {
          if (debug)  {
            console.log("OperationPlan save '" + operplan.name + "': ", response.data);
          }
          operplan.extend(response.data);
          return operplan;
          }
        );
  }

  // REST API DELETE
  function remove() {
    var operplan = this;
    return $http
      .delete(getURLprefix() + '/api/input/operationplan/?id=' + encodeURIComponent(operplan.name))
      .then(
        function (response) {
          if (debug) {
            console.log("OperationPlan delete '" + operplan.name + "': ", response.data);
          }
          return operplan;
          }
        );
  }

  OperationPlan.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };
  return OperationPlan;
}
