#
# Copyright (C) 2007-2017 by frePPLe bvba
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
import logging
import uuid
from time import time
from datetime import datetime

#uncomment below line to use checkCycles
#import networkx


from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.boot import getAttributes
from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.input.models import Resource, Item

logger = logging.getLogger(__name__)


class CheckTask(PlanTask):
  '''
  Planning task to be used for data validation tasks.

  Specific are:
    - low weight by default, ie fast execution assumed
  '''
  @staticmethod
  def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
    return 0.1


class LoadTask(PlanTask):
  '''
  Planning task to be used for data loading tasks.

  Specific are:
    - low weight by default, ie fast execution assumed
    - filter attribute to load only a subset of the data
    - subclass is used by the odoo connector to recognize data loading tasks
  '''

  @staticmethod
  def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
    return 0.1

  filter = None


@PlanTaskRegistry.register
class checkBuckets(CheckTask):
  # check for no buckets available
  # check for gaps between buckets (enddate bucket <> startdate next bucket)
  # check for overlaps (more than 1 bucket have the same startdate or the same enddate)
  # make sure partial indexes are created
  description = "Checking Buckets"
  sequence = 80

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    with connections[database].cursor() as cursor:
      cursor.execute('''
        WITH problems AS (
          (
            SELECT bucket_id, enddate AS date, 'enddate not matching next bucket startdate' AS message FROM common_bucketdetail
            EXCEPT
            SELECT bucket_id, startdate, 'enddate not matching next bucket startdate' AS message FROM common_bucketdetail
          )
          UNION ALL
            SELECT bucket_id, startdate AS date, 'startdate not unique for this bucket_id' AS message FROM common_bucketdetail GROUP BY bucket_id, startdate HAVING COUNT(*)>1
          UNION ALL
            SELECT bucket_id, enddate AS date, 'enddate not unique for this bucket_id' AS message FROM common_bucketdetail GROUP BY bucket_id, enddate HAVING COUNT(*)>1
        ),
        maxenddate AS (
              SELECT bucket_id, MAX(enddate) AS theend FROM common_bucketdetail GROUP BY bucket_id
        )
        SELECT problems.bucket_id, common_bucketdetail.name, problems.date, problems.date = maxenddate.theend, problems.message
        FROM common_bucketdetail
        RIGHT OUTER JOIN problems ON problems.bucket_id = common_bucketdetail.bucket_id AND (common_bucketdetail.startdate = problems.date OR common_bucketdetail.enddate = problems.date)
        INNER JOIN maxenddate ON maxenddate.bucket_id = common_bucketdetail.bucket_id
      ''')
      errors = 0
      empty = True
      for rec in cursor:
        empty = False
        if rec[3] is False:
          errors += 1
          logger.error('%s %s %s %s' % (rec[0], rec[1], rec[2], rec[4]))
      if empty:
        raise ValueError("No Calendar Buckets available")
      if errors > 0:
        raise ValueError("Invalid Bucket dates")

      # Check if partial indexes exist
      cursor.execute('''
        select name from common_bucket
        except
        select description from pg_description
        inner join pg_class on pg_class.oid = pg_description.objoid
        inner join pg_indexes on pg_indexes.indexname = pg_class.relname and pg_indexes.tablename = 'common_bucketdetail'
      ''')
      queries = []
      for rec in cursor:
        indexName = 'common_bucketdetail_' + str(uuid.uuid4())[:8]
        queries.append((indexName, rec[0]))

      for q in queries:
        cursor.execute('create index %s on common_bucketdetail (startdate, enddate) where bucket_id  = %%s' % q[0], (q[1],))
        cursor.execute('comment on index %s is %%s' % q[0], (q[1],))


