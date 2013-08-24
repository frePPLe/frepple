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

import os.path, subprocess, shutil
from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, transaction

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command creates a database dump of the frePPLe database.

  To use this command the following prerequisites need to be met:
    * MySQL:
        - mysqldump and mysql need to be in the path
    * PostgreSQL:
       - pg_dump and psql need to be in the path
       - The passwords need to be specified upfront in a file ~/.pgpass
    * SQLite:
       - none
    * Oracle:
       - impdp and expdp need to be in the path
       - The DBA has to create a server side directory, pointing to the directory configured as
         FREPPLE_LOGDIR. The oracle user will need to be granted rights to it:
           CREATE OR REPLACE DIRECTORY frepple_logdir AS 'c:\\temp';
           GRANT READ, WRITE ON DIRECTORY frepple_logdir TO usr1;
       - If the schemas reside on different servers, the DB will need to
         create a database link.
         If the database are on the same server, you might still use the database
         link to avoid create a temporary dump file.
       - Can't run multiple copies in parallel!
  '''
  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates a specific database to backup'),
      make_option('--task', dest='task', type='int',
        help='Task identifier (generated automatically if not provided)'),
      )

  requires_model_validation = False

  def get_version(self):
    return VERSION

  def handle(self, *args, **options):

    # Pick up the options
    if 'database' in options:
      database = options['database'] or DEFAULT_DB_ALIAS
    else:
      database = DEFAULT_DB_ALIAS
    if not database in settings.DATABASES.keys():
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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'restore database':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='restore database', submitted=now, started=now, status='0%', user=user)
      task.arguments = args and args[0] or None
      task.save(using=database)
      transaction.commit(using=database)

      # Validate options
      if not args:
        raise CommandError("No dump file specified")
      if not os.path.isfile(os.path.join(settings.FREPPLE_LOGDIR,args[0])):
        raise CommandError("Dump file not found")

      # Run the restore command
      if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
        # SQLITE
        shutil.copy2(os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR,args[0])), settings.DATABASES[database]['NAME'])
      elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.mysql':
        # MYSQL
        cmd = [ 'mysql',
            '--password=%s' % settings.DATABASES[database]['PASSWORD'],
            '--user=%s' % settings.DATABASES[database]['USER']
            ]
        if settings.DATABASES[database]['HOST']:
          cmd.append("--host=%s " % settings.DATABASES[database]['HOST'])
        if settings.DATABASES[database]['PORT']:
          cmd.append("--port=%s " % settings.DATABASES[database]['PORT'])
        cmd.append(settings.DATABASES[database]['NAME'])
        cmd.append('<%s' % os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR,args[0])))
        ret = subprocess.call(cmd, shell=True)  # Shell needs to be True in order to interpret the < character
        if ret: raise Exception("Run of mysql failed")
      elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.oracle':
        # ORACLE
        if settings.DATABASES[database]['HOST'] and settings.DATABASES[database]['PORT']:
          # The setting 'NAME' contains the SID name
          dsn = "%s/%s@//%s:%s/%s" % (
                settings.DATABASES[database]['USER'],
                settings.DATABASES[database]['PASSWORD'],
                settings.DATABASES[database]['HOST'],
                settings.DATABASES[database]['PORT'],
                settings.DATABASES[database]['NAME']
                )
        else:
          # The setting 'NAME' contains the TNS name
          dsn = "%s/%s@%s" % (
                settings.DATABASES[database]['USER'],
                settings.DATABASES[database]['PASSWORD'],
                settings.DATABASES[database]['NAME']
                )
        cmd = [ "impdp",
          dsn,
          "table_exists_action=replace",
          "nologfile=Y",
          "directory=frepple_logdir",
          "dumpfile=%s" % args[0]
          ]
        ret = subprocess.call(cmd)
        if ret: raise Exception("Run of impdp failed")
      elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        # POSTGRESQL
        cmd = [ "psql", '--username=%s' % settings.DATABASES[database]['USER'] ]
        if settings.DATABASES[database]['HOST']:
          cmd.append("--host=%s" % settings.DATABASES[database]['HOST'])
        if settings.DATABASES[database]['PORT']:
          cmd.append("--port=%s " % settings.DATABASES[database]['PORT'])
        cmd.append(settings.DATABASES[database]['NAME'])
        cmd.append('<%s' % os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR,args[0])))
        ret = subprocess.call(cmd, shell=True) # Shell needs to be True in order to interpret the < character
        if ret: raise Exception("Run of run psql failed")
      else:
        raise Exception('Database backup command not supported for engine %s' % settings.DATABASES[database]['ENGINE'])

      # Task update
      # We need to recreate a new task record, since the previous one is lost during the restoration.
      task = Task(name='restore database', submitted=task.submitted, started=task.started,
            arguments=task.arguments, status='Done', finished=datetime.now(), user=task.user)

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      # Commit it all, even in case of exceptions
      if task: task.save(using=database)
      try: transaction.commit(using=database)
      except: pass
      transaction.leave_transaction_management(using=database)
