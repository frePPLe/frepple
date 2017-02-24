/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module('frepple.input').factory('Item', ItemFactory);

ItemFactory.$inject = ['$http', 'getURLprefix'];

function ItemFactory ($http, getURLprefix) {  
  
  var debug = false;
  
  function Item(data) {
    if (data) 
      this.extend(data);
  };
  
  Item.prototype = {
    extend: extend,
    get: get,
    save: save,
    remove: remove 
  };
  
  return Item;
  
  function extend(data) {
    angular.extend(this, data);
  };

  // REST API GET
  function get() {
    var itm = this;
    return $http
      .get(getURLprefix() + '/api/input/item/' + encodeURIComponent(itm.name) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Item get '" + itm.name + "': ", response.data);
          itm.extend(response.data);
          return itm;
          }
        );
  };
  
  // REST API PUT
  function save() {
    var itm = this;
    return $http
      .put(getURLprefix() + '/api/input/item/' + encodeURIComponent(itm.name) + "/", itm)
      .then(
        function (response) {
          if (debug) 
            console.log("Item save '" + itm.name + "': ", response.data);
          itm.extend(response.data);
          return itm;
          }
        );
  };
  
  // REST API DELETE
  function remove() {
    var itm = this;
    return $http
      .delete(getURLprefix() + '/api/input/item/' + encodeURIComponent(itm.name) + "/")
      .then(
        function (response) {
          if (debug) 
            console.log("Item delete '" + itm.name + "': ", response.data);
          return itm;
          }
        );
  };
};