@PlanTaskRegistry.register
# Warning: Deactivated by default. Requires the installation of networkx package
class checkCycles(CheckTask):
  description = "Checking for cycles"
  sequence = 85

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    with connections[database].cursor() as cursor:      

      # Create Directed Graph
      G=networkx.DiGraph()

      # Let's try to be a bit smart here.
      # There are two kinds of possible cycles, cycles within a single location
      # and cycles across multiple locations
      # For cycles across multiple locations, this can only happen if the locations
      # in itemdistribution (without taking the items into consideration) present a cycle

      cursor.execute('select distinct origin_id, location_id from itemdistribution')
      # Adding edges to the directed graph
      G.add_edges_from(cursor.fetchall())

      locationCycles = list(networkx.simple_cycles(G))
      foundLocationCycle = (len(locationCycles)) > 0

      if foundLocationCycle:
        # No luck, there are cycles found in the itemdistribution locations
        # Let's shoot for the full query
        # but limited to the locations that present a cycle
        # This can be a bit optimized but let's start simple

        locationList = []
        for i in locationCycles:
          locationList.extend(i)

        cursor.execute('''
         select item.name||' @ '||origin_id, item.name||' @ '||location_id from itemdistribution
         inner join item do_item on do_item.name = itemdistribution.item_id
         inner join item on item.lft between do_item.lft and do_item.rght and item.lft = item.rght - 1
         inner join location origin on origin.name = itemdistribution.origin_id and origin.name in (%s)
         inner join location dst on dst.name = itemdistribution.location_id and dst.name in (%s)
         union
         select frm_om.item_id||' @ '||operation.location_id, to_om.item_id||' @ '||operation.location_id
         from operation
         inner join operationmaterial frm_om on frm_om.operation_id = operation.name and frm_om.quantity < 0
         inner join operationmaterial to_om on to_om.operation_id = operation.name and to_om.quantity > 0
         where operation.location_id in (%s)
         union
         select all_op.item_id||' @ '||operation.location_id, last_op.item_id||' @ '||operation.location_id from operation
         inner join suboperation all_subop
           on all_subop.operation_id = operation.name
         inner join suboperation last_subop
           on last_subop.operation_id = operation.name
           and not exists (select 1 from suboperation where operation_id = operation.name and priority > last_subop.priority )
         inner join operationmaterial all_op on all_op.operation_id = all_subop.suboperation_id and all_op.quantity < 0
         inner join operationmaterial last_op on last_op.operation_id = last_subop.suboperation_id and last_op.quantity > 0
         where operation.type = 'routing' and operation.location_id in (%s)
         ''' % (
           ', '.join(['%s'] * len(locationList)),
           ', '.join(['%s'] * len(locationList)),
           ', '.join(['%s'] * len(locationList)),
           ', '.join(['%s'] * len(locationList))),
           locationList + locationList + locationList + locationList
           )
        G.clear()
        G.add_edges_from(cursor.fetchall())
        foundCycles = False
        for i in list(networkx.simple_cycles(G)):
          print("Found a cycle : %s" % i  )
          foundCycles = True

        if (foundCycles):
          raise ValueError("Stopping execution because of cycles found in the model (see log file)")

      # Second cycle possibility, within a single location and we need operations for this to happen
      cursor.execute('''
        select frm_om.item_id||' @ '||operation.location_id, to_om.item_id||' @ '||operation.location_id
        from operation
        inner join operationmaterial frm_om on frm_om.operation_id = operation.name and frm_om.quantity < 0
        inner join operationmaterial to_om on to_om.operation_id = operation.name and to_om.quantity > 0
        union
        select all_op.item_id||' @ '||operation.location_id, last_op.item_id||' @ '||operation.location_id from operation
        inner join suboperation all_subop
          on all_subop.operation_id = operation.name
        inner join suboperation last_subop
          on last_subop.operation_id = operation.name
          and not exists (select 1 from suboperation where operation_id = operation.name and priority > last_subop.priority )
        inner join operationmaterial all_op on all_op.operation_id = all_subop.suboperation_id and all_op.quantity < 0
        inner join operationmaterial last_op on last_op.operation_id = last_subop.suboperation_id and last_op.quantity > 0
        where operation.type = 'routing'
      ''')

      G.clear()
      G.add_edges_from(cursor.fetchall())
      foundCycles = False
      for i in list(networkx.simple_cycles(G)):
        print("Found a cycle : %s" % i  )
        foundCycles = True

      if (foundCycles):
        raise ValueError("Stopping execution because of cycles found in the model (see log file)")


@PlanTaskRegistry.register
class loadParameter(LoadTask):

  description = "Importing parameters"
  sequence = 90

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    with connections[database].chunked_cursor() as cursor:
      cursor.execute('''
        SELECT name, value
        FROM common_parameter
        where name in ('currentdate', 'plan.calendar')
        ''')
      default_current_date = True
      for rec in cursor:
        if rec[0] == 'currentdate':
          try:
            frepple.settings.current = datetime.strptime(rec[1], "%Y-%m-%d %H:%M:%S")
            default_current_date = False
          except:
            pass
        elif rec[0] == 'plan.calendar' and rec[1]:
          frepple.settings.calendar = frepple.calendar(name=rec[1])
          logger.info('Bucketized planning using calendar %s' % rec[1])
      if default_current_date:
        frepple.settings.current = datetime.now().replace(microsecond=0)
      logger.info('Current date: %s' % frepple.settings.current)


