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

angular.module('frepple.input').factory('Operation', OperationFactory);

OperationFactory.$inject = ['$http', 'getURLprefix', 'Location'];

function OperationFactory($http, getURLprefix, Location) {

  var debug = false;

  function Operation(data) {
    if (data)
      this.extend(data);
  };

  Operation.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Operation;

  function extend(data) {
    angular.forEach(data, function(value, key) {
      switch (key) {
        case "location":
          if (value && !value instanceof Location)
            data['location'] = new Location(value);
          break;
      };
    });
    angular.extend(this, data);
  }

  //REST API GET
  function get() {
    var oper = this;
    return $http
      .get(getURLprefix() + '/api/input/operation/' + encodeURIComponent(oper.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Operation get '" + oper.name + "': ", response.data);
          oper.extend(response.data);
          return oper;
          }
        );
  };

  // REST API PUT
  function save() {
    var oper = this;
    return $http
      .put(getURLprefix() + '/api/input/operation/' + encodeURIComponent(oper.name) + "/", oper)
      .then(
        function (response) {
          if (debug)
            console.log("Operation save '" + oper.name + "': ", response.data);
          oper.extend(response.data);
          return oper;
          }
        );
  };

  // REST API DELETE
  function remove() {
    var oper = this;
    return $http
      .delete(getURLprefix() + '/api/input/operation/' + encodeURIComponent(oper.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Operation delete '" + oper.name + "': ", response.data);
          return oper;
          }
        );
  };
};
