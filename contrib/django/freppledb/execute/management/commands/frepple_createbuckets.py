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

from optparse import make_option
from datetime import timedelta, datetime, date

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.conf import settings

from freppledb.common.models import Bucket, BucketDetail
from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):

  help = '''
  This command initializes the date bucketization table in the database.
  '''

  option_list = BaseCommand.option_list + (
    make_option(
      '--start', dest='start', type='string',
      help='Start date in YYYY-MM-DD format'
      ),
    make_option(
      '--end', dest='end', type='string',
      help='End date in YYYY-MM-DD format'
      ),
    make_option(
      '--weekstart', dest='weekstart', type='int', default=1,
      help='First day of a week: 0=sunday, 1=monday (default), 2=tuesday, 3=wednesday, 4=thursday, 5=friday, 6=saturday'
      ),
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to populate date information into'
      ),
    make_option(
      '--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'
      ),
  )

  requires_system_checks = False

  def get_version(self):
    return VERSION


  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up the options
    if 'start' in options:
      start = options['start'] or '2011-1-1'
    else:
      start = '2011-1-1'
    if 'end' in options:
      end = options['end'] or '2019-1-1'
    else:
      end = '2019-1-1'
    if 'weekstart' in options:
      weekstart = int(options['weekstart'])
      if weekstart < 0 or weekstart > 6:
        raise CommandError("Invalid weekstart %s" % weekstart)
    else:
      weekstart = 1
    if 'database' in options:
      database = options['database'] or DEFAULT_DB_ALIAS
    else:
      database = DEFAULT_DB_ALIAS
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    if 'user' in options and options['user']:
      try:
        user = User.objects.all().using(database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      user = None

    now = datetime.now()
    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try:
          task = Task.objects.all().using(database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'generate buckets':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='generate buckets', submitted=now, started=now, status='0%', user=user, arguments="--start=%s --end=%s --weekstart=%s" % (start, end, weekstart))
      task.save(using=database)

      # Validate the date arguments
      try:
        curdate = datetime.strptime(start, '%Y-%m-%d')
        enddate = datetime.strptime(end, '%Y-%m-%d')
      except Exception as e:
        raise CommandError("Date is not matching format YYYY-MM-DD")

      with transaction.atomic(using=database, savepoint=False):
        # Delete previous contents
        connections[database].cursor().execute(
          "delete from common_bucketdetail where bucket_id in ('year','quarter','month','week','day')"
          )
        connections[database].cursor().execute(
          "delete from common_bucket where name in ('year','quarter','month','week','day')"
          )

        # Create buckets
        y = Bucket(name='year', description='Yearly time buckets', level=1)
        q = Bucket(name='quarter', description='Quarterly time buckets', level=2)
        m = Bucket(name='month', description='Monthly time buckets', level=3)
        w = Bucket(name='week', description='Weeky time buckets', level=4)
        d = Bucket(name='day', description='Daily time buckets', level=5)
        y.save(using=database)
        q.save(using=database)
        m.save(using=database)
        w.save(using=database)
        d.save(using=database)

        # Loop over all days in the chosen horizon
        prev_year = None
        prev_quarter = None
        prev_month = None
        prev_week = None
        while curdate < enddate:
          month = int(curdate.strftime("%m"))  # an integer in the range 1 - 12
          quarter = (month - 1) // 3 + 1       # an integer in the range 1 - 4
          year = int(curdate.strftime("%Y"))
          dayofweek = int(curdate.strftime("%w"))  # day of the week, 0 = sunday, 1 = monday, ...
          year_start = datetime(year, 1, 1)
          year_end = datetime(year + 1, 1, 1)
          week_start = curdate - timedelta((dayofweek + 6) % 7 + 1 - weekstart)
          week_end = curdate - timedelta((dayofweek + 6) % 7 - 6 - weekstart)
          if week_start < year_start:
            week_start = year_start
          if week_end > year_end:
            week_end = year_end

          # Create buckets
          if year != prev_year:
            prev_year = year
            BucketDetail(
              bucket=y,
              name=str(year),
              startdate=year_start,
              enddate=year_end
              ).save(using=database)
          if quarter != prev_quarter:
            prev_quarter = quarter
            BucketDetail(
              bucket=q,
              name="%02d Q%s" % (year - 2000, quarter),
              startdate=date(year, quarter * 3 - 2, 1),
              enddate=date(year + quarter // 4, quarter * 3 + 1 - 12 * (quarter // 4), 1)
              ).save(using=database)
          if month != prev_month:
            prev_month = month
            BucketDetail(
              bucket=m,
              name=curdate.strftime("%b %y"),
              startdate=date(year, month, 1),
              enddate=date(year + month // 12, month + 1 - 12 * (month // 12), 1),
              ).save(using=database)
          if week_start != prev_week:
            prev_week = week_start
            BucketDetail(
              bucket=w,
              name=curdate.strftime("%y W%W"),
              startdate=week_start,
              enddate=week_end,
              ).save(using=database)
          BucketDetail(
            bucket=d,
            name=str(curdate.date()),
            startdate=curdate,
            enddate=curdate + timedelta(1),
            ).save(using=database)

          # Next date
          curdate = curdate + timedelta(1)

      # Log success
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      if task:
        task.save(using=database)
      settings.DEBUG = tmp_debug
