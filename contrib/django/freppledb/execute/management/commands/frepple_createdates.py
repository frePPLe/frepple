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

#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$
#  email    : jdetaeye@users.sourceforge.net

import random
from optparse import make_option
from datetime import timedelta, datetime, date

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from django.utils.translation import ugettext as _

from input.models import *
from execute.models import log


class Command(BaseCommand):

  help = '''
  This command initiliazes the date bucketization table in the database.
  '''

  option_list = BaseCommand.option_list + (
      make_option('--start', dest='start',
          type='string', default='2006-1-1',
          help='Start date in YYYY-MM-DD format'),
      make_option('--end', dest='end',
          type='string', default='2010-1-1',
          help='End date in YYYY-MM-DD format'),
      make_option('--user', dest='user', default='',
          type='string', help='User running the command'),
  )

  requires_model_validation = False

  def get_version(self):
    return settings.FREPPLE_VERSION


  @transaction.commit_manually
  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up the date arguments
    try:
      curdate = datetime.strptime(options['start'],'%Y-%m-%d')
      end = datetime.strptime(options['end'],'%Y-%m-%d')
    except Exception, e:
      print "Error: date is not matching format YYYY-MM-DD"
      return

    try:
      # Logging the action
      log( category = 'CREATE', user = options['user'],
        message = _('Initializing dates')).save()

      # Performance improvement for sqlite during the bulky creation transactions
      if settings.DATABASE_ENGINE == 'sqlite3':
        connection.cursor().execute('PRAGMA synchronous=OFF')

      # Delete the previous set of records
      connection.cursor().execute('DELETE FROM dates')
      transaction.commit()

      # Loop over all days in the chosen horizon
      while curdate < end:
        month = int(curdate.strftime("%m"))  # an integer in the range 1 - 12
        quarter = (month-1) / 3 + 1          # an integer in the range 1 - 4
        year = int(curdate.strftime("%Y"))
        dayofweek = int(curdate.strftime("%w")) # day of the week, 0 = sunday, 1 = monday, ...

        # Main entry
        Dates(
          day = curdate,
          day_start = curdate,
          day_end = curdate + timedelta(1),
          dayofweek = dayofweek,
          week = curdate.strftime("%y W%W"),     # Weeks are starting on monday
          week_start = curdate - timedelta((dayofweek+6)%7),
          week_end = curdate - timedelta((dayofweek+6)%7-7),
          month =  curdate.strftime("%b %y"),
          month_start = date(year, month, 1),
          month_end = date(year+month/12, month+1-12*(month/12), 1),
          quarter = "%02d Q%s" % (year-2000,quarter),
          quarter_start = date(year, quarter*3-2, 1),
          quarter_end = date(year+quarter/4, quarter*3+1-12*(quarter/4), 1),
          year = curdate.strftime("%Y"),
          year_start = date(year,1,1),
          year_end = date(year+1,1,1),
          ).save()

        # Next date
        curdate = curdate + timedelta(1)

      # Log success
      log(category='CREATE', user = options['user'],
        message=_('Finished initializing dates')).save()

    except Exception, e:
      # Log failure and rethrow exception
      log(category='CREATE', user = options['user'],
        message=u'%s: %s' % (_('Failure initializing dates'),e)).save()
      raise e

    finally:
      # Commit it all, even in case of exceptions
      transaction.commit()
      settings.DEBUG = tmp_debug
