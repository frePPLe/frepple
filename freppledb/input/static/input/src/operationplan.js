/*
 * Copyright (C) 2017 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 *
 */

angular.module('frepple.input').factory('OperationPlan', OperationPlanFactory);

OperationPlanFactory.$inject = ['$http', 'getURLprefix', 'Operation', 'Location', 'Item'];

function OperationPlanFactory($http, getURLprefix, Operation, Location, Item) {

  var debug = false;

  function OperationPlan(data) {
    if (data)
      this.extend(data);
  }

  function extend(data) {
    angular.extend(this, data);
  }

  //REST API GET
  function get(callback) {
    var operplan = this;
    if (operplan.id === undefined)
      return operplan;
    else {
      return $http
        .get(getURLprefix() + '/operationplan/?reference=' + encodeURIComponent(operplan.id))
        .then(
          function (response) {
            if (debug) {
              console.log("Operation get '" + operplan.id + "': ");
              console.log(response.data);
            }
            Object.keys(operplan).forEach(key => { if (key !== "dirty") delete operplan[key] });
            operplan.extend(response.data[0]);
            if (typeof callback === 'function') {
              callback(operplan);
            }
            return operplan;
          },
          function (err) {
            if (err.status == 401)
              location.reload();
          }
        );
    }
  }

  // REST API PUT
  function save() {
    var operplan = this;
    return $http
      .put(getURLprefix() + '/api/input/operationplan/?reference=' + encodeURIComponent(operplan.name), operplan)
      .then(
        function (response) {
          if (debug) {
            console.log("OperationPlan save '" + operplan.name + "': ", response.data);
          }
          operplan.extend(response.data);
          return operplan;
        },
        function (err) {
          if (err.status == 401)
            location.reload();
        }
      );
  }

  // REST API DELETE
  function remove() {
    var operplan = this;
    return $http
      .delete(getURLprefix() + '/api/input/operationplan/?reference=' + encodeURIComponent(operplan.name))
      .then(
        function (response) {
          if (debug)
            console.log("OperationPlan delete '" + operplan.name + "': ", response.data);
          return operplan;
        },
        function (err) {
          if (err.status == 401)
            location.reload();
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
