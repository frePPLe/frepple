/*
 * Copyright (C) 2017 by frePPLe bv
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
  ['ngCookies', 'gettext', 'ngWebSocket', 'frepple.input', 'frepple.common', 'calendar'],
  ['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode({ enabled: true, requireBase: false });
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

operationplandetailapp.filter('formatdate', function () {
  return function (datestr) {
    if (moment.isMoment(datestr))
      return datestr.format(dateformat);
    else if (datestr && typeof (datestr) !== "undefined")
      return moment(datestr, datetimeformat).format(dateformat);
  };
});

operationplandetailapp.filter('formatdatetime', function () {
  return function (datestr) {
    if (moment.isMoment(datestr))
      return datestr.format(datetimeformat);
    else if (datestr && typeof (datestr) !== "undefined")
      return moment(datestr, datetimeformat).format(datetimeformat);
  };
});


operationplandetailapp.filter('formatnumber', function () {
  return function (nData, maxdecimals = 6) {
    // Number formatting function copied from free-jqgrid.
    // Adapted to show a max number of decimal places.
    if (typeof (nData) === 'undefined')
      return '';
    var isNumber = $.fmatter.isNumber;
    if (!isNumber(nData))
      nData *= 1;
    if (isNumber(nData)) {
      var bNegative = (nData < 0);
      var absData = Math.abs(nData);
      var sOutput;
      if (absData > 100000 || maxdecimals <= 0)
        sOutput = String(parseFloat(nData.toFixed()));
      else if (absData > 10000 || maxdecimals <= 1)
        sOutput = String(parseFloat(nData.toFixed(1)));
      else if (absData > 1000 || maxdecimals <= 2)
        sOutput = String(parseFloat(nData.toFixed(2)));
      else if (absData > 100 || maxdecimals <= 3)
        sOutput = String(parseFloat(nData.toFixed(3)));
      else if (absData > 10 || maxdecimals <= 4)
        sOutput = String(parseFloat(nData.toFixed(4)));
      else if (absData > 1 || maxdecimals <= 5)
        sOutput = String(parseFloat(nData.toFixed(5)));
      else
        sOutput = String(parseFloat(nData.toFixed(maxdecimals)));
      var sDecimalSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
      if (sDecimalSeparator !== ".")
        // Replace the "."
        sOutput = sOutput.replace(".", sDecimalSeparator);
      var sThousandsSeparator = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
      if (sThousandsSeparator) {
        var nDotIndex = sOutput.lastIndexOf(sDecimalSeparator);
        nDotIndex = (nDotIndex > -1) ? nDotIndex : sOutput.length;
        // we cut the part after the point for integer numbers
        // it will prevent storing/restoring of wrong numbers during inline editing
        var sNewOutput = sDecimalSeparator === undefined ? "" : sOutput.substring(nDotIndex);
        var nCount = -1, i;
        for (i = nDotIndex; i > 0; i--) {
          nCount++;
          if ((nCount % 3 === 0) && (i !== nDotIndex) && (!bNegative || (i > 1))) {
            sNewOutput = sThousandsSeparator + sNewOutput;
          }
          sNewOutput = sOutput.charAt(i - 1) + sNewOutput;
        }
        sOutput = sNewOutput;
      }
      return sOutput;
    }
    return nData;
  };
});