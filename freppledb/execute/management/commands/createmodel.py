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
import random
from datetime import timedelta, datetime, date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core import management
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.models import Min, Max

from freppledb.common.models import Parameter, BucketDetail
from freppledb.input.models import Operation, Buffer, Resource, Location, Calendar
from freppledb.input.models import CalendarBucket, Customer, Demand, Supplier
from freppledb.input.models import Item, OperationMaterial, OperationResource
from freppledb.input.models import ItemSupplier
from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):

  help = '''
      This command is a simple, generic model generator.
      It is meant as a quick way to produce models for tests on performance,
      memory size, database size...

      The auto-generated supply network looks schematically as follows:
        [ Operation -> buffer ] ...   [ -> Operation -> buffer ]  [ Delivery ]
        [ Operation -> buffer ] ...   [ -> Operation -> buffer ]  [ Delivery ]
        [ Operation -> buffer ] ...   [ -> Operation -> buffer ]  [ Delivery ]
        [ Operation -> buffer ] ...   [ -> Operation -> buffer ]  [ Delivery ]
        [ Operation -> buffer ] ...   [ -> Operation -> buffer ]  [ Delivery ]
            ...                                  ...
      Each row represents a cluster.
      The operation+buffer are repeated as many times as the depth of the supply
      path parameter.
      In each cluster a single item is defined, and a parametrizable number of
      demands is placed on the cluster.

      The script uses random numbers. These are reproducible (ie different runs
      will produce the same random number sequence), but not portable (ie runs
      on a different platform or version can give different results).
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
      '--cluster', type=int,
      help='Number of end items', default=100
      )
    parser.add_argument(
      '--demand', type=int,
      help='Demands per end item', default=30
      )
    parser.add_argument(
      '--forecast_per_item', type=int,
      help='Monthly forecast per end item', default=30
      )
    parser.add_argument(
      '--level', type=int,
      help='Depth of bill-of-material', default=5
      )
    parser.add_argument(
      '--resource', type=int,
      help='Number of resources', default=60
      )
    parser.add_argument(
      '--resource_size', type=int,
      help='Size of each resource', default=5
      )
    parser.add_argument(
      '--components', type=int,
      help='Total number of components', default=200
      )
    parser.add_argument(
      '--components_per', type=int,
      help='Number of components per end item', default=4
      )
    parser.add_argument(
      '--deliver_lt', type=int,
      help='Average delivery lead time of orders', default=30
      )
    parser.add_argument(
      '--procure_lt', type=int,
      help='Average procurement lead time', default=40
      )
    parser.add_argument(
      '--currentdate',
      help='Current date of the plan in YYYY-MM-DD format'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to populate'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )


  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up the options
    verbosity = int(options['verbosity'])
    cluster = int(options['cluster'])
    demand = int(options['demand'])
    forecast_per_item = int(options['forecast_per_item'])
    level = int(options['level'])
    resource = int(options['resource'])
    resource_size = int(options['resource_size'])
    components = int(options['components'])
    components_per = int(options['components_per'])
    if components <= 0:
      components_per = 0
    deliver_lt = int(options['deliver_lt'])
    procure_lt = int(options['procure_lt'])
    if options['currentdate']:
      currentdate = options['currentdate']
    else:
      currentdate = datetime.strftime(date.today(), '%Y-%m-%d')
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

    random.seed(100)  # Initialize random seed to get reproducible results

    now = datetime.now()
    task = None
    try:
      # Initialize the task
      if options['task']:
        try:
          task = Task.objects.all().using(database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_createmodel', 'createmodel'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='createmodel', submitted=now, started=now, status='0%', user=user)
      task.arguments = "--cluster=%s --demand=%s --forecast_per_item=%s --level=%s --resource=%s " \
        "--resource_size=%s --components=%s --components_per=%s --deliver_lt=%s --procure_lt=%s" % (
          cluster, demand, forecast_per_item, level, resource,
          resource_size, components, components_per, deliver_lt, procure_lt
        )
      task.save(using=database)

      # Pick up the startdate
      try:
        startdate = datetime.strptime(currentdate, '%Y-%m-%d')
      except:
        raise CommandError("current date is not matching format YYYY-MM-DD")

      # Check whether the database is empty
      if Buffer.objects.using(database).count() > 0 or Item.objects.using(database).count() > 0:
        raise CommandError("Database must be empty before creating a model")

      # Plan start date
      if verbosity > 0:
        print("Updating current date...")
      param = Parameter.objects.using(database).get_or_create(name="currentdate")[0]
      param.value = datetime.strftime(startdate, "%Y-%m-%d %H:%M:%S")
      param.save(using=database)

      # Planning horizon
      # minimum 10 daily buckets, weekly buckets till 40 days after current
      if verbosity > 0:
        print("Updating buckets...")
      management.call_command('createbuckets', user=user, database=database)
      task.status = '2%'
      task.save(using=database)

      # Weeks calendar
      if verbosity > 0:
        print("Creating weeks calendar...")
      with transaction.atomic(using=database):
        weeks = Calendar.objects.using(database).create(name="Weeks", defaultvalue=0)
        for i in BucketDetail.objects.using(database).filter(bucket="week").all():
          CalendarBucket(
            startdate=i.startdate, enddate=i.enddate, value=1, calendar=weeks
            ).save(using=database)
        task.status = '4%'
        task.save(using=database)

      # Working days calendar
      if verbosity > 0:
        print("Creating working days...")
      with transaction.atomic(using=database):
        workingdays = Calendar.objects.using(database).create(name="Working Days", defaultvalue=0)
        minmax = BucketDetail.objects.using(database).filter(bucket="week").aggregate(Min('startdate'), Max('startdate'))
        CalendarBucket(
          startdate=minmax['startdate__min'], enddate=minmax['startdate__max'],
          value=1, calendar=workingdays, priority=1, saturday=False, sunday=False
          ).save(using=database)
        task.status = '6%'
        task.save(using=database)

      # Parent location
      loc = Location.objects.using(database).create(
        name="Factory",
        available = workingdays
        )

      # Create a random list of categories to choose from
      categories = [
        'cat A', 'cat B', 'cat C', 'cat D', 'cat E', 'cat F', 'cat G'
        ]

      # Create customers
      if verbosity > 0:
        print("Creating customers...")
      with transaction.atomic(using=database):
        cust = []
        for i in range(100):
          c = Customer.objects.using(database).create(name='Cust %03d' % i)
          cust.append(c)
        task.status = '8%'
        task.save(using=database)

      # Create resources and their calendars
      if verbosity > 0:
        print("Creating resources and calendars...")
      with transaction.atomic(using=database):
        res = []
        for i in range(resource):
          cal = Calendar.objects.using(database).create(
            name='capacity for res %03d' % i,
            category='capacity',
            defaultvalue=0
            )
          CalendarBucket.objects.using(database).create(
            startdate=startdate,
            value=resource_size,
            calendar=cal
            )
          r = Resource.objects.using(database).create(
            name='Res %03d' % i, maximum_calendar=cal, location=loc
            )
          res.append(r)
        task.status = '10%'
        task.save(using=database)
        random.shuffle(res)

      # Create the components
      if verbosity > 0:
        print("Creating raw materials...")
      with transaction.atomic(using=database):
        comps = []
        compsupplier = Supplier.objects.using(database).create(name='component supplier')
        for i in range(components):
          it = Item.objects.using(database).create(
            name='Component %04d' % i,
            category='Procured',
            cost=str(round(random.uniform(0, 100)))
            )
          ld = abs(round(random.normalvariate(procure_lt, procure_lt / 3)))
          Buffer.objects.using(database).create(
            name='%s @ %s' % (it.name, loc.name),
            location=loc,
            category='Procured',
            item=it,
            minimum=20,
            onhand=str(round(forecast_per_item * random.uniform(1, 3) * ld / 30)),
            )
          ItemSupplier.objects.using(database).create(
            item=it,
            location=loc,
            supplier=compsupplier,
            leadtime=timedelta(days=ld),
            sizeminimum=80,
            sizemultiple=10,
            priority=1,
            cost=it.cost
            )
          comps.append(it)
        task.status = '12%'
        task.save(using=database)

      # Loop over all clusters
      durations = [ timedelta(days=i) for i in range(1,6) ]
      progress = 88.0 / cluster
      for i in range(cluster):
        with transaction.atomic(using=database):
          if verbosity > 0:
            print("Creating supply chain for end item %d..." % i)

          # Item
          it = Item.objects.using(database).create(
            name='Itm %05d' % i,
            category=random.choice(categories),
            cost=str(round(random.uniform(100, 200)))
            )

          # Level 0 buffer
          buf = Buffer.objects.using(database).create(
            name='%s @ %s' % (it.name, loc.name),
            item=it,
            location=loc,
            category='00'
            )

          # Demand
          for j in range(demand):
            Demand.objects.using(database).create(
              name='Dmd %05d %05d' % (i, j),
              item=it,
              location=loc,
              quantity=int(random.uniform(1, 6)),
              # Exponential distribution of due dates, with an average of deliver_lt days.
              due=startdate + timedelta(days=round(random.expovariate(float(1) / deliver_lt / 24)) / 24),
              # Orders have higher priority than forecast
              priority=random.choice([1, 2]),
              customer=random.choice(cust),
              category=random.choice(categories)
              )

          # Create upstream operations and buffers
          ops = []
          previtem = it
          for k in range(level):
            if k == 1 and res:
              # Create a resource load for operations on level 1
              oper = Operation.objects.using(database).create(
                name='Oper %05d L%02d' % (i, k),
                type='time_per',
                location=loc,
                duration_per=timedelta(days=1),
                sizemultiple=1,
                item=previtem
                )
              if resource < cluster and i < resource:
                # When there are more cluster than resources, we try to assure
                # that each resource is loaded by at least 1 operation.
                OperationResource.objects.using(database).create(resource=res[i], operation=oper)
              else:
                OperationResource.objects.using(database).create(resource=random.choice(res), operation=oper)
            else:
              oper = Operation.objects.using(database).create(
                name='Oper %05d L%02d' % (i, k),
                duration=random.choice(durations),
                sizemultiple=1,
                location=loc,
                item=previtem
                )
            ops.append(oper)
            # Some inventory in random buffers
            if random.uniform(0, 1) > 0.8:
              buf.onhand = int(random.uniform(5, 20))
            buf.save(using=database)
            OperationMaterial.objects.using(database).create(
              operation=oper,
              item=previtem,
              quantity=1,
              type="end"
              )
            if k != level - 1:
              # Consume from the next level in the bill of material
              it_tmp = Item.objects.using(database).create(
                name='Itm %05d L%02d' % (i, k+1),
                category=random.choice(categories),
                cost=str(round(random.uniform(100, 200)))
                )
              buf = Buffer.objects.using(database).create(
                name='%s @ %s' % (it_tmp.name, loc.name),
                item=it_tmp,
                location=loc,
                category='%02d' % (k + 1)
                )
              OperationMaterial.objects.using(database).create(
                operation=oper,
                item=it_tmp,
                quantity=-1
                )
            previtem = it_tmp

          # Consume raw materials / components
          c = []
          for j in range(components_per):
            o = random.choice(ops)
            b = random.choice(comps)
            while (o, b) in c:
              # A flow with the same operation and buffer already exists
              o = random.choice(ops)
              b = random.choice(comps)
            c.append( (o, b) )
            OperationMaterial.objects.using(database).create(
              operation=o,
              item=b,
              quantity=random.choice([-1, -1, -1, -2, -3])
              )

          # Commit the current cluster
          task.status = '%d%%' % (12 + progress * (i + 1))
          task.save(using=database)

      # Task update
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
        task.save(using=database)
      raise e

    finally:
      if task:
        task.save(using=database)
      settings.DEBUG = tmp_debug
