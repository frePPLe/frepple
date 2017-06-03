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
