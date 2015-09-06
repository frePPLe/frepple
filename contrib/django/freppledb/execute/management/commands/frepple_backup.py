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

import os
import re
import subprocess
from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command creates a database dump of the frePPLe database.

  It also removes dumps older than a month to limit the disk space usage.
  If you want to keep dumps for a longer period of time, you'll need to
  copy the dumps to a different location.

  The pg_dump command needs to be in the path, otherwise this command
  will fail.
  '''
  option_list = BaseCommand.option_list + (
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to backup'
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

    # Pick up the options
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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'backup database':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='backup database', submitted=now, started=now, status='0%', user=user)

      # Choose the backup file name
      backupfile = now.strftime("database.%s.%%Y%%m%%d.%%H%%M%%S.dump" % database)
      task.message = 'Backup to file %s' % backupfile
      task.save(using=database)

      # Run the backup command
      # Commenting the next line is a little more secure, but requires you to 
      # create a .pgpass file.
      os.environ['PGPASSWORD'] = settings.DATABASES[database]['PASSWORD']
      args = [
        "pg_dump",
        "-b", "-w",
        '--username=%s' % settings.DATABASES[database]['USER'],
        '--file=%s' % os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR, backupfile))
        ]
      if settings.DATABASES[database]['HOST']:
        args.append("--host=%s" % settings.DATABASES[database]['HOST'])
      if settings.DATABASES[database]['PORT']:
        args.append("--port=%s " % settings.DATABASES[database]['PORT'])
      args.append(settings.DATABASES[database]['NAME'])
      ret = subprocess.call(args)
      if ret:
        raise Exception("Run of run pg_dump failed")

      # Task update
      task.status = '99%'
      task.save(using=database)

      # Delete backups older than a month
      pattern = re.compile("database.*.*.*.dump")
      for f in os.listdir(settings.FREPPLE_LOGDIR):
        if os.path.isfile(os.path.join(settings.FREPPLE_LOGDIR, f)):
          # Note this is NOT 100% correct on UNIX. st_ctime is not alawys the creation date...
          created = datetime.fromtimestamp(os.stat(os.path.join(settings.FREPPLE_LOGDIR, f)).st_ctime)
          if pattern.match(f) and (now - created).days > 31:
            try:
              os.remove(os.path.join(settings.FREPPLE_LOGDIR, f))
            except:
              pass

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
      if task:
        task.save(using=database)
