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
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils.importlib import import_module
from django.db import transaction, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.execute.models import Task


class Command(BaseCommand):
  help = "Upload planning results from frePPle into an odoo instance"

  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to export from'),
      make_option('--task', dest='task', type='int',
        help='Task identifier (generated automatically if not provided)'),
  )

  requires_model_validation = False


  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options: self.verbosity = int(options['verbosity'] or '1')
    else: self.verbosity = 1
    if 'user' in options: user = options['user']
    else: user = ''
    if 'database' in options: self.database = options['database'] or DEFAULT_DB_ALIAS
    else: self.database = DEFAULT_DB_ALIAS
    if not self.database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )

    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all SQL
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    now = datetime.now()
    ac = transaction.get_autocommit(using=self.database)
    transaction.set_autocommit(False, using=self.database)
    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try: task = Task.objects.all().using(self.database).get(pk=options['task'])
        except: raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'Odoo export':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='Odoo export', submitted=now, started=now, status='0%', user=user)
      task.save(using=self.database)
      transaction.commit(using=self.database)

      # Find the connector class
      # We look for a module called "odoo_export" in each of the installed
      # applications, and expect to find a class called connector in it
      connector = None
      for app in reversed(settings.INSTALLED_APPS):
        try:
          connector = getattr(import_module('%s.odoo_export' % app),'Connector')
        except ImportError as e:
          # Silently ignore if it's the module which isn't found in the app
          if str(e) != 'No module named odoo_export': raise e
      if not connector:
          raise CommandError("No odoo_export connector found")

      # Instantiate the connector and upload all data
      connector(task, self.database, self.verbosity).run()

      # Log success
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      if task: task.save(using=self.database)
      try: transaction.commit(using=self.database)
      except: pass
      settings.DEBUG = tmp_debug
      transaction.set_autocommit(ac, using=self.database)
