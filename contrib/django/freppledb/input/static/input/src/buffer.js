/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module('frepple.input').factory('Buffer', BufferFactory);

BufferFactory.$inject = ['$http', 'getURLprefix', 'Item', 'Location'];

function BufferFactory ($http, getURLprefix, Item, Location) {  
  
  var debug = false;
  
  function Buffer(data) {
    if (data) 
      this.extend(data);
  };
  
  Buffer.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove 
  };
  
  return Buffer;

  function extend(data) {
    angular.forEach(data, function(value, key) {
      switch (key) {
        case "location":
          if (value && !value instanceof Location)
            data['location'] = new Location(value);
          break;
        case "item":
          if (value && !value instanceof Item)
            data['item'] = new Location(value);
          break;
        };
      });
    angular.extend(this, data);
  };

  // REST API GET
  function get() {
    var buf = this;
    return $http
      .get(getURLprefix() + '/api/input/buffer/' + encodeURIComponent(buf.name) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Buffer get '" + buf.name + "': ", response.data);
          buf.extend(response.data);
          return buf;
          }
        );
  };
  
  // REST API PUT
  function save() {
    var buf = this;
    return $http
      .put(getURLprefix() + '/api/input/buffer/' + encodeURIComponent(buf.name) + "/", buf)
      .then(
        function (response) {
          if (debug) 
            console.log("Buffer save '" + buf.name + "': ", response.data);
          buf.extend(response.data);
          return buf;
          }
        );
  };
  
  // REST API DELETE
  function remove() {
    var buf = this;
    return $http
      .delete(getURLprefix() + '/api/input/buffer/' + encodeURIComponent(buf.name) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Buffer delete '" + buf.name + "': ", response.data);
          return buf;
          }
        );
  };
};