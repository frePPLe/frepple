#
# Copyright (C) 2016 by frePPLe bvba
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

from datetime import datetime
from importlib import import_module
from operator import attrgetter
import os
import sys
import logging

if __name__ == "__main__":
  # Initialize django
  import django
  django.setup()

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.encoding import force_text

from freppledb.execute.models import Task

logger = logging.getLogger(__name__)


class PlanTaskRegistry:
  reg = []

  @classmethod
  def register(cls, task):
    if not issubclass(task, PlanTask):
      logger.warning("Warning: PlanTaskRegistry only registers PlanTask objects")
    elif task.sequence is None:
      logger.warning("Warning: PlanTask doesn't have a sequence")
    else:
      # Remove a previous task at the same sequence
      for t in cls.reg:
        if t.sequence == task.sequence:
          cls.reg.remove(t)
          break
      # Adding the new task to the registry
      cls.reg.append(task)
    return task

  @classmethod
  def getTask(cls, sequence=None):
    for i in cls.reg:
      if i.sequence == sequence:
        return i
    return None

  @classmethod
  def getLabels(cls):
    res = []
    for t in cls.reg:
      if t.label:
        lbl = (t.label[0], force_text(t.label[1]))
        if lbl not in res:
          res.append(lbl)
    return res

  @classmethod
  def unregister(cls, task):
    if not issubclass(task, PlanTask):
      logger.warning("Warning: PlanTaskRegistry only unregisters PlanTask objects")
    elif task.sequence is None:
      logger.warning("Warning: PlanTask doesn't have a sequence")
    else:
      # Removing a task from the registry
      cls.reg.remove(task)

  @classmethod
  def autodiscover(cls):
    if not cls.reg:
      for app in reversed(settings.INSTALLED_APPS):
        try:
          mod = import_module('%s.commands' % app)
        except ImportError as e:
          # Silently ignore if it's the commands module which isn't found
          if str(e) not in ("No module named %s.commands" % app, "No module named '%s.commands'" % app):
            raise e
      cls.reg = sorted(cls.reg, key=attrgetter('sequence'))

  @classmethod
  def display(cls, **kwargs):
    logger.info("Planning task registry:")
    for i in cls.reg:
      i.weight = i.getWeight(**kwargs)
      if i.weight is not None and i.weight >= 0:
        logger.info("  %s: %s (weight %s)" % (i.sequence, i.description, i.weight))

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    cls.task = None
    if 'FREPPLE_TASKID' in os.environ:
      try:
        cls.task = Task.objects.all().using(database).get(pk=os.environ['FREPPLE_TASKID'])
      except:
        raise Exception("Task identifier not found")
    if cls.task and cls.task.status == 'Canceling':
      cls.task.status = 'Cancelled'
      cls.task.save(using=database)
      sys.exit(2)

    # Collect the list of tasks
    task_weights = 0
    task_list = []
    for i in cls.reg:
      i.task = cls.task
      i.weight = i.getWeight(database=database, **kwargs)
      if i.weight is not None and i.weight >= 0:
        task_weights += i.weight
        task_list.append(i)
    if not task_weights:
      task_weights = 1

    # Execute all tasks in the list
    try:
      progress = 0
      for step in task_list:
        # Update status and message
        if cls.task:
          cls.task.status = '%d%%' % int(progress * 100.0 / task_weights)
          cls.task.message = step.description
          cls.task.save(using=database)

        # Run the step
        logger.info("Start step %s '%s' at %s" % (
          step.sequence,
          step.description,
          datetime.now().strftime("%H:%M:%S")
          ))
        step.run(database=database, **kwargs)
        if step.sequence > 0:
          logger.info("Finished '%s' at %s \n" % (step.description, datetime.now().strftime("%H:%M:%S")))
        progress += step.weight

      # Final task status
      if cls.task:
        cls.task.finished = datetime.now()
        cls.task.status = '100%'
        cls.task.message = ''
        cls.task.save(using=database)
      logger.info("Finished planning at %s" % datetime.now().strftime("%H:%M:%S"))
    except Exception as e:
      if cls.task:
        cls.task.finished = datetime.now()
        cls.task.status = 'Failed'
        cls.task.message = str(e)
        cls.task.save(using=database)
      raise


class PlanTask:
  '''
  Base class for steps in the plan generation process
  '''
  description = ''
  sequence = None
  label = None

  @staticmethod
  def getWeight(**kwargs):
    return 1

  @staticmethod
  def run(**kwargs):
    logger.warning("Warning: PlanTask doesn't implement the run method")


if __name__ == "__main__":
  # Select database
  try:
    database = os.environ['FREPPLE_DATABASE'] or DEFAULT_DB_ALIAS
  except:
    database = DEFAULT_DB_ALIAS

  # Use the test database if we are running the test suite
  if 'FREPPLE_TEST' in os.environ:
    settings.DATABASES[database]['NAME'] = settings.DATABASES[database]['TEST']['NAME']

  # Make sure the debug flag is not set!
  # When it is set, the Django database wrapper collects a list of all sql
  # statements executed and their timings. This consumes plenty of memory
  # and cpu time.
  settings.DEBUG = False

  # Send the output to a logfile
  frepple.settings.logfile = os.path.join(settings.FREPPLE_LOGDIR, os.environ.get('FREPPLE_LOGFILE', 'frepple.log'))

  # Welcome message
  print("FrePPLe with processid %s on %s using database '%s'" % (
    os.getpid(),
    sys.platform,
    database
    ))

  # Find all planning steps and execute them
  from freppledb.common.commands import PlanTaskRegistry as register
  register.autodiscover()
  try:
    register.run(database=database)
  except Exception as e:
    print("Error during planning: %s" % e)
    raise
