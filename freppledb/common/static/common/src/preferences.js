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

angular.module("frepple.common").service("PreferenceSvc", PreferenceSvc);

PreferenceSvc.$inject = ["$http"];

/*
 * This service updates and retrieves user preferences for a certain report.
 * TODO Current implementation completely relies on the "preferences" and "reportkey" global variables passed from django.
 */
function PreferenceSvc($http) {
  'use strict';

  function save(key, value, callback) {
    var data = preferences;
    if (typeof (data) !== 'undefined' && data !== 'None' && data !== null)
      data = angular.fromJson(preferences);
    else
      data = {};

    // Key and value can both be an array to save lists of keys
    // and values with just one call
    if (typeof key === 'object' && key.length === value.length) {
      angular.forEach(key, function (currentKey, index) {
        data[currentKey] = value[index];
      });
    } else
      data[key] = value;

    // Post to the server
    var urlprefix = '/' + angular.element(document).find('#database').attr('name');
    if (urlprefix === '/default' || urlprefix === '/undefined')
      urlprefix = '';
    var tmp = {};
    tmp[reportkey] = data;
    $http.post(urlprefix + '/settings/', angular.toJson(tmp))
      .then(
        function (response) {
          if (typeof callback === 'function')
            callback(response);
        },
        function (response) {
          angular.element(document).find('.modal-body').html('<div style="width: 100%; overflow: auto;">' + response.data + '</div>');
          showModal('popup2');
        }
      );
  };

  function get(key, defaultvalue) {
    var data = preferences;
    if (typeof (data) !== 'undefined' && data !== 'None' && data !== null)
      data = angular.fromJson(preferences);
    else
      data = {};
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
