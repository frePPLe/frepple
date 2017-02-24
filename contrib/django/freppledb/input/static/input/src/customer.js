/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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