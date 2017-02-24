/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
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
