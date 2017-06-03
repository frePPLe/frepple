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

angular.module("frepple.common").service("PreferenceSvc", PreferenceSvc);

PreferenceSvc.$inject = ["$http"];

/*
 * This service updates and retrieves user preferences for a certain report.
 * TODO Current implementation assumes the reportname is fixed and hardcoded.
 * TODO Current implementation depends on the "preferences" variable passed from django.
 */
function PreferenceSvc($http) {
  'use strict';

  // Set initial preferences
  var reportname = 'freppledb.planningboard';
  var data = preferences;
  if (typeof(data) !== 'undefined' && data !== 'None')
    data = angular.fromJson(preferences);
  else
    data = {};

  function save(key, value, callback) {
    // Key and value can both be an array to save lists of keys
    // and values with just one call
    if (typeof key === 'object' && key.length === value.length) {
      angular.forEach(key, function(currentKey,index) {
        data[currentKey] = value[index];
      });
    } else
      data[key] = value;

    // Post to the server
    var urlprefix = '/'+angular.element(document).find('#database').attr('name');
    if (urlprefix === '/default' || urlprefix === '/undefined')
      urlprefix = '';
    var tmp = {};
    tmp[reportname] = data;
    $http.post(urlprefix + '/settings/', angular.toJson(tmp))
      .then(
        function(response) {
          if (typeof callback === 'function')
            callback(response);
        },
        function(response) {
          angular.element(document).find('.modal-body').html('<div style="width: 100%; overflow: auto;">' + response.data + '</div>');
          angular.element(document).find('#popup2').modal('show');
        }
      );
  };

  function get(key, defaultvalue) {
    if (key in data)
      return data[key];
    else
      return defaultvalue;
  };

  var service = {
    get: get,
    save: save
  };
  return service;

};
