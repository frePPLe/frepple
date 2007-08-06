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

# Functions for ORACLE
elif settings.DATABASE_ENGINE == 'oracle':

  def sql_true():
    return 'true'

  def sql_datediff(d1,d2):
    return '(%s - %s)' % (d1,d2)

  def sql_overlap(s1,e1,s2,e2):
    return 'greatest(0,least(%s,%s) - greatest(%s,%s))' % (e1,e2,s1,s2)

  def sql_max(d1, d2):
    return "greatest(%s,%s)" % (d1,d2)

  def sql_min(d1, d2):
    return "least(%s,%s)" % (d1,d2)

else:
  raise NameError('The %s database is not support by frePPLe' % settings.DATABASE_ENGINE)
