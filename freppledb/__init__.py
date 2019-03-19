r'''
A Django project implementing a web-based user interface for frePPLe.
'''


VERSION = '5.1.0'


def runCommand(taskname, *args, **kwargs):
  '''
  Auxilary method to run a django command. It is intended to be used
  as a target for the multiprocessing module.

  The code is put here, such that a child process loads only
  a minimum of other python modules.
  '''
  # Initialize django
  import os
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")
  import django
  django.setup()

  # Be sure to use the correct database
  from django.db import DEFAULT_DB_ALIAS, connections
  from freppledb.common.middleware import _thread_locals
  database = kwargs.get("database", DEFAULT_DB_ALIAS)
  setattr(_thread_locals, 'database', database)
  if 'FREPPLE_TEST' in os.environ:
    from django.conf import settings
    connections[database].close()
    settings.DATABASES[database]['NAME'] = settings.DATABASES[database]['TEST']['NAME']

  # Run the command
  try:
    from django.core import management
    management.call_command(taskname, *args, **kwargs)
  except Exception as e:
    taskid = kwargs.get("task", None)
    if taskid:
      from datetime import datetime
      from freppledb.execute.models import Task
      task = Task.objects.all().using(database).get(pk=taskid)
      task.status = 'Failed'
      now = datetime.now()
      if not task.started:
        task.started = now
      task.finished = now
      task.message = str(e)
      task.processid = None
      task.save(using=database)
