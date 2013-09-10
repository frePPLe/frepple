#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command empties the contents of all data tables in the frePPLe database.

  The results are similar to the 'flush input output' command, with the
  difference that some tables are not emptied and some performance related
  tweaks.
  Another difference is that the initial_data fixture is not loaded.
  '''
  option_list = BaseCommand.option_list + (
    make_option('--user', dest='user', type='string',
      help='User running the command'),
    make_option('--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a specific database to delete data from'),
    make_option('--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'),
    )

  requires_model_validation = False

  def get_version(self):
    return VERSION

  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up options
    if 'database' in options:
      database = options['database'] or DEFAULT_DB_ALIAS
    else:
      database = DEFAULT_DB_ALIAS
    if not database in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    if 'user' in options and options['user']:
      try: user = User.objects.all().using(database).get(username=options['user'])
      except: raise CommandError("User '%s' not found" % options['user'] )
    else:
      user = None

    now = datetime.now()
    transaction.enter_transaction_management(using=database)
    transaction.managed(True, using=database)
    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try: task = Task.objects.all().using(database).get(pk=options['task'])
        except: raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'empty database':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='empty database', submitted=now, started=now, status='0%', user=user)
      task.save(using=database)
      transaction.commit(using=database)

      # Create a database connection
      cursor = connections[database].cursor()

      # Delete all records from the tables.
      # We split the tables in groups to speed things up in postgreSQL.
      cursor.execute('update common_user set horizonbuckets = null')
      transaction.commit(using=database)
      tables = [
        ['out_demandpegging'],
        ['out_problem','out_resourceplan','out_constraint'],
        ['out_loadplan','out_flowplan','out_operationplan'],
        ['out_demand',],
        ['demand','customer','resourceskill','skill',
         'setuprule','setupmatrix','resourceload','resource',
         'flow','buffer','operationplan','item',
         'suboperation','operation', # TODO Required to add for enterprise version on postgresql :'forecast','forecastdemand',
         'location','calendarbucket','calendar',],
        ['common_parameter','common_bucketdetail','common_bucket'],
        ['common_comment','django_admin_log'],
        ]
      for group in tables:
        sql_list = connections[database].ops.sql_flush(no_style(), group, [] )
        for sql in sql_list:
          cursor.execute(sql)
          transaction.commit(using=database)

      # SQLite specials
      if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
        cursor.execute('vacuum')   # Shrink the database file

      # Task update
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      if task: task.save(using=database)
      try: transaction.commit(using=database)
      except: pass
      settings.DEBUG = tmp_debug
      transaction.leave_transaction_management(using=database)
