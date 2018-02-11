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

import os.path
import subprocess
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):

  help = '''
    This command creates a database dump of the frePPLe database.

    The psql command needs to be in the path, otherwise this command
    will fail.
    '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user', help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to restore into'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      'dump', help='Database dump file to restore.'
      )


  def handle(self, **options):

    # Pick up the options
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
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_restore', 'restore'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='restore', submitted=now, started=now, status='0%', user=user)
      task.arguments = options['dump']
      task.save(using=database)

      # Validate options
      if not os.path.isfile(os.path.join(settings.FREPPLE_LOGDIR, options['dump'])):
        raise CommandError("Dump file not found")

      # Run the restore command
      # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
      if settings.DATABASES[database]['PASSWORD']:
        os.environ['PGPASSWORD'] = settings.DATABASES[database]['PASSWORD']
      cmd = [ "psql", ]
      if settings.DATABASES[database]['USER']:
        cmd.append("--username=%s" % settings.DATABASES[database]['USER'])
      if settings.DATABASES[database]['HOST']:
        cmd.append("--host=%s" % settings.DATABASES[database]['HOST'])
      if settings.DATABASES[database]['PORT']:
        cmd.append("--port=%s " % settings.DATABASES[database]['PORT'])
      cmd.append(settings.DATABASES[database]['NAME'])
      cmd.append('<%s' % os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR, options['dump'])))
      ret = subprocess.call(cmd, shell=True)  # Shell needs to be True in order to interpret the < character
      if ret:
        raise Exception("Run of psql failed")

      # Task update
      # We need to recreate a new task record, since the previous one is lost during the restoration.
      task = Task(
        name='restore', submitted=task.submitted, started=task.started,
        arguments=task.arguments, status='Done', finished=datetime.now(),
        user=task.user
        )

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      # Commit it all, even in case of exceptions
      if task:
        task.save(using=database)
