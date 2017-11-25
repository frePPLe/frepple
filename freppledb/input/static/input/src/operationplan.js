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

angular.module('frepple.input').factory('OperationPlan', OperationPlanFactory);

OperationPlanFactory.$inject = ['$http', 'getURLprefix', 'Operation', 'Location', 'Item'];

function OperationPlanFactory($http, getURLprefix, Operation, Location, Item) {

  var debug = false;

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
  function get(callback) {
    var operplan = this;
    if (operplan.id === undefined) {
      return operplan;
    } else {
      return $http
        .get(getURLprefix() + '/operationplan/?id=' + encodeURIComponent(operplan.id))
        .then(
          function (response) {
            if (debug) {
              console.log("Operation get '" + operplan.id + "': ");
              console.log(response.data);
            }
            operplan.extend(response.data[0]);
            if (typeof callback === 'function') {
              callback(operplan);
            }
            return operplan;
          }
        );
    }
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
