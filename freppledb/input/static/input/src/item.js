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