@PlanTaskRegistry.register
class loadLocations(LoadTask):

  description = "Importing locations"
  sequence = 91

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          name, description, owner_id, available_id, category, subcategory, source
        FROM location %s
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          x = frepple.location(name=i[0], description=i[1], category=i[4], subcategory=i[5], source=i[6])
          if i[2]:
            x.owner = frepple.location(name=i[2])
          if i[3]:
            x.available = frepple.calendar(name=i[3])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d locations in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadCalendars(LoadTask):
  description = "Importing calendars"
  sequence = 92

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          name, defaultvalue, source, 0 hidden
        FROM calendar %s
        union
        SELECT
          name, 0, 'common_bucket', 1 hidden
        FROM common_bucket
        order by name asc
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          frepple.calendar(name=i[0], default=i[1], source=i[2], hidden=i[3])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d calendars in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadCalendarBuckets(LoadTask):

  description = "Importing calendar buckets"
  sequence = 93

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          calendar_id, startdate, enddate, priority, value,
          sunday, monday, tuesday, wednesday, thursday, friday, saturday,
          starttime, endtime, source
        FROM calendarbucket %s
        ORDER BY calendar_id, startdate desc
        ''' % filter_where)
      prevcal = None
      for i in cursor:
        cnt += 1
        try:
          days = 0
          if i[5]:
            days += 1
          if i[6]:
            days += 2
          if i[7]:
            days += 4
          if i[8]:
            days += 8
          if i[9]:
            days += 16
          if i[10]:
            days += 32
          if i[11]:
            days += 64
          if i[0] != prevcal:
            cal = frepple.calendar(name=i[0])
            prevcal = i[0]
          b = frepple.bucket(
            calendar=cal,
            start=i[1],
            end=i[2] if i[2] else datetime(2030, 12, 31),
            priority=i[3],
            source=i[14],
            value=i[4],
            days=days
            )
          if i[12]:
            b.starttime = i[12].hour * 3600 + i[12].minute * 60 + i[12].second
          if i[13]:
            b.endtime = i[13].hour * 3600 + i[13].minute * 60 + i[13].second + 1
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadCustomers(LoadTask):

  description = "Importing customers"
  sequence = 94

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          name, description, owner_id, category, subcategory, source
        FROM customer %s
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          x = frepple.customer(name=i[0], description=i[1], category=i[3], subcategory=i[4], source=i[5])
          if i[2]:
            x.owner = frepple.customer(name=i[2])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d customers in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadSuppliers(LoadTask):

  description = "Importing suppliers"
  sequence = 95

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          name, description, owner_id, category, subcategory, source
        FROM supplier %s
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          x = frepple.supplier(name=i[0], description=i[1], category=i[3], subcategory=i[4], source=i[5])
          if i[2]:
            x.owner = frepple.supplier(name=i[2])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d suppliers in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadOperations(LoadTask):

  description = "Importing operations"
  sequence = 96

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].cursor() as cursor:
      cnt = 0
      starttime = time()

      # Preprocessing step
      # Make sure any routing has the produced item of its last step populated in the operation table
      cursor.execute('''
        update operation
        set item_id = t.item_id
        from (
              select operation.name operation_id, min(operationmaterial.item_id) item_id
               from operation
               inner join suboperation s1 on s1.operation_id = operation.name
               inner join operationmaterial on operationmaterial.operation_id = s1.suboperation_id and quantity > 0
               where operation.type = 'routing'
               and not exists
                  (select 1 from suboperation s2 where s1.operation_id = s2.operation_id and s1.priority < s2.priority)
               group by operation.name
               having count(operationmaterial.item_id) = 1
             ) t
        where operation.type = 'routing'
          and operation.name = t.operation_id
        ''')

      # Preprocessing step
      # Make sure any regular operation (i.e. that has no suboperation and is not a suboperation)
      # has its item_id field populated
      # That should cover 90% of the cases
      cursor.execute('''
        update operation
        set item_id = t.item_id
        from (
              select operation.name operation_id, min(operationmaterial.item_id) item_id
              from operation
              inner join operationmaterial on operationmaterial.operation_id = operation.name and quantity > 0
              where not exists
                    (select 1 from suboperation
                    where suboperation.operation_id = operation.name
                          or suboperation.suboperation_id = operation.name)
                and operation.type not in ('routing', 'alternate', 'split')
              group by operation.name
              having count(operationmaterial.item_id) = 1
             ) t
        where operation.type not in ('routing', 'alternate', 'split')
          and t.operation_id = operation.name
        ''')

      # Preprocessing step
      # Operations that are suboperation of a parent operation shouldn't have
      # the item field set. It is the parent operation that should have it set.
      cursor.execute('''
        update operation
        set item_id = null
        from suboperation
        where operation.name = suboperation.suboperation_id
        and operation.item_id is not null
        ''')

    with connections[database].chunked_cursor() as cursor:

      cursor.execute('''
        SELECT
          name, fence, posttime, sizeminimum, sizemultiple, sizemaximum,
          type, duration, duration_per, location_id, cost, search, description,
          category, subcategory, source, item_id, priority, effective_start,
          effective_end, available_id
        FROM operation %s
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          if not i[6] or i[6] == "fixed_time":
            x = frepple.operation_fixed_time(
              name=i[0], description=i[12], category=i[13], subcategory=i[14], source=i[15]
              )
            if i[7]:
              x.duration = i[7].total_seconds()
          elif i[6] == "time_per":
            x = frepple.operation_time_per(
              name=i[0], description=i[12], category=i[13], subcategory=i[14], source=i[15]
              )
            if i[7]:
              x.duration = i[7].total_seconds()
            if i[8]:
              x.duration_per = i[8].total_seconds()
          elif i[6] == "alternate":
            x = frepple.operation_alternate(
              name=i[0], description=i[12], category=i[13], subcategory=i[14], source=i[15]
              )
          elif i[6] == "split":
            x = frepple.operation_split(
              name=i[0], description=i[12], category=i[13], subcategory=i[14], source=i[15]
              )
          elif i[6] == "routing":
            x = frepple.operation_routing(
              name=i[0], description=i[12], category=i[13], subcategory=i[14], source=i[15]
              )
          else:
            raise ValueError("Operation type '%s' not recognized" % i[6])
          if i[1]:
            x.fence = i[1].total_seconds()
          if i[2]:
            x.posttime = i[2].total_seconds()
          if i[3] is not None:
            x.size_minimum = i[3]
          if i[4]:
            x.size_multiple = i[4]
          if i[5]:
            x.size_maximum = i[5]
          if i[9]:
            x.location = frepple.location(name=i[9])
          if i[10]:
            x.cost = i[10]
          if i[11]:
            x.search = i[11]
          if i[16]:
            x.item = frepple.item(name=i[16])
          if i[17] is not None:
            x.priority = i[17]
          if i[18]:
            x.effective_start = i[18]
          if i[19]:
            x.effective_end = i[19]
          if i[20]:
            x.available = frepple.calendar(name=i[20])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d operations in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadSuboperations(LoadTask):

  description = "Importing suboperations"
  sequence = 97

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_and = "and %s " % cls.filter
    else:
      filter_and = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT operation_id, suboperation_id, priority, effective_start, effective_end,
          (SELECT type
           from operation
           where suboperation.operation_id = operation.name) as type
        FROM suboperation
        WHERE priority >= 0 %s
        ORDER BY operation_id, priority
        ''' % filter_and)
      curopername = None
      for i in cursor:
        cnt += 1
        try:
          if i[0] != curopername:
            curopername = i[0]
            curoper = frepple.operation(name=curopername)
          sub = frepple.suboperation(
            owner=curoper,
            operation=frepple.operation(name=i[1]),
            priority=i[2]
            )
          if i[3]:
            sub.effective_start = i[3]
          if i[4]:
            sub.effective_end = i[4]
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d suboperations in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadItems(LoadTask):

  description = "Importing items"
  sequence = 98

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      attrs = [ f[0] for f in getAttributes(Item) ]
      if attrs:
        attrsql = ', %s' % ', '.join(attrs)
      else:
        attrsql = ''
      cursor.execute('''
        SELECT
          name, description, owner_id,
          cost, category, subcategory, source %s
        FROM item %s
        ''' % (attrsql, filter_where))
      for i in cursor:
        cnt += 1
        try:
          x = frepple.item(name=i[0], description=i[1], category=i[4], subcategory=i[5], source=i[6])
          if i[2]:
            x.owner = frepple.item(name=i[2])
          if i[3]:
            x.cost = i[3]
          idx = 7
          for a in attrs:
            setattr(x, a, i[idx])
            idx += 1
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d items in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadItemSuppliers(LoadTask):

  description = "Importing item suppliers"
  sequence = 99

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          supplier_id, item_id, location_id, sizeminimum, sizemultiple,
          cost, priority, effective_start, effective_end, source, leadtime,
          resource_id, resource_qty, fence
        FROM itemsupplier %s
        ORDER BY supplier_id, item_id, location_id, priority desc
        ''' % filter_where)
      cursuppliername = None
      curitemname = None
      for i in cursor:
        cnt += 1
        try:
          if i[0] != cursuppliername:
            cursuppliername = i[0]
            cursupplier = frepple.supplier(name=cursuppliername)
          if i[1] != curitemname:
            curitemname = i[1]
            curitem = frepple.item(name=curitemname)
          curitemsupplier = frepple.itemsupplier(
            supplier=cursupplier, item=curitem, source=i[9],
            leadtime=i[10].total_seconds() if i[10] else 0,
            fence=i[13].total_seconds() if i[13] else 0,
            resource_qty=i[12]
            )
          if i[2]:
            curitemsupplier.location = frepple.location(name=i[2])
          if i[3]:
            curitemsupplier.size_minimum = i[3]
          if i[4]:
            curitemsupplier.size_multiple = i[4]
          if i[5]:
            curitemsupplier.cost = i[5]
          if i[6] is not None:
            curitemsupplier.priority = i[6]
          if i[7]:
            curitemsupplier.effective_start = i[7]
          if i[8]:
            curitemsupplier.effective_end = i[8]
          if i[11]:
            curitemsupplier.resource = frepple.resource(name=i[11])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d item suppliers in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadItemDistributions(LoadTask):

  description = "Importing item distributions"
  sequence = 100

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          origin_id, item_id, location_id, sizeminimum, sizemultiple,
          cost, priority, effective_start, effective_end, source,
          leadtime, resource_id, resource_qty, fence
        FROM itemdistribution %s
        ORDER BY origin_id, item_id, location_id, priority desc
        ''' % filter_where)
      curoriginname = None
      curitemname = None
      for i in cursor:
        cnt += 1
        try:
          if i[0] != curoriginname:
            curoriginname = i[0]
            curorigin = frepple.location(name=curoriginname)
          if i[1] != curitemname:
            curitemname = i[1]
            curitem = frepple.item(name=curitemname)
          curitemdistribution = frepple.itemdistribution(
            origin=curorigin, item=curitem, source=i[9],
            leadtime=i[10].total_seconds() if i[10] else 0,
            fence=i[13].total_seconds() if i[13] else 0,
            resource_qty=i[12]
            )
          if i[2]:
            curitemdistribution.destination = frepple.location(name=i[2])
          if i[3]:
            curitemdistribution.size_minimum = i[3]
          if i[4]:
            curitemdistribution.size_multiple = i[4]
          if i[5]:
            curitemdistribution.cost = i[5]
          if i[6] is not None:
            curitemdistribution.priority = i[6]
          if i[7]:
            curitemdistribution.effective_start = i[7]
          if i[8]:
            curitemdistribution.effective_end = i[8]
          if i[11]:
            curitemdistribution.resource = frepple.resource(name=i[11])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d item distributions in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadBuffers(LoadTask):

  description = "Importing buffers"
  sequence = 101

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT name, description, location_id, item_id, onhand,
          minimum, minimum_calendar_id, type,
          min_interval, category, subcategory, source
        FROM buffer %s
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        if i[7] == "infinite":
          b = frepple.buffer_infinite(
            name=i[0], description=i[1], location=frepple.location(name=i[2]),
            item=frepple.item(name=i[3]), onhand=max(i[4] or 0, 0),
            category=i[9], subcategory=i[10], source=i[11]
            )
        elif not i[7] or i[7] == "default":
          b = frepple.buffer(
            name=i[0], description=i[1], location=frepple.location(name=i[2]),
            item=frepple.item(name=i[3]), onhand=max(i[4] or 0, 0),
            category=i[9], subcategory=i[10], source=i[11]
            )
          if i[8]:
            b.mininterval = i[8].total_seconds()
        else:
          raise ValueError("Buffer type '%s' not recognized" % i[7])
        if i[10] == 'tool':
          b.tool = True
        if i[5]:
          b.minimum = i[5]
        if i[6]:
          b.minimum_calendar = frepple.calendar(name=i[6])
      logger.info('Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadSetupMatrices(LoadTask):

  description = "Importing setup matrix rules"
  sequence = 102

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT name, source
        FROM setupmatrix %s
        ORDER BY name
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          frepple.setupmatrix(name=i[0], source=i[1])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d setup matrices in %.2f seconds' % (cnt, time() - starttime))

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          setupmatrix_id, priority, fromsetup, tosetup, duration, cost, source
        FROM setuprule %s
        ORDER BY setupmatrix_id, priority DESC
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          frepple.setupmatrixrule(
            setupmatrix=frepple.setupmatrix(name=i[0]),
            priority=i[1],
            fromsetup=i[2],
            tosetup=i[3],
            duration=i[4].total_seconds(),
            cost=i[5],
            source=i[6]
            )
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d setup matrix rules in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadResources(LoadTask):

  description = "Importing resources"
  sequence = 94.5

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      Resource.rebuildHierarchy(database=database)
      cursor.execute('''
        SELECT
          name, description, maximum, maximum_calendar_id, location_id, type,
          cost, maxearly, setup, setupmatrix_id, category, subcategory,
          owner_id, source, available_id, efficiency, efficiency_calendar_id
        FROM %s %s
        ORDER BY lvl ASC, name
        ''' % (connections[cursor.db.alias].ops.quote_name('resource'), filter_where) )
      for i in cursor:
        cnt += 1
        try:
          if i[5] == "infinite":
            x = frepple.resource_infinite(
              name=i[0], description=i[1], category=i[10], subcategory=i[11], source=i[13]
              )
          elif i[5] == "buckets":
            x = frepple.resource_buckets(
              name=i[0], description=i[1], category=i[10], subcategory=i[11], source=i[13]
              )
            if i[7] is not None:
              x.maxearly = i[7]
          elif not i[5] or i[5] == "default":
            x = frepple.resource_default(
              name=i[0], description=i[1], category=i[10], subcategory=i[11], source=i[13]
              )
            if i[7] is not None:
              x.maxearly = i[7].total_seconds()
            if i[2] is not None:
              x.maximum = i[2]
          else:
            raise ValueError("Resource type '%s' not recognized" % i[5])
          if i[3]:
            x.maximum_calendar = frepple.calendar(name=i[3])
          if i[4]:
            x.location = frepple.location(name=i[4])
          if i[6]:
            x.cost = i[6]
          if i[8]:
            x.setup = i[8]
          if i[9]:
            x.setupmatrix = frepple.setupmatrix(name=i[9])
          if i[12]:
            x.owner = frepple.resource(name=i[12])
          if i[14]:
            x.available = frepple.calendar(name=i[14])
          if i[15] is not None:
            x.efficiency = i[15]
          if i[16]:
            x.efficiency_calendar = frepple.calendar(name=i[16])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d resources in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadResourceSkills(LoadTask):

  description = "Importing resources skills"
  sequence = 104

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          resource_id, skill_id, effective_start, effective_end, priority, source
        FROM resourceskill %s
        ORDER BY skill_id, priority, resource_id
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          cur = frepple.resourceskill(
            resource=frepple.resource(name=i[0]), skill=frepple.skill(name=i[1]),
            priority=i[4] or 1, source=i[5]
            )
          if i[2]:
            cur.effective_start = i[2]
          if i[3]:
            cur.effective_end = i[3]
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d resource skills in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadOperationMaterials(LoadTask):

  description = "Importing operation materials"
  sequence = 105

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      # Note: The sorting of the flows is not really necessary, but helps to make
      # the planning progress consistent across runs and database engines.
      cursor.execute('''
        SELECT
          operation_id, item_id, quantity, type, effective_start,
          effective_end, name, priority, search, source, transferbatch, quantity_fixed
        FROM operationmaterial %s
        ORDER BY operation_id, item_id
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          curflow = frepple.flow(
            operation=frepple.operation(name=i[0]),
            item=frepple.item(name=i[1]),
            quantity=i[2],
            quantity_fixed=i[11],
            type="flow_%s" % i[3],
            source=i[9]
            )
          if i[4]:
            curflow.effective_start = i[4]
          if i[5]:
            curflow.effective_end = i[5]
          if i[6]:
            curflow.name = i[6]
          if i[7]:
            curflow.priority = i[7]
          if i[8]:
            curflow.search = i[8]
          if i[10] and i[3] == 'transfer_batch':
            curflow.transferbatch = i[10]
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d operation materials in %.2f seconds' % (cnt, time() - starttime))

      # Check for operations where:
      #  - operation.item is still blank
      #  - they have a single operationmaterial item with quantity > 0
      # If found we update
      starttime = time()
      cnt = 0
      logger.info('Auto-update operation items...')
      for oper in frepple.operations():
        if oper.hidden or oper.item or oper.hasSuperOperations:
          continue
        item = None
        for fl in oper.flows:
          if fl.quantity < 0 or fl.hidden:
            continue
          if item and item != fl.item:
            item = None
            break
          else:
            item = fl.item
        if item:
          cnt += 1
          oper.item = item
      logger.info('Auto-update of %s operation items in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadOperationResources(LoadTask):

  description = "Importing operation resources"
  sequence = 106

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_where = "where %s " % cls.filter
    else:
      filter_where = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      # Note: The sorting of the loads is not really necessary, but helps to make
      # the planning progress consistent across runs and database engines.
      cursor.execute('''
        SELECT
          operation_id, resource_id, quantity, effective_start, effective_end, name,
          priority, setup, search, skill_id, source
        FROM operationresource %s
        ORDER BY operation_id, resource_id
        ''' % filter_where)
      for i in cursor:
        cnt += 1
        try:
          curload = frepple.load(
            operation=frepple.operation(name=i[0]),
            resource=frepple.resource(name=i[1]),
            quantity=i[2],
            source=i[10]
            )
          if i[3]:
            curload.effective_start = i[3]
          if i[4]:
            curload.effective_end = i[4]
          if i[5]:
            curload.name = i[5]
          if i[6]:
            curload.priority = i[6]
          if i[7]:
            curload.setup = i[7]
          if i[8]:
            curload.search = i[8]
          if i[9]:
            curload.skill = frepple.skill(name=i[9])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d resource loads in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadDemand(LoadTask):

  description = "Importing demands"
  sequence = 107

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_and = "and %s " % cls.filter
    else:
      filter_and = ""

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        SELECT
          name, due, quantity, priority, item_id,
          operation_id, customer_id, owner_id, minshipment, maxlateness,
          category, subcategory, source, location_id, status
        FROM demand
        WHERE (status IS NULL OR status ='open' OR status = 'quote') %s
        ''' % filter_and)
      for i in cursor:
        cnt += 1
        try:
          x = frepple.demand(
            name=i[0], due=i[1], quantity=i[2], priority=i[3], status=i[14],
            item=frepple.item(name=i[4]), category=i[10], subcategory=i[11],
            source=i[12]
            )
          if i[5]:
            x.operation = frepple.operation(name=i[5])
          if i[6]:
            x.customer = frepple.customer(name=i[6])
          if i[7]:
            x.owner = frepple.demand(name=i[7])
          if i[8] is not None:
            x.minshipment = i[8]
          if i[9] is not None:
            x.maxlateness = i[9].total_seconds()
          if i[13]:
            x.location = frepple.location(name=i[13])
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d demands in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadOperationPlans(LoadTask):

  description = "Importing operationplans"
  sequence = 108

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    if cls.filter:
      filter_and = "and %s " % cls.filter
    else:
      filter_and = ""

    with connections[database].chunked_cursor() as cursor:
      if 'supply' in os.environ:
        confirmed_filter = " and operationplan.status in ('confirmed', 'approved')"
        create_flag = True
      else:
        confirmed_filter = ""
        create_flag = False
      cnt_mo = 0
      cnt_po = 0
      cnt_do = 0
      cnt_dlvr = 0
      starttime = time()
      cursor.execute('''
        SELECT
          operationplan.operation_id, operationplan.id, operationplan.quantity,
          operationplan.startdate, operationplan.enddate, operationplan.status, operationplan.source,
          operationplan.type, operationplan.origin_id, operationplan.destination_id, operationplan.supplier_id,
          operationplan.item_id, operationplan.location_id,
          reference, coalesce(dmd.name, null)
        FROM operationplan
        LEFT OUTER JOIN (select name from demand
          where demand.status = 'open'
          ) dmd
        on dmd.name = operationplan.demand_id
        WHERE operationplan.owner_id IS NULL
          and operationplan.quantity >= 0 and operationplan.status <> 'closed'
          %s%s and operationplan.type in ('PO', 'MO', 'DO', 'DLVR')
          and (operationplan.startdate is null or operationplan.startdate < '2030-12-31')
          and (operationplan.enddate is null or operationplan.enddate < '2030-12-31')
        ORDER BY operationplan.id ASC
        ''' % (filter_and, confirmed_filter))
      for i in cursor:
        try:
          if i[7] == 'MO':
            cnt_mo += 1
            opplan = frepple.operationplan(
              operation=frepple.operation(name=i[0]), id=i[1],
              quantity=i[2], source=i[6], start=i[3], end=i[4],
              status=i[5], reference=i[13], create=create_flag
              )
          elif i[7] == 'PO':
            cnt_po += 1
            opplan = frepple.operationplan(
              location=frepple.location(name=i[12]), ordertype=i[7],
              id=i[1], reference=i[13],
              item=frepple.item(name=i[11]) if i[11] else None,
              supplier=frepple.supplier(name=i[10]) if i[10] else None,
              quantity=i[2], start=i[3], end=i[4],
              status=i[5], source=i[6], create=create_flag
              )
          elif i[7] == 'DO':
            cnt_do += 1
            opplan = frepple.operationplan(
              location=frepple.location(name=i[9]) if i[9] else None,
              id=i[1], reference=i[13], ordertype=i[7],
              item=frepple.item(name=i[11]) if i[11] else None,
              origin=frepple.location(name=i[8]) if i[8] else None,
              quantity=i[2], start=i[3], end=i[4],
              status=i[5], source=i[6], create=create_flag
              )
          elif i[7] == 'DLVR':
            cnt_dlvr += 1
            opplan = frepple.operationplan(
              location=frepple.location(name=i[12]) if i[12] else None,
              id=i[1], reference=i[13], ordertype=i[7],
              item=frepple.item(name=i[11]) if i[11] else None,
              origin=frepple.location(name=i[8]) if i[8] else None,
              demand=frepple.demand(name=i[14]) if i[14] else None,
              quantity=i[2], start=i[3], end=i[4],
              status=i[5], source=i[6], create=create_flag
              )
            opplan = None
          else:
            logger.warning("Warning: unhandled operationplan type '%s'" % i[7])
            continue
          if i[14] and opplan:
            opplan.demand = frepple.demand(name=i[14])
        except Exception as e:
          logger.error("**** %s ****" % e)
    with connections[database].chunked_cursor() as cursor:
      cursor.execute('''
        SELECT
          operationplan.operation_id, operationplan.id, operationplan.quantity,
          operationplan.startdate, operationplan.enddate, operationplan.status,
          operationplan.owner_id, operationplan.source, operationplan.reference,
          coalesce(dmd.name, null)
        FROM operationplan
        INNER JOIN (select id
          from operationplan
          ) opplan_parent
        on operationplan.owner_id = opplan_parent.id
        LEFT OUTER JOIN (select name from demand
          where demand.status = 'open'
          ) dmd
        on dmd.name = operationplan.demand_id
        WHERE operationplan.quantity >= 0 and operationplan.status <> 'closed'
          %s%s and operationplan.type = 'MO'
          and (operationplan.startdate is null or operationplan.startdate < '2030-12-31')
          and (operationplan.enddate is null or operationplan.enddate < '2030-12-31')
        ORDER BY operationplan.id ASC
        ''' % (filter_and, confirmed_filter))
      for i in cursor:
        cnt_mo += 1
        opplan = frepple.operationplan(
          operation=frepple.operation(name=i[0]),
          id=i[1], quantity=i[2], source=i[7],
          start=i[3], end=i[4], status=i[5], reference=i[8]
          )
        if i[6] and opplan:
          try:
            opplan.owner = frepple.operationplan(id=i[6])
          except:
            pass
        if i[9] and opplan:
          opplan.demand = frepple.demand(name=i[9])
      logger.info('Loaded %d manufacturing orders, %d purchase orders, %d distribution orders and %s deliveries in %.2f seconds' % (cnt_mo, cnt_po, cnt_do, cnt_dlvr, time() - starttime))

    with connections[database].cursor() as cursor:
      # Assure the operationplan ids will be unique.
      # We call this method only at the end, as calling it earlier gives a slower
      # performance to load operationplans
      cursor.execute('''
        select coalesce(max(id),1) + 1 as max_id
        from operationplan
        ''')
      d = cursor.fetchone()
      frepple.settings.id = d[0]


@PlanTaskRegistry.register
class loadOperationPlanMaterials(LoadTask):

  description = "Importing operationplanmaterials"
  sequence = 109

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        select
          quantity, flowdate, operationplan_id, item_id, location_id, status
        from operationplanmaterial
        where status <> 'proposed'
      ''')
      for i in cursor:
        cnt += 1
        try:
          opplan = frepple.operationplan(id=i[2])
          if opplan.status not in ("confirmed", "approved"):
            pass
          for fl in opplan.flowplans:
            if fl.buffer.item and fl.buffer.item.name == i[3] \
              and fl.buffer.location and fl.buffer.location.name == i[4]:
                fl.status = "confirmed"
                if i[1]:
                  fl.date = i[1]
                fl.quantity = i[0]
                break
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d operationplanmaterials in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class loadOperationPlanResources(LoadTask):

  description = "Importing operationplanresources"
  sequence = 110

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple

    with connections[database].chunked_cursor() as cursor:
      cnt = 0
      starttime = time()
      cursor.execute('''
        select resource_id, quantity, operationplan_id
        from operationplanresource
        where status <> 'proposed'
      ''')
      for i in cursor:
        cnt += 1
        try:
          opplan = frepple.operationplan(id=i[2])
          if opplan.status not in ("confirmed", "approved"):
            pass
          for lo in opplan.loadplans:
            if lo.resource.name == i[0]:
              lo.status = "confirmed"
              lo.quantity = i[1]
        except Exception as e:
          logger.error("**** %s ****" % e)
      logger.info('Loaded %d operationplanresources in %.2f seconds' % (cnt, time() - starttime))


@PlanTaskRegistry.register
class PlanSize(CheckTask):

  description = "Plan Size"
  sequence = 120

  @staticmethod
  def run(database=DEFAULT_DB_ALIAS, **kwargs):
    '''
    It is important that all data is loaded at this point. We build out
    all buffers and their supply paths at this point.
    If new replenishment methods are added later on, they will not be used.
    '''
    import frepple
    frepple.printsize()
