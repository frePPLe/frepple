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
