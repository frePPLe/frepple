/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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
