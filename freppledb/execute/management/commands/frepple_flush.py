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

from datetime import datetime

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.contrib.contenttypes.models import ContentType

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb.common.report import EXCLUDE_FROM_BULK_OPERATIONS
import freppledb.input.models as inputmodels
from freppledb import VERSION


class Command(BaseCommand):

  help = '''
    This command empties the contents of all data tables in the frePPLe database.

    The results are similar to the 'flush input output' command, with the
    difference that some tables are not emptied and some performance related
    tweaks.
    Another difference is that the initial_data fixture is not loaded.
    '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user',
      help='User running the command'
      )
    parser.add_argument(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a specific database to delete data from'
      ),
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      ),
    parser.add_argument(
      '--models',
      help='Comma-separated list of models to erase'
      )


  def handle(self, **options):
    # Pick up options
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
    if options['models']:
      models = options['models'].split(',')
    else:
      models = None

    now = datetime.now()
    task = None
    try:
      # Initialize the task
      if options['task']:
        try:
          task = Task.objects.all().using(database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'empty database':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='empty database', submitted=now, started=now, status='0%', user=user)
      task.save(using=database)

      # Create a database connection
      cursor = connections[database].cursor()

      # Get a list of all django tables in the database
      tables = set(connections[database].introspection.django_table_names(only_existing=True))
      ContentTypekeys = set()
      # Validate the user list of tables
      if models:
        models2tables = set()
        admin_log_positive = True
        for m in models:
          try:
            x = m.split('.', 1)
            x = apps.get_model(x[0], x[1])
            if x in EXCLUDE_FROM_BULK_OPERATIONS:
              continue

            ContentTypekeys.add(ContentType.objects.get_for_model(x).pk)

            x = x._meta.db_table
            if x not in tables:
              raise
            models2tables.add(x)
          except Exception as e:
            raise CommandError("Invalid model to erase: %s" % m)
        tables = models2tables
      else:
        admin_log_positive = False
        tables.discard('django_admin_log')
        for i in EXCLUDE_FROM_BULK_OPERATIONS:
          tables.discard(i._meta.db_table)
          ContentTypekeys.add(ContentType.objects.get_for_model(i).pk)
      # Some tables need to be handled a bit special
      if "setupmatrix" in tables:
        tables.add("setuprule")
      if 'operationplan' in tables:
        tables.add('operationplanmaterial')
        tables.add('operationplanresource')
      if 'resource' in tables and 'out_resourceplan' not in tables:
        tables.add('out_resourceplan')
      tables.discard('auth_group_permissions')
      tables.discard('auth_permission')
      tables.discard('auth_group')
      tables.discard('django_session')
      tables.discard('common_user')
      tables.discard('common_user_groups')
      tables.discard('common_user_user_permissions')
      tables.discard('common_preference')
      tables.discard('django_content_type')
      tables.discard('execute_log')
      tables.discard('common_scenario')

      # Delete all records from the tables.
      with transaction.atomic(using=database, savepoint=False):
        if ContentTypekeys:
          if admin_log_positive:
            cursor.execute(
              "delete from django_admin_log where content_type_id = any(%s)",
              ( list(ContentTypekeys), )
              )
          else:
            cursor.execute(
              "delete from django_admin_log where content_type_id != any(%s)",
              ( list(ContentTypekeys), )
              )
        if "common_bucket" in tables:
          cursor.execute('update common_user set horizonbuckets = null')
        for stmt in connections[database].ops.sql_flush(no_style(), tables, []):
          cursor.execute(stmt)
        if models:
          if 'input.purchaseorder' in models:
            cursor.execute('''
              delete from operationplanresource
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'PO'
                )
              ''')
            cursor.execute('''
              delete from operationplanmaterial
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'PO'
                )
              ''')
            cursor.execute("delete from operationplan where type = 'PO'")
            key = ContentType.objects.get_for_model(inputmodels.PurchaseOrder, for_concrete_model=False).pk
            cursor.execute("delete from django_admin_log where content_type_id = %s", (key,))
          if 'input.distributionorder' in models:
            cursor.execute('''
              delete from operationplanresource
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'DO'
                )
              ''')
            cursor.execute('''
              delete from operationplanmaterial
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'DO'
                )
              ''')
            cursor.execute("delete from operationplan where type = 'DO'")
            key = ContentType.objects.get_for_model(inputmodels.DistributionOrder, for_concrete_model=False).pk
            cursor.execute("delete from django_admin_log where content_type_id = %s", (key,))
          if 'input.manufacturingorder' in models:
            cursor.execute('''
              delete from operationplanmaterial
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'MO'
                )
              ''')
            cursor.execute('''
              delete from operationplanresource
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'MO'
                )
              ''')
            cursor.execute("delete from operationplan where type = 'MO'")
            key = ContentType.objects.get_for_model(inputmodels.ManufacturingOrder, for_concrete_model=False).pk
            cursor.execute("delete from django_admin_log where content_type_id = %s", (key,))
          if 'input.deliveryorder' in models:
            cursor.execute('''
              delete from operationplanmaterial
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'DLVR'
                )
              ''')
            cursor.execute('''
              delete from operationplanresource
              where operationplan_id in (
                select operationplan.id from operationplan
                where type = 'DLVR'
                )
              ''')
            cursor.execute("delete from operationplan where type = 'DLVR'")
            key = ContentType.objects.get_for_model(inputmodels.DeliveryOrder, for_concrete_model=False).pk
            cursor.execute("delete from django_admin_log where content_type_id = %s", (key,))

      # Task update
      task.status = 'Done'
      task.finished = datetime.now()
      task.save(using=database)

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
        task.save(using=database)
      raise CommandError('%s' % e)
