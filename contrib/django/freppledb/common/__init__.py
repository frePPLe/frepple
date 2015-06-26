#
# Copyright (C) 2007-2013 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

r'''
An reusable application that contains common functionality of different
frePPLe data models.

The common functionality handles:
  - user preferences: reporting buckets, report start and end dates, language, csv delimiter
  - breadcrumbs
  - login using the e-mail address
  - generic report framework
  - database utility functions, mainly to handle SQL dates in a portable way
  - date and time bucket definition
  - middleware allowing users to set their preferred language
'''
