/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module('frepple.input').factory('Location', LocationFactory);

LocationFactory.$inject = ['$http', 'getURLprefix'];

function LocationFactory($http, getURLprefix) {  
  
  var debug = false;
  
  function Location(data) {
    if (data)
     this.extend(data);
  };
  
  Location.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove  
  };
  
  return Location;
  
  function extend(data) {
    angular.extend(this, data);
  };
  
  //REST API GET
  function get() {
    var loc = this;
    return $http
      .get(getURLprefix() + '/api/input/location/' + encodeURIComponent(loc.name) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Location get '" + loc.name + "': ", response.data);
          loc.extend(response.data);
          return loc;
          }
        );
  };
  
  // REST API PUT
  function save() {
    var loc = this;
    return $http
      .put(getURLprefix() + '/api/input/location/' + encodeURIComponent(loc.name) + "/", loc)
      .then(
        function (response) {
          if (debug) 
            console.log("Location save '" + loc.name + "': ", response.data);
          loc.extend(response.data);
          return loc;
          }
        );
  };
  
  // REST API DELETE
  function remove() {
    var loc = this;
    return $http
      .delete(getURLprefix() + '/api/input/location/' + encodeURIComponent(loc.name) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Location delete '" + loc.name + "': ", response.data);
          return loc;
          });
  };
};