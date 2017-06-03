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

angular.module('frepple.input').factory('Customer', CustomerFactory);

CustomerFactory.$inject = ['$http', 'getURLprefix'];

function CustomerFactory ($http, getURLprefix) {

  var debug = false;

  function Customer(data) {
    if (data)
      angular.extend(this, data);
  };

  Customer.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove
  };

  return Customer;

  function extend(data) {
    angular.extend(this, data);
  };

  // REST API GET
  function get() {
    var cst = this;
    return $http
      .get(getURLprefix() + '/api/input/customer/' + encodeURIComponent(cst.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Customer get '" + cst.name + "': ", response.data);
          cst.extend(response.data);
          return cst;
          }
        );
  };

  // REST API PUT
  function save() {
    var cst = this;
    return $http
      .put(getURLprefix() + '/api/input/customer/' + encodeURIComponent(cst.name) + "/", cst)
      .then(
        function (response) {
          if (debug)
            console.log("Customer save '" + cst.name + "': ", response.data);
          cst.extend(response.data);
          return cst;
          }
        );
  };

  // REST API DELETE
  function remove() {
    var cst = this;
    return $http
      .delete(getURLprefix() + '/api/input/customer/' + encodeURIComponent(cst.name) + "/")
      .then(
        function (response) {
          if (debug)
            console.log("Customer delete '" + itm.name + "': ", response.data);
          return cst;
          }
        );
  };
};
