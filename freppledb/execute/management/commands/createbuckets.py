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

from datetime import timedelta, datetime, date

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.template import Template, RequestContext

from freppledb.common.models import Bucket, BucketDetail
from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):

  help = '''
  This command initializes the date bucketization table in the database.
  '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--start', default='2014-1-1',
      help='Start date in YYYY-MM-DD format'
      )
    parser.add_argument(
      '--end', default='2021-1-1',
      help='End date in YYYY-MM-DD format'
      )
    parser.add_argument(
      '--weekstart', type=int, default=1,
      choices=[0, 1, 2, 3, 4, 5, 6],
      help='First day of a week: 0=sunday, 1=monday (default), 2=tuesday, 3=wednesday, 4=thursday, 5=friday, 6=saturday'
      ),
    parser.add_argument(
      '--format-day', default='%Y-%m-%d',
      help='Format template for a daily bucket'
      ),
    parser.add_argument(
      '--format-week', default='%y W%W',
      help='Format template for a weekly bucket'
      ),
    parser.add_argument(
      '--format-month', default='%b %y',
      help='Format template for a monthly bucket'
      ),
    parser.add_argument(
      '--format-quarter', default='%y Q%q',
      help='Format template for a quarterly bucket'
      ),
    parser.add_argument(
      '--format-year', default='%Y',
      help='Format template for a yearly bucket'
      ),
    parser.add_argument(
      '--user',
      help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to populate date information into'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )


  def formatDate(self, curdate, template):
    fmt = template
    if "%q" in fmt:
      month = int(curdate.strftime("%m"))  # an integer in the range 1 - 12
      quarter = (month - 1) // 3 + 1       # an integer in the range 1 - 4
      fmt = fmt.replace("%q", str(quarter))
    return curdate.strftime(fmt)


  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up the options
    start = options['start']
    end = options['end']
    weekstart = int(options['weekstart'])
    database = options['database']
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    if options['user']:
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
      if options['task']:
        try:
          task = Task.objects.all().using(database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_createbuckets', 'createbuckets'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='createbuckets', submitted=now, started=now, status='0%', user=user, arguments="--start=%s --end=%s --weekstart=%s" % (start, end, weekstart))
      task.save(using=database)

      # Validate the date arguments
      try:
        curdate = datetime.strptime(start, '%Y-%m-%d')
        enddate = datetime.strptime(end, '%Y-%m-%d')
      except Exception as e:
        raise CommandError("Date is not matching format YYYY-MM-DD")

      with transaction.atomic(using=database, savepoint=False):
        # Delete previous contents
        with connections[database].cursor() as cursor:
          cursor.execute(
            "delete from common_bucketdetail where bucket_id in ('year','quarter','month','week','day')"
            )
          cursor.execute(
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

          # Create buckets
          if year != prev_year:
            prev_year = year
            BucketDetail(
              bucket=y,
              name=self.formatDate(curdate, options['format_year']),
              startdate=year_start,
              enddate=year_end
              ).save(using=database)
          if quarter != prev_quarter:
            prev_quarter = quarter
            BucketDetail(
              bucket=q,
              name=self.formatDate(curdate, options['format_quarter']),
              startdate=date(year, quarter * 3 - 2, 1),
              enddate=date(year + quarter // 4, quarter * 3 + 1 - 12 * (quarter // 4), 1)
              ).save(using=database)
          if month != prev_month:
            prev_month = month
            BucketDetail(
              bucket=m,
              name=self.formatDate(curdate, options['format_month']),
              startdate=date(year, month, 1),
              enddate=date(year + month // 12, month + 1 - 12 * (month // 12), 1),
              ).save(using=database)
          if week_start != prev_week:
            prev_week = week_start
            # we need to avoid weeks 00
            # we will therefore take the name of the week starting the monday
            # included in that week
            BucketDetail(
              bucket=w,
              name=self.formatDate(
                week_start + timedelta(days=(7 - week_start.weekday()) % 7),
                options['format_week']
                ),
              startdate=week_start,
              enddate=week_end,
              ).save(using=database)
          BucketDetail(
            bucket=d,
            name=self.formatDate(curdate.date(), options['format_day']),
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


  # accordion template
  title = _('Generate buckets')
  index = 2000
  help_url = 'user-guide/command-reference.html#createbuckets'

  @ staticmethod
  def getHTML(request):

    if request.user.has_perm('auth.run_db'):
      javascript = '''
        iconslist = {
            time: 'fa fa-clock-o',
            date: 'fa fa-calendar',
            up: 'fa fa-chevron-up',
            down: 'fa fa-chevron-down',
            previous: 'fa fa-chevron-left',
            next: 'fa fa-chevron-right',
            today: 'fa fa-bullseye',
            clear: 'fa fa-trash',
            close: 'fa fa-close'
          };
        // Date picker
        $(".vDateField").on('focusin', function() {
          $(this).parent().css('position', 'relative');
          $(this).datetimepicker({format: 'YYYY-MM-DD', calendarWeeks: true, icons: iconslist, locale: document.documentElement.lang});
        });

        $("#weekstartul li a").click(function(){
          $("#weekstart1").html($(this).text() + ' <span class="caret"></span>');
          $("#weekstart").val($(this).parent().index());
        });
      '''
      context = RequestContext(request, {'javascript': javascript})

      template = Template('''
        {%% load i18n %%}
        <form class="form-horizontal" role="form" method="post" action="{{request.prefix}}/execute/launch/createbuckets/">{%% csrf_token %%}
        <input type="hidden" name="weekstart" id="weekstart" value="1">
        <table>
          <tr>
            <td style="vertical-align:top; padding: 15px">
              <button class="btn btn-primary" type="submit" value="{%% trans "launch"|capfirst %%}">{%% trans "launch"|capfirst %%}</button>
            </td>
            <td style="padding: 15px; width:99%%">
            %s
            </td>
          </tr>
        </table>
        </form>
        <script>{{ javascript|safe }}</script>
      ''' % (
        force_text(_('''<p>Create time buckets for reporting.</p>
          <div class="form-group">
          <label class="col-sm-3 control-label">Start date</label>
          <div class="col-sm-9">
          <input class="vDateField form-control" id="start" name="start" type="text" size="12"/>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label">End date</label>
          <div class="col-sm-9">
          <input class="vDateField form-control" id="end" name="end" type="text" size="12"/>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label" for="weekstart1">Week starts on</label>
          <div class="col-sm-9">
          <div class="dropdown dropdown-submit-input">
            <button class="btn btn-default dropdown-toggle form-control"  id="weekstart1" value="1" type="button" data-toggle="dropdown">Monday&nbsp;&nbsp;<span class="caret"></span></button>
            <ul class="dropdown-menu col-xs-12" aria-labelledby="weekstart1" id="weekstartul">
              <li><a>Sunday</a></li>
              <li><a>Monday</a></li>
              <li><a>Tuesday</a></li>
              <li><a>Wednesday</a></li>
              <li><a>Thursday</a></li>
              <li><a>Friday</a></li>
              <li><a>Saturday</a></li>
            </ul>
          </div>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label">Day name</label>
          <div class="col-sm-9">
          <input class="form-control" name="format-day" type="text" size="12" value="%Y-%m-%d"/>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label">Week name</label>
          <div class="col-sm-9">
          <input class="form-control" name="format-week" type="text" size="12" value="%y W%W"/>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label">Month name</label>
          <div class="col-sm-9">
          <input class="form-control" name="format-month" type="text" size="12" value="%b %y"/>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label">Quarter format</label>
          <div class="col-sm-9">
          <input class="form-control" name="format-quarter" type="text" size="12" value="%y Q%q"/>
          </div>
          </div>
          <div class="form-group">
          <label class="col-sm-3 control-label">Year format</label>
          <div class="col-sm-9">
          <input class="form-control" name="format-year" type="text" size="12" value="%Y"/>
          </div>
          </div>
          '''))
        ))
      return template.render(context)
      # A list of translation strings from the above
      translated = (
        _("launch"), _("data tables"), _("admin tables"),
        _("Erase selected tables.")
        )
    else:
      return None
