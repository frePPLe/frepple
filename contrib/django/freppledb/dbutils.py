#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net

from django.conf import settings
from datetime import date, datetime

# Note: Django also includes a set of wrapper functions around incompatible
# database functionality. A seperate one was required to add functions and
# enhance others.
#  - sql_datediff:
#    Returns the time diffence between 2 datetime values, expressed in days.
#  - sql_overlap:
#    Returns the overlap between 2 date ranges, expressed in days.
#  - sql_min:
#    Returns the maximum of 2 numbers.
#  - sql_max:
#    Returns the minimum of 2 numbers.
#  - python_date:
#    A date database field is represented differently by the different
#    database connectors.
#    Oracle returns a python datetime object.
#    SQLite returns a string.
#    PostgreSQL and mySQL both return a date object.
#    This method does what one might intuitively expect: a date field in the
#    database is always returned as a python date object.

# Functions for SQLITE
if settings.DATABASE_ENGINE == 'sqlite3':

  def sql_true():
    return '1'

  def sql_datediff(d1, d2):
    return "((strftime('%%%%s',%s) - strftime('%%%%s',%s)) / 86400.0)" % (d1,d2)

  def sql_overlap(s1, e1, s2, e2):
    return "max(0,((" \
      "min(strftime('%%%%s',%s),strftime('%%%%s',%s)) - " \
      "max(strftime('%%%%s',%s),strftime('%%%%s',%s)) " \
      ")) / 86400.0)" % (e1,e2,s1,s2)

  def sql_max(d1, d2):
    return "max(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "min(%s,%s)" % (d1,d2)

  def python_date(d):
    return datetime.strptime(d,'%Y-%m-%d').date()

# Functions for POSTGRESQL
elif settings.DATABASE_ENGINE == 'postgresql_psycopg2':

  def sql_true():
    return 'true'

  def sql_datediff(d1, d2):
    return '(extract(epoch from (cast(%s as timestamp) - cast(%s as timestamp))) / 86400)' % (d1,d2)

  def sql_overlap(s1, e1, s2, e2):
    return 'greatest(0,extract(epoch from ' \
      '(least(cast(%s as timestamp),cast(%s as timestamp)) ' \
      ' - greatest(cast(%s as timestamp),cast(%s as timestamp)))) / 86400)' % (e1,e2,s1,s2)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

  def python_date(d):
    return d

# Functions for MYSQL
elif settings.DATABASE_ENGINE == 'mysql':

  def sql_true():
    return '1'

  def sql_datediff(d1,d2):
    return 'datediff(%s,%s)' % (d1,d2)

  def sql_overlap(s1,e1,s2,e2):
    return 'greatest(0,datediff(least(%s,%s), greatest(%s,%s)))' % (e1,e2,s1,s2)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

  def python_date(d):
    return d

# Functions for ORACLE
elif settings.DATABASE_ENGINE == 'oracle':

  def sql_true():
    return '1'

  def sql_datediff(d1,d2):
    # Ridiculously complex code. Bad marks for Oracle!
    # Straightforward subtraction gives use an "interval" data type, from which it is hard to extract the total time as a number.
    # We force subtracting 2 dates, which does give the difference in days
    return "(to_date(to_char(%s,'MM/DD/YYYY HH:MI:SS'),'MM/DD/YYYY HH:MI:SS') - to_date(to_char(%s,'MM/DD/YYYY HH:MI:SS'),'MM/DD/YYYY HH:MI:SS') )" % (d1,d2)

  def sql_overlap(s1,e1,s2,e2):
    # Ridiculously complex code. Bad marks for Oracle!
    return "greatest(0,to_date(to_char(least(%s,%s),'MM/DD/YYYY HH:MI:SS'),'MM/DD/YYYY HH:MI:SS') - to_date(to_char(greatest(%s,%s),'MM/DD/YYYY HH:MI:SS'),'MM/DD/YYYY HH:MI:SS') )" % (e1,e2,s1,s2)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

  def python_date(d):
    return d.date()

else:
  raise NameError('The %s database is not support by frePPLe' % settings.DATABASE_ENGINE)
