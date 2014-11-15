#
# Copyright (C) 2010-2013 by Johan De Taeye, frePPLe bvba
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

import os
import shutil
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from freppledb.execute.models import Task, Scenario
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command copies the contents of a database into another.
  The original data in the destination database are lost.

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
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--force', action="store_true", dest='force',
      default=False, help='Overwrite scenarios already in use'
      ),
    make_option(
      '--description', dest='description', type='string',
      help='Description of the destination scenario'
      ),
    make_option(
      '--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'
      ),
    )
  args = 'source_database destination_database'

  requires_model_validation = False

  def get_version(self):
    return VERSION


  def handle(self, *args, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up options
    if 'force' in options:
      force = options['force']
    else:
      force = False
    test = 'FREPPLE_TEST' in os.environ
    if 'user' in options and options['user']:
      try:
        user = User.objects.all().get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      user = None

    # Initialize the task
    now = datetime.now()
    task = None
    if 'task' in options and options['task']:
      try:
        task = Task.objects.all().get(pk=options['task'])
      except:
        raise CommandError("Task identifier not found")
      if task.started or task.finished or task.status != "Waiting" or task.name != 'copy scenario':
        raise CommandError("Invalid task identifier")
      task.status = '0%'
      task.started = now
    else:
      task = Task(name='copy scenario', submitted=now, started=now, status='0%', user=user)
    task.save()

    # Synchronize the scenario table with the settings
    Scenario.syncWithSettings()

    # Validate the arguments
    destinationscenario = None
    try:
      if len(args) != 2:
        raise CommandError("Command takes exactly 2 arguments.")
      task.arguments = "%s %s" % (args[0], args[1])
      task.save()
      source = args[0]
      try:
        sourcescenario = Scenario.objects.get(pk=source)
      except:
        raise CommandError("No source database defined with name '%s'" % source)
      destination = args[1]
      try:
        destinationscenario = Scenario.objects.get(pk=destination)
      except:
        raise CommandError("No destination database defined with name '%s'" % destination)
      if source == destination:
        raise CommandError("Can't copy a schema on itself")
      if settings.DATABASES[source]['ENGINE'] != settings.DATABASES[destination]['ENGINE']:
        raise CommandError("Source and destination scenarios have a different engine")
      if sourcescenario.status != 'In use':
        raise CommandError("Source scenario is not in use")
      if destinationscenario.status != 'Free' and not force:
        raise CommandError("Destination scenario is not free")

      # Logging message - always logging in the default database
      destinationscenario.status = 'Busy'
      destinationscenario.save()

      # Copying the data
      if settings.DATABASES[source]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
        os.environ['PGPASSWORD'] = settings.DATABASES[source]['PASSWORD']
        ret = os.system("pg_dump -c -U%s -Fp %s%s%s | psql -U%s %s%s%s" % (
          settings.DATABASES[source]['USER'],
          settings.DATABASES[source]['HOST'] and ("-h %s " % settings.DATABASES[source]['HOST']) or '',
          settings.DATABASES[source]['PORT'] and ("-p %s " % settings.DATABASES[source]['PORT']) or '',
          test and settings.DATABASES[source]['TEST_NAME'] or settings.DATABASES[source]['NAME'],
          settings.DATABASES[destination]['USER'],
          settings.DATABASES[destination]['HOST'] and ("-h %s " % settings.DATABASES[destination]['HOST']) or '',
          settings.DATABASES[destination]['PORT'] and ("-p %s " % settings.DATABASES[destination]['PORT']) or '',
          test and settings.DATABASES[destination]['TEST_NAME'] or settings.DATABASES[destination]['NAME'],
          ))
        if ret:
          raise Exception('Exit code of the database copy command is %d' % ret)
      elif settings.DATABASES[source]['ENGINE'] == 'django.db.backends.sqlite3':
        # A plain copy of the database file
        if test:
          shutil.copy2(settings.DATABASES[source]['TEST_NAME'], settings.DATABASES[destination]['TEST_NAME'])
        else:
          shutil.copy2(settings.DATABASES[source]['NAME'], settings.DATABASES[destination]['NAME'])
      elif settings.DATABASES[source]['ENGINE'] == 'django.db.backends.mysql':
        ret = os.system("mysqldump %s --password=%s --user=%s %s%s--quick --compress --extended-insert --add-drop-table | mysql %s --password=%s --user=%s %s%s" % (
          test and settings.DATABASES[source]['TEST_NAME'] or settings.DATABASES[source]['NAME'],
          settings.DATABASES[source]['PASSWORD'],
          settings.DATABASES[source]['USER'],
          settings.DATABASES[source]['HOST'] and ("--host=%s " % settings.DATABASES[source]['HOST']) or '',
          settings.DATABASES[source]['PORT'] and ("--port=%s " % settings.DATABASES[source]['PORT']) or '',
          test and settings.DATABASES[destination]['TEST_NAME'] or settings.DATABASES[destination]['NAME'],
          settings.DATABASES[destination]['PASSWORD'],
          settings.DATABASES[destination]['USER'],
          settings.DATABASES[destination]['HOST'] and ("--host=%s " % settings.DATABASES[destination]['HOST']) or '',
          settings.DATABASES[destination]['PORT'] and ("--port=%s " % settings.DATABASES[destination]['PORT']) or '',
          ))
        if ret:
          raise Exception('Exit code of the database copy command is %d' % ret)
      elif settings.DATABASES[source]['ENGINE'] == 'django.db.backends.oracle':
        try:
          try:
            os.unlink(os.path.join(settings.FREPPLE_LOGDIR, 'frepple.dmp'))
          except:
            pass
          ret = os.system("expdp %s/%s@//%s:%s/%s schemas=%s directory=frepple_logdir nologfile=Y dumpfile=frepple.dmp" % (
            test and settings.DATABASES[source]['TEST_USER'] or settings.DATABASES[source]['USER'],
            settings.DATABASES[source]['PASSWORD'],
            settings.DATABASES[source]['HOST'] or 'localhost',
            settings.DATABASES[source]['PORT'] or '1521',
            test and settings.DATABASES[source]['TEST_NAME'] or settings.DATABASES[source]['NAME'],
            test and settings.DATABASES[source]['TEST_USER'] or settings.DATABASES[source]['USER'],
            ))
          if ret:
            raise Exception('Exit code of the database export command is %d' % ret)
          ret = os.system("impdp %s/%s@//%s:%s/%s remap_schema=%s:%s table_exists_action=replace directory=frepple_logdir nologfile=Y dumpfile=frepple.dmp" % (
            test and settings.DATABASES[destination]['TEST_USER'] or settings.DATABASES[destination]['USER'],
            settings.DATABASES[destination]['PASSWORD'],
            settings.DATABASES[destination]['HOST'],
            settings.DATABASES[destination]['PORT'],
            test and settings.DATABASES[destination]['TEST_NAME'] or settings.DATABASES[destination]['NAME'],
            test and settings.DATABASES[source]['TEST_USER'] or settings.DATABASES[source]['USER'],
            test and settings.DATABASES[destination]['TEST_USER'] or settings.DATABASES[destination]['USER'],
            ))
          if ret:
            raise Exception('Exit code of the database import command is %d' % ret)
        finally:
          try:
            os.unlink(os.path.join(settings.FREPPLE_LOGDIR, 'frepple.dmp'))
          except:
            pass
      else:
        raise Exception('Copy command not supported for database engine %s' % settings.DATABASES[source]['ENGINE'])

      # Update the scenario table
      destinationscenario.status = 'In use'
      destinationscenario.lastrefresh = datetime.today()
      if 'description' in options:
        destinationscenario.description = options['description']
      else:
        destinationscenario.description = "Copied from scenario '%s'" % source
      destinationscenario.save()

      # Logging message
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      if destinationscenario and destinationscenario.status == 'Busy':
        destinationscenario.status = 'Free'
        destinationscenario.save()
      raise e

    finally:
      if task:
        task.save()
      settings.DEBUG = tmp_debug
