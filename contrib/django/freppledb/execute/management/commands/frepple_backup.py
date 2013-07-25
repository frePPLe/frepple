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

import os, re, subprocess, shutil
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

  def handle(self, **options):

    # Pick up the options
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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'backup database':
          if not task.started: task.started = now
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='backup database', submitted=now, started=now, status='0%', user=user)

      # Choose the backup file name
      backupfile = now.strftime("database.%s.%%Y%%m%%d.%%H%%M%%S.dump" % database)
      task.message = 'Backup to file %s' % backupfile
      task.save(using=database)
      transaction.commit(using=database)

      # Run the backup command
      if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
        # SQLITE
        shutil.copy2(settings.DATABASES[database]['NAME'], os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR,backupfile)))
      elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.mysql':
        # MYSQL
        args = [ "mysqldump",
            "--password=%s" % settings.DATABASES[database]['PASSWORD'],
            "--user=%s" % settings.DATABASES[database]['USER'],
            "--quick", "--compress", "--extended-insert", "--add-drop-table",
            "--result-file=%s" % os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR,backupfile))
            ]
        if settings.DATABASES[database]['HOST']:
          args.append("--host=%s " % settings.DATABASES[database]['HOST'])
        if settings.DATABASES[database]['PORT']:
          args.append("--port=%s " % settings.DATABASES[database]['PORT'])
        args.append(settings.DATABASES[database]['NAME'])
        ret = subprocess.call(args)
        if ret: raise Exception("Run of mysqldump failed")
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
        args = [ "expdp",
            dsn,
            "schemas=%s" % settings.DATABASES[database]['USER'],
            "directory=frepple_logdir",
            "nologfile=Y",
            "dumpfile=%s" % backupfile
            ]
        ret = subprocess.call(args)
        if ret: raise Exception("Run of expdp failed")
      elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        # POSTGRESQL
        args = [ "pg_dump",
            "-b", "-w",
            '--username=%s' % settings.DATABASES[database]['USER'],
            '--file=%s' % os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR,backupfile))
            ]
        if settings.DATABASES[database]['HOST']:
          args.append("--host=%s" % settings.DATABASES[database]['HOST'])
        if settings.DATABASES[database]['PORT']:
          args.append("--port=%s " % settings.DATABASES[database]['PORT'])
        args.append(settings.DATABASES[database]['NAME'])
        ret = subprocess.call(args)
        if ret: raise Exception("Run of run pg_dump failed")
      else:
        raise Exception('Databasebackup command not supported for database engine %s' % settings.DATABASES[database]['ENGINE'])

      # Task update
      task.status = '99%'
      task.save(using=database)
      transaction.commit(using=database)

      # Delete backups older than a month
      pattern = re.compile("database.*.*.*.dump")
      for f in os.listdir(settings.FREPPLE_LOGDIR):
        if os.path.isfile(os.path.join(settings.FREPPLE_LOGDIR,f)):
          # Note this is NOT 100% correct on UNIX. st_ctime is not alawys the creation date...
          created = datetime.fromtimestamp(os.stat(os.path.join(settings.FREPPLE_LOGDIR,f)).st_ctime)
          if pattern.match(f) and  (now - created).days > 31:
            try: os.remove(os.path.join(settings.FREPPLE_LOGDIR,f))
            except: pass

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
      transaction.leave_transaction_management(using=database)

