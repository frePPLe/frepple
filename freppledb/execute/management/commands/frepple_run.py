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
from datetime import datetime
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.commands import PlanTaskRegistry
from freppledb.common.models import User
from freppledb.execute.models import Task
from freppledb import VERSION


class Command(BaseCommand):
  
  help = "Runs frePPLe to generate a plan"

  requires_system_checks = False
  
  
  def get_version(self):
    return VERSION
  
  
  def add_arguments(self, parser):
    parser.add_argument(
      '--user', dest='user',
      help='User running the command'
      )
    parser.add_argument(
      '--constraint', dest='constraint', type=int, default=15,
      choices=range(0, 15),
      help='Constraints to be considered: 1=lead time, 2=material, 4=capacity, 8=release fence'
      )
    parser.add_argument(
      '--plantype', dest='plantype', type=int, choices=[1, 2],
      default=1, help='Plan type: 1=constrained, 2=unconstrained'
      )
    parser.add_argument(
      '--database', dest='database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      )
    parser.add_argument(
      '--task', dest='task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      '--env', dest='env',
      help='A comma separated list of extra settings passed as environment variables to the engine'
      )
    parser.add_argument(
      '--background', dest='background', action='store_true', default=False,
      help='Run the planning engine in the background (default = False)'
      )
    
  
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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'generate plan':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='generate plan', submitted=now, started=now, status='0%', user=user)

      # Validate options
      if 'constraint' in options:
        constraint = int(options['constraint'])
        if constraint < 0 or constraint > 15:
          raise ValueError("Invalid constraint: %s" % options['constraint'])
      else:
        constraint = 15
      if 'plantype' in options:
        plantype = int(options['plantype'])
      else:
        plantype = 1

      # Reset environment variables
      # TODO avoid having to delete the environment variables. Use options directly?
      PlanTaskRegistry.autodiscover()
      for i in PlanTaskRegistry.reg:
        if 'env' in options:
          # Options specified
          if i.label and i.label[0] in os.environ:
            del os.environ[i.label[0]]
        elif i.label:
          # No options specified - default to activate them all
          os.environ[i.label[0]] = '1'

      # Set environment variables
      if options['env']:
        task.arguments = "--constraint=%d --plantype=%d --env=%s" % (constraint, plantype, options['env'])
        for i in options['env'].split(','):
          j = i.split('=')
          if len(j) == 1:
            os.environ[j[0]] = '1'
          else:
            os.environ[j[0]] = j[1]
      else:
        task.arguments = "--constraint=%d --plantype=%d" % (constraint, plantype)
      if options['background']:
        task.arguments += " --background"

      # Log task
      task.save(using=database)

      # Locate commands.py
      import freppledb.common.commands
      cmd = freppledb.common.commands.__file__

      # Prepare environment
      os.environ['FREPPLE_PLANTYPE'] = str(plantype)
      os.environ['FREPPLE_CONSTRAINT'] = str(constraint)
      os.environ['FREPPLE_TASKID'] = str(task.id)
      os.environ['FREPPLE_DATABASE'] = database
      os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
      if os.path.isfile(os.path.join(settings.FREPPLE_HOME, 'libfrepple.so')):
        os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
      if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
      os.environ['PYTHONPATH'] = os.path.normpath(settings.FREPPLE_APP)

      if options['background']:
        # Execute as background process on Windows
        if os.name == 'nt':
          subprocess.Popen(['frepple', cmd], creationflags=0x08000000)
        else:
          # Execute as background process on Linux
          subprocess.Popen(['frepple', cmd])
      else:
        # Execute in foreground
        ret = subprocess.call(['frepple', cmd])
        if ret != 0 and ret != 2:
          # Return code 0 is a successful run
          # Return code is 2 is a run cancelled by a user. That's shown in the status field.
          raise Exception('Failed with exit code %d' % ret)

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
