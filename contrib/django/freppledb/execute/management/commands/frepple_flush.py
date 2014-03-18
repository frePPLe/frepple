#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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
from django.db.models.loading import get_model

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
    make_option('--models', dest='models', type='string',
      help='Comma-separated list of models to erase')
    )

  requires_model_validation = False

  def get_version(self):
    return VERSION

  def handle(self, **options):
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
    if 'models' in options and options['models']:
      models = options['models'].split(',')
    else:
      models = None

    now = datetime.now()
    transaction.enter_transaction_management(using=database)
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

      # Get a list of all django tables in the database
      tables = set(connections[database].introspection.django_table_names(only_existing=True))

      # Validate the user list of tables
      if models:
        models2tables = set()
        for m in models:
          try:
            x = m.split('.',1)
            x = get_model(x[0], x[1])._meta.db_table
            if not x in tables: raise
            models2tables.add(x)
          except Exception as e:
            raise CommandError("Invalid model to erase: %s" % m)
        tables = models2tables

      # Some tables need to be handled a bit special
      if "common_bucket" in tables:
        cursor.execute('update common_user set horizonbuckets = null')
      tables.discard('auth_group_permissions')
      tables.discard('auth_permission')
      tables.discard('auth_group')
      tables.discard('django_session')
      tables.discard('common_user')
      tables.discard('common_user_groups')
      tables.discard('common_user_user_permissions')
      tables.discard('django_content_type')
      tables.discard('execute_log')
      tables.discard('execute_scenario')
      transaction.commit(using=database)

      # Delete all records from the tables.
      for stmt in connections[database].ops.sql_flush(no_style(), tables, []):
        cursor.execute(stmt)
      transaction.commit(using=database)

      # SQLite specials
      if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
        cursor.execute('vacuum')   # Shrink the database file

      # Task update
      task.status = 'Done'
      task.finished = datetime.now()
      task.save(using=database)
      transaction.commit(using=database)

    except Exception as e:
      transaction.rollback()
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
        task.save(using=database)
        transaction.commit(using=database)
      raise CommandError('%s' % e)

    finally:
      transaction.leave_transaction_management(using=database)
