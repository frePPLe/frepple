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

from datetime import datetime, timedelta
import logging
import os
import shlex
import time
import operator
from threading import Thread

from django.conf import settings
from django.core import management
from django.core.management import get_commands
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections

from freppledb import VERSION
from freppledb.common.models import Parameter
from freppledb.common.middleware import _thread_locals
from freppledb.execute.models import Task


logger = logging.getLogger(__name__)


class WorkerAlive(Thread):
  def __init__(self, database=DEFAULT_DB_ALIAS):
    self.database = database
    Thread.__init__(self)
    self.daemon = True

  def run(self):
    while True:
      p = Parameter.objects.all().using(self.database).get_or_create(pk='Worker alive')[0]
      p.value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      try:
        p.save(update_fields=['value'])
      except:
        pass
      time.sleep(5)


def checkActive(database=DEFAULT_DB_ALIAS):
    try:
      p = Parameter.objects.all().using(database).get(pk='Worker alive')
      return datetime.now() - datetime.strptime(p.value, "%Y-%m-%d %H:%M:%S") <= timedelta(0, 5)
    except:
      return False


class Command(BaseCommand):

  help = '''Processes the job queue of a database.
    The command is intended only to be used internally by frePPLe, not by an API or user.
    '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      )
    parser.add_argument(
      '--continuous', action="store_true",
      default=False, help='Keep the worker alive after the queue is empty'
      )


  def handle(self, *args, **options):

    # Pick up the options
    database = options['database']
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    continuous = options['continuous']

    # Use the test database if we are running the test suite
    if 'FREPPLE_TEST' in os.environ:
      connections[database].close()
      settings.DATABASES[database]['NAME'] = settings.DATABASES[database]['TEST']['NAME']

    # Check if a worker already exists
    if checkActive(database):
      if 'FREPPLE_TEST' not in os.environ:
        logger.info("Worker process already active")
      return

    # Spawn a worker-alive thread
    WorkerAlive(database).start()

    # Process the queue
    if 'FREPPLE_TEST' not in os.environ:
      logger.info("Worker starting to process jobs in the queue")
    idle_loop_done = False
    setattr(_thread_locals, 'database', database)
    while True:
      try:
        task = Task.objects.all().using(database).filter(status='Waiting').order_by('id')[0]
        idle_loop_done = False
      except:
        # No more tasks found
        if continuous:
          time.sleep(5)
          continue
        else:
          # Special case: we need to permit a single idle loop before shutting down
          # the worker. If we shut down immediately, a newly launched task could think
          # that a work is already running - while it just shut down.
          if idle_loop_done:
            break
          else:
            idle_loop_done = True
            time.sleep(5)
            continue
      try:
        if 'FREPPLE_TEST' not in os.environ:
          logger.info("starting task %d at %s" % (task.id, datetime.now()))
        background = False
        task.started = datetime.now()
        # A
        if task.name in ('frepple_run', 'runplan'):
          kwargs = {}
          if task.arguments:
            for i in shlex.split(task.arguments):
              j = i.split('=')
              if len(j) > 1:
                kwargs[j[0][2:]] = j[1]
              else:
                kwargs[j[0][2:]] = True
          if 'background' in kwargs:
            background = True
          management.call_command('runplan', database=database, task=task.id, **kwargs)
        # C
        elif task.name in ('frepple_flush', 'empty'):
          # Erase the database contents
          kwargs = {}
          if task.arguments:
            for i in shlex.split(task.arguments):
              key, val = i.split('=')
              kwargs[key[2:]] = val
          management.call_command('empty', database=database, task=task.id, **kwargs)
        # D
        elif task.name == 'loaddata':
          args = shlex.split(task.arguments)
          management.call_command('loaddata', *args, verbosity=0, database=database, task=task.id)
        # E
        elif task.name in ('frepple_copy', 'scenario_copy'):
          args = shlex.split(task.arguments)
          management.call_command('scenario_copy', *args, task=task.id)
        elif task.name in ('frepple_createbuckets', 'createbuckets'):
          args = {}
          if task.arguments:
            for i in shlex.split(task.arguments):
              key, val = i.split('=')
              args[key.strip("--").replace('-', '_')] = val
          management.call_command('createbuckets', database=database, task=task.id, **args)
        else:
          # Verify the command exists
          exists = False
          for commandname in get_commands():
            if commandname == task.name:
              exists = True
              break

          # Execute the command
          if not exists:
            logger.error('Task %s not recognized' % task.name)
          else:
            kwargs = {}
            if task.arguments:
              for i in shlex.split(task.arguments):
                key, val = i.split('=')
                kwargs[key[2:]] = val
            management.call_command(task.name, database=database, task=task.id, **kwargs)

        # Read the task again from the database and update.
        task = Task.objects.all().using(database).get(pk=task.id)
        if task.status not in ('Done', 'Failed') or not task.finished or not task.started:
          now = datetime.now()
          if not task.started:
            task.started = now
          if not background:
            if not task.finished:
              task.finished = now
            if task.status not in ('Done', 'Failed'):
              task.status = 'Done'
          task.save(using=database)
        if 'FREPPLE_TEST' not in os.environ:
          logger.info("finished task %d at %s: success" % (task.id, datetime.now()))
      except Exception as e:
        # Read the task again from the database and update.
        task = Task.objects.all().using(database).get(pk=task.id)
        task.status = 'Failed'
        now = datetime.now()
        if not task.started:
          task.started = now
        task.finished = now
        task.message = str(e)
        task.save(using=database)
        if 'FREPPLE_TEST' not in os.environ:
          logger.info("finished task %d at %s: failed" % (task.id, datetime.now()))
    # Remove the parameter again
    try:
      Parameter.objects.all().using(database).get(pk='Worker alive').delete()
    except:
      pass
    setattr(_thread_locals, 'database', None)

    # Remove log files exceeding the configured disk space allocation
    totallogs = 0
    filelist = []
    for x in os.listdir(settings.FREPPLE_LOGDIR):
      if x.endswith('.log'):
        size = 0
        creation = 0
        filename = os.path.join(settings.FREPPLE_LOGDIR, x)
        # needs try/catch because log files may still be open or being used and Windows does not like it
        try:
          size = os.path.getsize(filename)
          creation = os.path.getctime(filename)
          filelist.append( {'name': filename, 'size': size, 'creation': creation} )
        except:
          pass
        totallogs += size
    todelete = totallogs - settings.MAXTOTALLOGFILESIZE * 1024 * 1024
    filelist.sort(key=operator.itemgetter('creation'))
    for fordeletion in filelist:
      if todelete > 0:
        try:
          os.remove(fordeletion['name'])
          todelete -= fordeletion['size']
        except:
          pass

    # Exit
    if 'FREPPLE_TEST' not in os.environ:
      logger.info("Worker finished all jobs in the queue and exits")
