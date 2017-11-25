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
      return moment(Date.parse(datestr)).format("YYYY-MM-DD HH:mm:ss");
    }
  };
});
