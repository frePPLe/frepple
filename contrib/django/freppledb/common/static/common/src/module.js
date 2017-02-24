/*
 * Copyright (C) 2016 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

angular.module("frepple.common", []);

// Global variable database is passed from Django. 
angular.module("frepple.common")
  .constant('getURLprefix', function getURLprefix() {
    return database === 'default' ? '' : '/' + database;
    }
  );

// Date formatting filter, expecting a moment instance as input
angular.module("frepple.common")
  .filter('dateTimeFormat', function dateTimeFormat() {
    return function (input, fmt) {
      fmt = fmt || 'YYYY-MM-DD HH:mm:ss';
      return input ? input.format(fmt) : '';
    };
  });
