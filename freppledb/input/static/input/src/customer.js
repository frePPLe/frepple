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

angular.module('frepple.input').factory('Customer', CustomerFactory);

CustomerFactory.$inject = ['$http', 'getURLprefix'];

function CustomerFactory($http, getURLprefix) {

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
