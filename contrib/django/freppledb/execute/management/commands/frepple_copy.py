#
# Copyright (C) 2010-2013 by frePPLe bvba
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
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from freppledb.execute.models import Task
from freppledb.common.models import User, Scenario
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command copies the contents of a database into another.
  The original data in the destination database are lost.

  The pg_dump and psql commands need to be in the path, otherwise
  this command will fail.
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

  requires_system_checks = False

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
      # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
      os.environ['PGPASSWORD'] = settings.DATABASES[source]['PASSWORD']
      ret = os.system("pg_dump -c -U%s -Fp %s%s%s | psql -U%s %s%s%s" % (
        settings.DATABASES[source]['USER'],
        settings.DATABASES[source]['HOST'] and ("-h %s " % settings.DATABASES[source]['HOST']) or '',
        settings.DATABASES[source]['PORT'] and ("-p %s " % settings.DATABASES[source]['PORT']) or '',
        test and settings.DATABASES[source]['TEST']['NAME'] or settings.DATABASES[source]['NAME'],
        settings.DATABASES[destination]['USER'],
        settings.DATABASES[destination]['HOST'] and ("-h %s " % settings.DATABASES[destination]['HOST']) or '',
        settings.DATABASES[destination]['PORT'] and ("-p %s " % settings.DATABASES[destination]['PORT']) or '',
        test and settings.DATABASES[destination]['TEST']['NAME'] or settings.DATABASES[destination]['NAME'],
        ))
      if ret:
        raise Exception('Exit code of the database copy command is %d' % ret)

      # Update the scenario table
      destinationscenario.status = 'In use'
      destinationscenario.lastrefresh = datetime.today()
      if 'description' in options:
        destinationscenario.description = options['description']
      else:
        destinationscenario.description = "Copied from scenario '%s'" % source
      destinationscenario.save()

      # Give access to the destination scenario to:
      #  a) the user doing the copy
      #  b) all superusers from the source schema
      User.objects.using(destination).filter(is_superuser=True).update(is_active=True)
      User.objects.using(destination).filter(is_superuser=False).update(is_active=False)
      if user:
        User.objects.using(destination).filter(username=user.username).update(is_active=True)

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
