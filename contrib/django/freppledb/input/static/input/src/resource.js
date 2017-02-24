/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module('frepple.input').factory('Resource', ResourceFactory);

ResourceFactory.$inject = ['$http', 'getURLprefix', 'Location'];

function ResourceFactory($http, getURLprefix, Location) {  
  
  var debug = false;
  
  function Resource(data) {
    if (data) 
      this.extend(data);
  };
  
  Resource.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove 
  };
  
  return Resource;
  
  function extend(data) {
    angular.forEach(data, function(value, key) {
      switch (key) {
        case "location":
          if (value && !value instanceof Location)
            data['location'] = new Location(value);
          break;
      }
    });
    angular.extend(this, data);
  }

  // REST API GET
  function get() {
    var res = this;
    return $http
      .get(getURLprefix() + '/api/input/resource/' + encodeURIComponent(res) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Resource get '" + res.name + "': ", response.data);
          res.extend(response.data);
          return res;
          }
        );
  };
  
  // REST API PUT
  function save() {
    var res = this;
    return $http
      .put(getURLprefix() + '/api/input/resource/' + encodeURIComponent(red.name) + "/", res)
      .then(
        function (response) {
          if (debug) 
            console.log("Resource save '" + res.name + "': ", response.data);
          res.extend(response.data);
          return res;
          }
        );
  };
  
  // REST API DELETE
  function remove() {
    var res = this;
    return $http
      .delete(getURLprefix() + '/api/input/resource/' + encodeURIComponent(res) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Resource delete '" + res.name + "': ", response.data);
          return res;
          }
        );
  };  
};