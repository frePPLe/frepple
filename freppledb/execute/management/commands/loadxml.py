#
# Copyright (C) 2011-2013 by frePPLe bvba
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
import sys
from datetime import datetime
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):

  help = "Loads an XML file into the frePPLe database"

  requires_system_checks = False

  def add_arguments(self, parser):
    parser.add_argument(
      '--user', help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      'file', nargs='+',
      help='XML data files to load'
      )


  def get_version(self):
    return VERSION


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
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_loadxml', 'loadxml'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='loadxml', submitted=now, started=now, status='0%', user=user)
      task.arguments = ' '.join(options['file'])
      task.save(using=database)

      # Execute
      # TODO: if frePPLe is available as a module, we don't really need to spawn another process.
      os.environ['FREPPLE_HOME'] = settings.FREPPLE_HOME.replace('\\', '\\\\')
      os.environ['FREPPLE_APP'] = settings.FREPPLE_APP
      os.environ['FREPPLE_DATABASE'] = database
      os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
      os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
      if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
      if os.path.exists(os.path.join(os.environ['FREPPLE_HOME'], 'python36.zip')):
        # For the py2exe executable
        os.environ['PYTHONPATH'] = os.path.join(
          os.environ['FREPPLE_HOME'],
          'python%d%d.zip' % (sys.version_info[0], sys.version_info[1])
          ) + os.pathsep + os.path.normpath(os.environ['FREPPLE_APP'])
      else:
        # Other executables
        os.environ['PYTHONPATH'] = os.path.normpath(os.environ['FREPPLE_APP'])
      cmdline = [ '"%s"' % i for i in options['file'] ]
      cmdline.insert(0, 'frepple')
      cmdline.append( '"%s"' % os.path.join(settings.FREPPLE_APP, 'freppledb', 'execute', 'loadxml.py') )
      proc = subprocess.run(' '.join(cmdline))
      if proc.returncode:
        raise Exception('Exit code of the batch run is %d' % proc.returncode)

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
