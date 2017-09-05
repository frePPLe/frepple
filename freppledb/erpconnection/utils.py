#
# Copyright (C) 2017 by frePPLe bvba
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

from django.db import DEFAULT_DB_ALIAS


def getERPconnection(database=DEFAULT_DB_ALIAS):
  '''
  Customize this method to connect to the ERP database.

  The example here uses Microsoft ADO to connect from a windows machine to a database.
  The site https://www.connectionstrings.com/ has a handy summary of the syntax of the
  connection strings.

  To improve configurability of the connector we can use either:
    a) Parameters stored in the frePPLe parameter table.
       Benefit is that end user can then easily change these.
    b) Settings in the frePPLe djangosettings file.
       For storing password and other security sensitive information this file is better.
  '''
  import adodbapi
  connectionstring = 'Provider=SQLNCLI11;Server=localhost;Database=acutec;User Id=acutec;Password=acutec;'
  return adodbapi.connect(connectionstring, timeout=600)
