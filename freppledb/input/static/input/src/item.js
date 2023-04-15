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

angular.module('frepple.input').factory('Item', ItemFactory);

ItemFactory.$inject = ['$http', 'getURLprefix'];

function ItemFactory($http, getURLprefix) {

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
