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
