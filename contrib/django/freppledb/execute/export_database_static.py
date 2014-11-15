#
# Copyright (C) 2011-2013 by Johan De Taeye, frePPLe bvba
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

r'''
Exports frePPLe information into a database.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

The code iterates over all objects in the C++ core engine, and creates
database records with the information. The Django database wrappers are used
to keep the code portable between different databases.
'''
import datetime
from time import time
from threading import Thread
import os
import traceback

from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings

import frepple


class exportStaticModel(object):

  def __init__(self, database=None, source=None):
    if database:
      self.database = database
    elif 'FREPPLE_DATABASE' in os.environ:
      self.database = os.environ['FREPPLE_DATABASE']
    else:
      self.database = DEFAULT_DB_ALIAS
    self.source = source


  def exportLocations(self, cursor):
    print("Exporting locations...")
    starttime = time()
    cursor.execute("SELECT name FROM location")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      "insert into location \
      (name,description,available_id,category,subcategory,source,lastmodified) \
      values(%s,%s,%s,%s,%s,%s,%s)",
      [
        (
          i.name, i.description, i.available and i.available.name or None,
          i.category, i.subcategory, i.source, self.timestamp
        )
        for i in frepple.locations()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update location \
       set description=%s, available_id=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s \
       where name=%s",
      [
        (
          i.description, i.available and i.available.name or None,
          i.category, i.subcategory, i.source, self.timestamp, i.name
        )
        for i in frepple.locations()
        if i.name in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update location set owner_id=%s where name=%s",
      [
        (i.owner.name, i.name)
        for i in frepple.locations()
        if i.owner and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported locations in %.2f seconds' % (time() - starttime))


  def exportCalendars(self, cursor):
    print("Exporting calendars...")
    starttime = time()
    cursor.execute("SELECT name FROM calendar")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      "insert into calendar \
      (name,defaultvalue,source,lastmodified) \
      values(%s,%s,%s,%s)",
      [
        (
          i.name, round(i.default, settings.DECIMAL_PLACES), i.source,
          self.timestamp
        )
        for i in frepple.calendars()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update calendar \
       set defaultvalue=%s, source=%s, lastmodified=%s \
       where name=%s",
      [
        (
          round(i.default, settings.DECIMAL_PLACES), i.source, self.timestamp,
          i.name
        )
        for i in frepple.calendars()
        if i.name in primary_keys and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported calendars in %.2f seconds' % (time() - starttime))


  def exportCalendarBuckets(self, cursor):
    print("Exporting calendar buckets...")
    starttime = time()
    cursor.execute("delete from calendarbucket where source = %s", [self.source])

    def buckets():
      cursor.execute("SELECT max(id) FROM calendarbucket")
      cnt = cursor.fetchone()[0] or 1
      for c in frepple.calendars():
        if self.source and self.source != c.source:
          continue
        for i in c.buckets:
          cnt += 1
          yield i, cnt

    def int_to_time(i):
      hour = i // 3600
      i -= (hour * 3600)
      minute = i // 60
      i -= (minute * 60)
      second = i
      if hour >= 24:
        hour -= 24
      return "%s:%s:%s" % (hour, minute, second)

    cursor.executemany(
      '''insert into calendarbucket
      (calendar_id,startdate,enddate,id,priority,value,
       sunday,monday,tuesday,wednesday,thursday,friday,saturday,
       starttime,endtime,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
        (
          i[0].calendar.name, str(i[0].start), str(i[0].end), i[1], i[0].priority,
          round(i[0].value, settings.DECIMAL_PLACES),
          (i[0].days & 1) and True or False, (i[0].days & 2) and True or False,
          (i[0].days & 4) and True or False, (i[0].days & 8) and True or False,
          (i[0].days & 16) and True or False, (i[0].days & 32) and True or False,
          (i[0].days & 64) and True or False,
          int_to_time(i[0].starttime), int_to_time(i[0].endtime - 1),
          i[0].calendar.source, self.timestamp
        )
        for i in buckets()
      ])
    transaction.commit(using=self.database)
    print('Exported calendar buckets in %.2f seconds' % (time() - starttime))


  def exportOperations(self, cursor):
    print("Exporting operations...")
    starttime = time()
    cursor.execute("SELECT name FROM operation")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      '''insert into operation
      (name,fence,posttime,sizeminimum,sizemultiple,sizemaximum,type,duration,
       duration_per,location_id,cost,search,description,category,subcategory,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
        (
          i.name, i.fence, i.posttime, round(i.size_minimum, settings.DECIMAL_PLACES),
          round(i.size_multiple, settings.DECIMAL_PLACES),
          i.size_maximum < 9999999999999 and round(i.size_maximum, settings.DECIMAL_PLACES) or None,
          i.__class__.__name__[10:],
          isinstance(i, (frepple.operation_fixed_time, frepple.operation_time_per)) and i.duration or None,
          isinstance(i, frepple.operation_time_per) and i.duration_per or None,
          i.location and i.location.name or None, round(i.cost, settings.DECIMAL_PLACES),
          isinstance(i, frepple.operation_alternate) and i.search or None,
          i.description, i.category, i.subcategory, i.source, self.timestamp
        )
        for i in frepple.operations()
        if i.name not in primary_keys and not i.hidden and i.name != 'setup operation' and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update operation
       set fence=%s, posttime=%s, sizeminimum=%s, sizemultiple=%s,
       sizemaximum=%s, type=%s, duration=%s, duration_per=%s, location_id=%s, cost=%s, search=%s,
       description=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s
       where name=%s''',
      [
        (
          i.fence, i.posttime, round(i.size_minimum, settings.DECIMAL_PLACES),
          round(i.size_multiple, settings.DECIMAL_PLACES),
          i.size_maximum < 9999999999999 and round(i.size_maximum, settings.DECIMAL_PLACES) or None,
          i.__class__.__name__[10:],
          isinstance(i, (frepple.operation_fixed_time, frepple.operation_time_per)) and i.duration or None,
          isinstance(i, frepple.operation_time_per) and i.duration_per or None,
          i.location and i.location.name or None, round(i.cost, settings.DECIMAL_PLACES),
          isinstance(i, frepple.operation_alternate) and i.search or None,
          i.description, i.category, i.subcategory, i.source, self.timestamp, i.name
        )
        for i in frepple.operations()
        if i.name in primary_keys and not i.hidden and i.name != 'setup operation' and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported operations in %.2f seconds' % (time() - starttime))


  def exportSubOperations(self, cursor):
    print("Exporting suboperations...")
    starttime = time()
    cursor.execute("SELECT operation_id, suboperation_id FROM suboperation")
    primary_keys = set([ i for i in cursor.fetchall() ])

    def subops():
      for i in frepple.operations():
        if isinstance(i, frepple.operation_alternate):
          for j in i.alternates:
            yield i, j[0], j[1], j[2], j[3], i.source
        elif isinstance(i, frepple.operation_split):
          for j in i.alternates:
            yield i, j[0], j[1], j[2], j[3], i.source
        elif isinstance(i, frepple.operation_routing):
          cnt = 1
          for j in i.steps:
            yield i, j, cnt, None, None, i.source
            cnt += 1

    cursor.executemany(
      "insert into suboperation \
      (operation_id,suboperation_id,priority,effective_start,effective_end,source,lastmodified) \
      values(%s,%s,%s,%s,%s,%s,%s)",
      [
        (i[0].name, i[1].name, i[2], i[3], i[4], i[5], self.timestamp)
        for i in subops()
        if (i[0].name, i[1].name) not in primary_keys and (not self.source or self.source == i[5])
      ])
    cursor.executemany(
      "update suboperation \
       set priority=%s, effective_start=%s, effective_end=%s, source=%s, lastmodified=%s \
       where operation_id=%s and suboperation_id=%s",
      [
        (i[2], i[3], i[4], i[5], self.timestamp, i[0].name, i[1].name)
        for i in subops()
        if (i[0].name, i[1].name) in primary_keys and (not self.source or self.source == i[5])
      ])
    transaction.commit(using=self.database)
    print('Exported suboperations in %.2f seconds' % (time() - starttime))


  def exportFlows(self, cursor):
    print("Exporting flows...")
    starttime = time()
    cursor.execute("SELECT operation_id, thebuffer_id FROM flow")  # todo oper&buffer are not necesarily unique
    primary_keys = set([ i for i in cursor.fetchall() ])

    def flows():
      for o in frepple.operations():
        for i in o.flows:
          yield i

    cursor.executemany(
      '''insert into flow
      (operation_id,thebuffer_id,quantity,type,effective_start,effective_end,name,priority,
      search,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
        (
          i.operation.name, i.buffer.name, round(i.quantity, settings.DECIMAL_PLACES),
          i.type[5:], str(i.effective_start), str(i.effective_end),
          i.name, i.priority, i.search != 'PRIORITY' and i.search or None, i.source, self.timestamp
        )
        for i in flows()
        if (i.operation.name, i.buffer.name) not in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update flow
       set quantity=%s, type=%s, effective_start=%s, effective_end=%s, name=%s,
       priority=%s, search=%s, source=%s, lastmodified=%s
       where operation_id=%s and thebuffer_id=%s''',
      [
        (
          round(i.quantity, settings.DECIMAL_PLACES),
          i.type[5:], str(i.effective_start), str(i.effective_end),
          i.name, i.priority, i.search != 'PRIORITY' and i.search or None, i.source,
          self.timestamp, i.operation.name, i.buffer.name,
        )
        for i in flows()
        if (i.operation.name, i.buffer.name) in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported flows in %.2f seconds' % (time() - starttime))


  def exportLoads(self, cursor):
    print("Exporting loads...")
    starttime = time()
    cursor.execute("SELECT operation_id, resource_id FROM resourceload")  # todo oper&resource are not necesarily unique
    primary_keys = set([ i for i in cursor.fetchall() ])

    def loads():
      for o in frepple.operations():
        for i in o.loads:
          yield i

    cursor.executemany(
      '''insert into resourceload
      (operation_id,resource_id,quantity,setup,effective_start,effective_end,name,priority,
      search,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
        (
          i.operation.name, i.resource.name, round(i.quantity, settings.DECIMAL_PLACES),
          i.setup, str(i.effective_start), str(i.effective_end),
          i.name, i.priority, i.search != 'PRIORITY' and i.search or None,
          i.source, self.timestamp
        )
        for i in loads()
        if (i.operation.name, i.resource.name) not in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update resourceload
       set quantity=%s, setup=%s, effective_start=%s, effective_end=%s, name=%s,
       priority=%s, search=%s, source=%s, lastmodified=%s
       where operation_id=%s and resource_id=%s''',
      [
        (
          round(i.quantity, settings.DECIMAL_PLACES),
          i.setup, str(i.effective_start), str(i.effective_end),
          i.name, i.priority, i.search != 'PRIORITY' and i.search or None,
          i.source, self.timestamp, i.operation.name, i.resource.name,
        )
        for i in loads()
        if (i.operation.name, i.resource.name) in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported loads in %.2f seconds' % (time() - starttime))


  def exportBuffers(self, cursor):
    print("Exporting buffers...")
    starttime = time()
    cursor.execute("SELECT name FROM buffer")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      '''insert into buffer
      (name,description,location_id,item_id,onhand,minimum,minimum_calendar_id,
       producing_id,type,leadtime,min_inventory,
       max_inventory,min_interval,max_interval,size_minimum,
       size_multiple,size_maximum,fence,
       carrying_cost,category,subcategory,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
        (
          i.name, i.description, i.location and i.location.name or None,
          i.item and i.item.name or None,
          round(i.onhand, settings.DECIMAL_PLACES), round(i.minimum, settings.DECIMAL_PLACES),
          i.minimum_calendar and i.minimum_calendar.name or None,
          (not isinstance(i, frepple.buffer_procure) and i.producing) and i.producing.name or None,
          i.__class__.__name__[7:],
          isinstance(i, frepple.buffer_procure) and i.leadtime or None,
          isinstance(i, frepple.buffer_procure) and round(i.mininventory, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and round(i.maxinventory, settings.DECIMAL_PLACES) or None,
          i.mininterval,
          i.maxinterval < 99999999999 and i.maxinterval or None,
          isinstance(i, frepple.buffer_procure) and round(i.size_minimum, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and round(i.size_multiple, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and i.size_maximum < 99999999999 and round(i.size_maximum, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and i.fence or None,
          round(i.carrying_cost, settings.DECIMAL_PLACES), i.category, i.subcategory,
          i.source, self.timestamp
        )
        for i in frepple.buffers()
        if i.name not in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update buffer
       set description=%s, location_id=%s, item_id=%s, onhand=%s, minimum=%s, minimum_calendar_id=%s,
       producing_id=%s, type=%s, leadtime=%s, min_inventory=%s, max_inventory=%s, min_interval=%s,
       max_interval=%s, size_minimum=%s, size_multiple=%s, size_maximum=%s, fence=%s,
       carrying_cost=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s
       where name=%s''',
      [
        (
          i.description, i.location and i.location.name or None, i.item and i.item.name or None,
          round(i.onhand, settings.DECIMAL_PLACES), round(i.minimum, settings.DECIMAL_PLACES),
          i.minimum_calendar and i.minimum_calendar.name or None,
          (not isinstance(i, frepple.buffer_procure) and i.producing) and i.producing.name or None,
          i.__class__.__name__[7:],
          isinstance(i, frepple.buffer_procure) and i.leadtime or None,
          isinstance(i, frepple.buffer_procure) and round(i.mininventory, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and round(i.maxinventory, settings.DECIMAL_PLACES) or None,
          (i.mininterval!=-1) and i.mininterval or None,
          i.maxinterval < 99999999999 and i.maxinterval or None,
          isinstance(i, frepple.buffer_procure) and round(i.size_minimum, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and round(i.size_multiple, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and i.size_maximum < 99999999999 and round(i.size_maximum, settings.DECIMAL_PLACES) or None,
          isinstance(i, frepple.buffer_procure) and i.fence or None,
          round(i.carrying_cost, settings.DECIMAL_PLACES), i.category, i.subcategory,
          i.source, self.timestamp, i.name
        )
        for i in frepple.buffers()
        if i.name in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update buffer set owner_id=%s where name=%s",
      [
        (i.owner.name, i.name)
        for i in frepple.buffers()
        if i.owner and not i.hidden
      ])
    transaction.commit(using=self.database)
    print('Exported buffers in %.2f seconds' % (time() - starttime))


  def exportCustomers(self, cursor):
    print("Exporting customers...")
    starttime = time()
    cursor.execute("SELECT name FROM customer")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      "insert into customer \
      (name,description,category,subcategory,source,lastmodified) \
      values(%s,%s,%s,%s,%s,%s)",
      [
        (i.name, i.description, i.category, i.subcategory, i.source, self.timestamp)
        for i in frepple.customers()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update customer \
       set description=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s \
       where name=%s",
      [
        (i.description, i.category, i.subcategory, i.source, self.timestamp, i.name)
        for i in frepple.customers()
        if i.name in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update customer set owner_id=%s where name=%s",
      [
        (i.owner.name, i.name)
        for i in frepple.customers()
        if i.owner and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported customers in %.2f seconds' % (time() - starttime))


  def exportSuppliers(self, cursor):
    print("Exporting suppliers...")
    starttime = time()
    cursor.execute("SELECT name FROM supplier")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      "insert into supplier \
      (name,description,category,subcategory,source,lastmodified) \
      values(%s,%s,%s,%s,%s,%s)",
      [
        (i.name, i.description, i.category, i.subcategory, i.source, self.timestamp)
        for i in frepple.suppliers()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update supplier \
       set description=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s \
       where name=%s",
      [
        (i.description, i.category, i.subcategory, i.source, self.timestamp, i.name)
        for i in frepple.suppliers()
        if i.name in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update supplier set owner_id=%s where name=%s",
      [
        (i.owner.name, i.name)
        for i in frepple.suppliers()
        if i.owner and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported suppliers in %.2f seconds' % (time() - starttime))


  def exportDemands(self, cursor):
    print("Exporting demands...")
    starttime = time()
    cursor.execute("SELECT name FROM demand")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      '''insert into demand
      (name,due,quantity,priority,item_id,operation_id,customer_id,
       minshipment,maxlateness,category,subcategory,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
        (
          i.name, str(i.due), round(i.quantity, settings.DECIMAL_PLACES), i.priority, i.item.name,
          i.operation and i.operation.name or None, i.customer and i.customer.name or None,
          round(i.minshipment, settings.DECIMAL_PLACES), round(i.maxlateness, settings.DECIMAL_PLACES),
          i.category, i.subcategory, i.source, self.timestamp
        )
        for i in frepple.demands()
        if i.name not in primary_keys and isinstance(i, frepple.demand_default) and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update demand
       set due=%s, quantity=%s, priority=%s, item_id=%s, operation_id=%s, customer_id=%s,
       minshipment=%s, maxlateness=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s
       where name=%s''',
      [
        (
          str(i.due), round(i.quantity, settings.DECIMAL_PLACES), i.priority,
          i.item.name, i.operation and i.operation.name or None,
          i.customer and i.customer.name or None,
          round(i.minshipment, settings.DECIMAL_PLACES),
          round(i.maxlateness, settings.DECIMAL_PLACES),
          i.category, i.subcategory, i.source, self.timestamp, i.name
        )
        for i in frepple.demands()
        if i.name in primary_keys and isinstance(i, frepple.demand_default) and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update demand set owner_id=%s where name=%s",
      [
        (i.owner.name, i.name)
        for i in frepple.demands()
        if i.owner and isinstance(i, frepple.demand_default) and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported demands in %.2f seconds' % (time() - starttime))


  def exportOperationPlans(self, cursor):
    '''
    Only locked operationplans are exported. That because we assume that
    all of those were given as input.
    '''
    print("Exporting operationplans...")
    starttime = time()
    cursor.execute("SELECT id FROM operationplan")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      '''insert into operationplan
      (id,operation_id,quantity,startdate,enddate,locked,source,lastmodified)
      values(%s,%s,%s,%s,%s,%s,%s,%s)''',
      [
       (
         i.id, i.operation.name, round(i.quantity, settings.DECIMAL_PLACES),
         str(i.start), str(i.end), i.locked, i.source, self.timestamp
       )
       for i in frepple.operationplans()
       if i.locked and not i.operation.hidden and i.id not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update operationplan
       set operation_id=%s, quantity=%s, startdate=%s, enddate=%s, locked=%s, source=%s, lastmodified=%s
       where id=%s''',
      [
       (
         i.operation.name, round(i.quantity, settings.DECIMAL_PLACES),
         str(i.start), str(i.end), i.locked, i.source, self.timestamp, i.id
       )
       for i in frepple.operationplans()
       if i.locked and not i.operation.hidden and i.id in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update operationplan set owner_id=%s where id=%s",
      [
        (i.owner.id, i.id)
        for i in frepple.operationplans()
        if i.owner and not i.operation.hidden and i.locked and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported operationplans in %.2f seconds' % (time() - starttime))


  def exportResources(self, cursor):
    print("Exporting resources...")
    starttime = time()
    cursor.execute("SELECT name FROM %s" % connections[self.database].ops.quote_name('resource'))
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      '''insert into %s
      (name,description,maximum,maximum_calendar_id,location_id,type,cost,
       maxearly,setup,setupmatrix_id,category,subcategory,source,lastmodified)
      values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)''' % connections[self.database].ops.quote_name('resource'),
      [
        (
          i.name, i.description, i.maximum, i.maximum_calendar and i.maximum_calendar.name or None,
          i.location and i.location.name or None, i.__class__.__name__[9:],
          round(i.cost, settings.DECIMAL_PLACES), round(i.maxearly, settings.DECIMAL_PLACES),
          i.setup, i.setupmatrix and i.setupmatrix.name or None,
          i.category, i.subcategory, i.source, self.timestamp
        )
        for i in frepple.resources()
        if i.name not in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update %s
       set description=%%s, maximum=%%s, maximum_calendar_id=%%s, location_id=%%s,
       type=%%s, cost=%%s, maxearly=%%s, setup=%%s, setupmatrix_id=%%s, category=%%s,
       subcategory=%%s, source=%%s, lastmodified=%%s
       where name=%%s''' % connections[self.database].ops.quote_name('resource'),
      [
        (
          i.description, i.maximum,
          i.maximum_calendar and i.maximum_calendar.name or None,
          i.location and i.location.name or None, i.__class__.__name__[9:],
          round(i.cost, settings.DECIMAL_PLACES),
          round(i.maxearly, settings.DECIMAL_PLACES),
          i.setup, i.setupmatrix and i.setupmatrix.name or None,
          i.category, i.subcategory, i.source, self.timestamp, i.name
        )
        for i in frepple.resources()
        if i.name in primary_keys and not i.hidden and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update %s set owner_id=%%s where name=%%s" % connections[self.database].ops.quote_name('resource'),
      [
        (i.owner.name, i.name)
        for i in frepple.resources()
        if i.owner and not i.hidden and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported resources in %.2f seconds' % (time() - starttime))


  def exportSkills(self, cursor):
    print("Exporting skills...")
    starttime = time()
    cursor.execute("SELECT name FROM skill")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      '''insert into skill (name,source,lastmodified) values(%s,%s,%s)''',
      [
        ( i.name, i.source, self.timestamp )
        for i in frepple.skills()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update skill set source=%s, lastmodified=%s where name=%s''',
      [
        (i.source, self.timestamp, i.name)
        for i in frepple.skills()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported skills in %.2f seconds' % (time() - starttime))


  def exportResourceSkills(self, cursor):
    print("Exporting resource skills...")
    starttime = time()
    cursor.execute("SELECT resource_id, skill_id FROM resourceskill")  # todo resource&skill are not necesarily unique
    primary_keys = set([ i for i in cursor.fetchall() ])

    def res_skills():
      for s in frepple.skills():
        for r in s.resources:
          yield (r.effective_start, r.effective_end, r.priority, r.source, self.timestamp, r.name, s.name)

    cursor.executemany(
      '''insert into resourceskill
      (effective_start,effective_end,priority,source,lastmodified,resource_id,skill_id)
      values(%s,%s,%s,%s,%s,%s,%s)''',
      [
        i for i in res_skills()
        if i not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      '''update resourceskill
      set effective_start=%s, effective_end=%s, priority=%s, source=%s, lastmodified=%s
      where resource_id=%s and skill_id=%s''',
      [
        i for i in res_skills()
        if i not in primary_keys and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported resource skills in %.2f seconds' % (time() - starttime))


  def exportSetupMatrices(self, cursor):
    print("Exporting setup matrices...")
    starttime = time()
    cursor.execute("SELECT name FROM setupmatrix")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      "insert into setupmatrix \
      (name,source,lastmodified) \
      values(%s,%s,%s)",
      [
        (i.name, i.source, self.timestamp)
        for i in frepple.setupmatrices()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update setupmatrix \
       set source=%s, lastmodified=%s \
       where name=%s",
      [
        (i.source, self.timestamp, i.name)
        for i in frepple.setupmatrices()
        if i.name in primary_keys and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported setupmatrices in %.2f seconds' % (time() - starttime))


  def exportSetupMatricesRules(self, cursor):
    print("Exporting setup matrix rules...")
    starttime = time()
    cursor.execute("SELECT setupmatrix_id, priority FROM setuprule")
    primary_keys = set([ i for i in cursor.fetchall() ])

    def matrixrules():
      for m in frepple.setupmatrices():
        for i in m.rules:
          yield m, i

    cursor.executemany(
      "insert into setuprule \
      (setupmatrix_id,priority,fromsetup,tosetup,duration,cost,source,lastmodified) \
      values(%s,%s,%s,%s,%s,%s,%s,%s)",
      [
       (
         i[0].name, i[1].priority, i[1].fromsetup, i[1].tosetup, i[1].duration,
         round(i[1].cost, settings.DECIMAL_PLACES),
         i.source, self.timestamp
       )
       for i in matrixrules()
       if (i[0].name, i[1].priority) not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update setuprule \
       set fromsetup=%s, tosetup=%s, duration=%s, cost=%s, source=%s, lastmodified=%s \
       where setupmatrix_id=%s and priority=%s",
      [
        (
          i[1].fromsetup, i[1].tosetup, i[1].duration, round(i[1].cost, settings.DECIMAL_PLACES),
          i.source, self.timestamp, i[0].name, i[1].priority
        )
        for i[1] in matrixrules()
        if (i[0].name, i[1].priority) in primary_keys and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported setup matrix rules in %.2f seconds' % (time() - starttime))


  def exportItems(self, cursor):
    print("Exporting items...")
    starttime = time()
    cursor.execute("SELECT name FROM item")
    primary_keys = set([ i[0] for i in cursor.fetchall() ])
    cursor.executemany(
      "insert into item \
      (name,description,operation_id,price,category,subcategory,source,lastmodified) \
      values(%s,%s,%s,%s,%s,%s,%s,%s)",
      [
        (
          i.name, i.description, i.operation and i.operation.name or None,
          round(i.price, settings.DECIMAL_PLACES), i.category, i.subcategory,
          i.source, self.timestamp
        )
        for i in frepple.items()
        if i.name not in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update item \
       set description=%s, operation_id=%s, price=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s \
       where name=%s",
      [
        (
          i.description, i.operation and i.operation.name or None,
          round(i.price, settings.DECIMAL_PLACES), i.category, i.subcategory,
          i.source, self.timestamp, i.name
        )
        for i in frepple.items()
        if i.name in primary_keys and (not self.source or self.source == i.source)
      ])
    cursor.executemany(
      "update item set owner_id=%s where name=%s",
      [
        (i.owner.name, i.name)
        for i in frepple.items()
        if i.owner and (not self.source or self.source == i.source)
      ])
    transaction.commit(using=self.database)
    print('Exported items in %.2f seconds' % (time() - starttime))


  def exportParameters(self, cursor):
    if self.source:
      # Only complete export should save the current date
      return
    print("Exporting parameters...")
    starttime = time()
    # Update current date if the parameter already exists
    # If it doesn't exist, we want to continue using the system clock for the next run.
    cursor.execute(
      "UPDATE common_parameter SET value=%s, lastmodified=%s WHERE name='currentdate'",
      (frepple.settings.current.strftime("%Y-%m-%d %H:%M:%S"), self.timestamp)
      )
    transaction.commit(using=self.database)
    print('Exported parameters in %.2f seconds' % (time() - starttime))


  def run(self):
    '''
    This function exports the data from the frePPLe memory into the database.
    '''
    transaction.set_autocommit(False, using=self.database)
    try:
      # Make sure the debug flag is not set!
      # When it is set, the django database wrapper collects a list of all sql
      # statements executed and their timings. This consumes plenty of memory
      # and cpu time.
      settings.DEBUG = False
      self.timestamp = str(datetime.datetime.now())

      # Create a database connection
      cursor = connections[self.database].cursor()
      if settings.DATABASES[self.database]['ENGINE'] == 'django.db.backends.sqlite3':
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA synchronous = OFF')
        cursor.execute('PRAGMA cache_size = 8000')
      elif settings.DATABASES[self.database]['ENGINE'] == 'oracle':
        cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")

      if settings.DATABASES[self.database]['ENGINE'] == 'django.db.backends.sqlite3':
        # OPTION 1: Sequential export of each entity
        # For SQLite this is required since a writer blocks the database file.
        # For other databases the parallel export normally gives a better
        # performance, but you could still choose a sequential export.
        try:
          self.exportParameters(cursor)
          self.exportCalendars(cursor)
          self.exportCalendarBuckets(cursor)
          self.exportLocations(cursor)
          self.exportOperations(cursor)
          self.exportSubOperations(cursor)
          self.exportOperationPlans(cursor)
          self.exportItems(cursor)
          self.exportBuffers(cursor)
          self.exportFlows(cursor)
          self.exportSetupMatrices(cursor)
          self.exportSetupMatricesRules(cursor)
          self.exportResources(cursor)
          self.exportSkills(cursor)
          self.exportResourceSkills(cursor)
          self.exportLoads(cursor)
          self.exportCustomers(cursor)
          self.exportSuppliers(cursor)
          self.exportDemands(cursor)
        except:
          traceback.print_exc()

      else:
        # OPTION 2: Parallel export of entities in groups.
        # The groups are running in separate threads, and all functions in a group
        # are run in sequence.
        try:
          self.exportCalendars(cursor)
          self.exportLocations(cursor)
          self.exportOperations(cursor)
          self.exportItems(cursor)
          tasks = (
            DatabaseTask(self, self.exportCalendarBuckets, self.exportSubOperations, self.exportOperationPlans, self.exportParameters),
            DatabaseTask(self, self.exportBuffers, self.exportFlows, exportSuppliers),
            DatabaseTask(self, self.exportSetupMatrices, self.exportSetupMatricesRules, self.exportResources, self.exportSkills, self.exportResourceSkills, self.exportLoads),
            DatabaseTask(self, self.exportCustomers, self.exportDemands),
            )
          # Start all threads
          for i in tasks:
            i.start()
          # Wait for all threads to finish
          for i in tasks:
            i.join()
        except Exception as e:
          print("Error exporting static model:", e)

      # Cleanup unused records
      if self.source:
        cursor.execute("delete from flow where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from buffer where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from demand where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from item where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from operationplan where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from suboperation where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from resourceload where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from resourceskill where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from operation where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from suboperation where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from resource where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from location where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from calendar where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from skill where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from setuprule where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from setupmatrix where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from customer where source = %s and lastmodified <> %s", (self.source, self.timestamp))

      # Analyze
      if settings.DATABASES[self.database]['ENGINE'] == 'django.db.backends.sqlite3':
        print("Analyzing database tables...")
        cursor.execute("analyze")

      # Close the database connection
      cursor.close()
      transaction.commit(using=self.database)
    finally:
      transaction.rollback(using=self.database)
      transaction.set_autocommit(True, using=self.database)


class DatabaseTask(Thread):
  '''
  An auxiliary class that allows us to run a function with its own
  database connection in its own thread.
  '''
  def __init__(self, xprt, *f):
    super(DatabaseTask, self).__init__()
    self.export = xprt
    self.functions = f

  def run(self):
    transaction.set_autocommit(False, using=self.export.database)
    try:
      # Create a database connection
      cursor = connections[self.export.database].cursor()
      if settings.DATABASES[self.export.database]['ENGINE'] == 'django.db.backends.sqlite3':
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA synchronous = OFF')
        cursor.execute('PRAGMA cache_size = 8000')
      elif settings.DATABASES[self.export.database]['ENGINE'] == 'django.db.backends.oracle':
        cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")

      # Run the functions sequentially
      for f in self.functions:
        try:
          f(cursor)
        except:
          traceback.print_exc()

      # Close the connection
      cursor.close()
      transaction.commit(using=self.export.database)
    finally:
      transaction.rollback(using=self.export.database)
      transaction.set_autocommit(True, using=self.export.database)
