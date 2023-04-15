#
# Copyright (C) 2017 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.db import DEFAULT_DB_ALIAS


def getERPconnection(database=DEFAULT_DB_ALIAS):
    """
    Customize this method to connect to the ERP database.

    The example here uses Microsoft ADO to connect from a windows machine to a database.
    The site https://www.connectionstrings.com/ has a handy summary of the syntax of the
    connection strings.

    To improve configurability of the connector we can use either:
      a) Parameters stored in the frePPLe parameter table.
         Benefit is that end user can then easily change these.
      b) Settings in the frePPLe djangosettings file.
         For storing password and other security sensitive information this file is better.
    """
    import adodbapi

    connectionstring = "Provider=SQLNCLI11;Server=localhost;Database=acutec;User Id=acutec;Password=acutec;"
    return adodbapi.connect(connectionstring, timeout=600)
