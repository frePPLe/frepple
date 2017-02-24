/*
 * Copyright (C) 2017 by frePPLe bvba
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

'use strict';

var operationplandetailapp = angular.module('operationplandetailapp',
  ['ngCookies', 'gettext', 'ngWebSocket', 'frepple.input', 'frepple.common'],
  ['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode({enabled: true, requireBase: false});
}]);

operationplandetailapp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);

operationplandetailapp.run(['gettextCatalog', function (gettextCatalog) {
    gettextCatalog.setCurrentLanguage(language);
    //gettextCatalog.debug = true; //show missing label on untranslated strings
}]);

operationplandetailapp.filter('formatdate', function(){
  return function(datestr){
    if (typeof(datestr) !== "undefined" ){
      return moment(datestr).format("YYYY-MM-DD HH:mm:ss");
    }
  };
});
