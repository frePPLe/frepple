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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
This module holds a number of functions that are useful to make SQL statements
portable across different databases.

Django also includes a set of wrapper functions around incompatible
database functionality. A seperate one was required to add functions and 
enhance others.
  - sql_datediff:
    Returns the time diffence between 2 datetime values, expressed in days.
  - sql_overlap:
    Returns the overlap between 2 date ranges, expressed in days.
  - sql_min:
    Returns the maximum of 2 numbers.
  - sql_max:
    Returns the minimum of 2 numbers.
  - python_date:
    A datetime database field is represented differently by the different
    database connectors.
    Oracle, PostgreSQL and mySQL return a python datetime object.
    SQLite returns a string.
    This method does what one might intuitively expect: a python date object
    is always returned.
'''

from django.conf import settings
from datetime import date, datetime

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

  def sql_overlap3(s1, e1, s2, e2, s3, e3):
    return "max(0,((" \
      "min(strftime('%%%%s',%s),strftime('%%%%s',%s),strftime('%%%%s',%s)) - " \
      "max(strftime('%%%%s',%s),strftime('%%%%s',%s),strftime('%%%%s',%s)) " \
      ")) / 86400.0)" % (e1,e2,e3,s1,s2,s3)

  def sql_max(d1, d2):
    return "max(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "min(%s,%s)" % (d1,d2)

  def python_date(d):
    if isinstance(d,datetime): return d.date()
    return datetime.strptime(d,'%Y-%m-%d %H:%M:%S').date()

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

  def sql_overlap3(s1, e1, s2, e2, s3, e3):
    return 'greatest(0,extract(epoch from ' \
      '(least(cast(%s as timestamp),cast(%s as timestamp),cast(%s as timestamp)) ' \
      ' - greatest(cast(%s as timestamp),cast(%s as timestamp),cast(%s as timestamp)))) / 86400)' % (e1,e2,e3,s1,s2,s3)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

  def python_date(d):
    return d.date()

# Functions for MYSQL
elif settings.DATABASE_ENGINE == 'mysql':

  def sql_true():
    return '1'

  def sql_datediff(d1,d2):
    return 'timestampdiff(second,%s,%s)/86400' % (d2,d1)

  def sql_overlap(s1,e1,s2,e2):
    return 'greatest(0,timestampdiff(second,greatest(%s,%s),least(%s,%s)))/86400' % (s1,s2,e1,e2)

  def sql_overlap3(s1,e1,s2,e2,s3,e3):
    return 'greatest(0,timestampdiff(second,greatest(%s,%s,%s),least(%s,%s,%s)))/86400' % (s1,s2,s3,e1,e2,e3)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

  def python_date(d):
    return d.date()

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

  def sql_overlap3(s1,e1,s2,e2,s3,e3):
    # Ridiculously complex code. Bad marks for Oracle!
    return "greatest(0,to_date(to_char(least(%s,%s,%s),'MM/DD/YYYY HH:MI:SS'),'MM/DD/YYYY HH:MI:SS') - to_date(to_char(greatest(%s,%s,%s),'MM/DD/YYYY HH:MI:SS'),'MM/DD/YYYY HH:MI:SS') )" % (e1,e2,e3,s1,s2,s3)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

  def python_date(d):
    return d.date()

else:
  raise NameError('The %s database is not support by frePPLe' % settings.DATABASE_ENGINE)
