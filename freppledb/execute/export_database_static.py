#
# Copyright (C) 2011-2013 by frePPLe bvba
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
    with transaction.atomic(using=self.database, savepoint=False):
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
      print('Exported locations in %.2f seconds' % (time() - starttime))


  def exportCalendars(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
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
            i.name, round(i.default, 8), i.source,
            self.timestamp
          )
          for i in frepple.calendars()
          if i.name not in primary_keys and not i.hidden and (not self.source or self.source == i.source and not i.source == 'common_bucket')
        ])
      cursor.executemany(
        "update calendar \
         set defaultvalue=%s, source=%s, lastmodified=%s \
         where name=%s",
        [
          (
            round(i.default, 8), i.source, self.timestamp,
            i.name
          )
          for i in frepple.calendars()
          if i.name in primary_keys and not i.hidden and (not self.source or self.source == i.source and not i.source == 'common_bucket')
        ])
      print('Exported calendars in %.2f seconds' % (time() - starttime))


  def exportCalendarBuckets(self, cursor):

    def buckets():
      cursor.execute("SELECT max(id) FROM calendarbucket")
      cnt = cursor.fetchone()[0] or 1
      for c in frepple.calendars():
        if c.hidden or c.source == 'common_bucket':
          continue
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

    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting calendar buckets...")
      starttime = time()
      if self.source:
        cursor.execute("delete from calendarbucket where source = %s", [self.source])
      else:
        cursor.execute("delete from calendarbucket")

      cursor.executemany(
        "insert into calendarbucket \
        (calendar_id,startdate,enddate,id,priority,value, \
        sunday,monday,tuesday,wednesday,thursday,friday,saturday, \
        starttime,endtime,source,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (
            i[0].calendar.name, str(i[0].start), str(i[0].end), i[1], i[0].priority,
            round(i[0].value, 8),
            (i[0].days & 1) and True or False, (i[0].days & 2) and True or False,
            (i[0].days & 4) and True or False, (i[0].days & 8) and True or False,
            (i[0].days & 16) and True or False, (i[0].days & 32) and True or False,
            (i[0].days & 64) and True or False,
            int_to_time(i[0].starttime), int_to_time(i[0].endtime - 1),
            i[0].source, self.timestamp
          )
          for i in buckets()
        ])
      print('Exported calendar buckets in %.2f seconds' % (time() - starttime))


  def exportOperations(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting operations...")
      starttime = time()
      default_start = datetime.datetime(1971, 1, 1)
      default_end = datetime.datetime(2030, 12, 31)
      cursor.execute("SELECT name FROM operation")
      primary_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into operation \
        (name,fence,posttime,sizeminimum,sizemultiple,sizemaximum,type, \
        duration,duration_per,location_id,cost,search,description,category, \
        subcategory,source,item_id,priority,effective_start,effective_end, \
        lastmodified) \
        values(%s,%s * interval '1 second',%s * interval '1 second',%s,%s, \
        %s,%s,%s * interval '1 second',%s * interval '1 second',%s,%s,%s, \
        %s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (
            i.name, i.fence, i.posttime, round(i.size_minimum, 8),
            round(i.size_multiple, 8),
            i.size_maximum < 9999999999999 and round(i.size_maximum, 8) or None,
            i.__class__.__name__[10:],
            isinstance(i, (frepple.operation_fixed_time, frepple.operation_time_per)) and i.duration or None,
            isinstance(i, frepple.operation_time_per) and i.duration_per or None,
            i.location and i.location.name or None, round(i.cost, 8),
            isinstance(i, frepple.operation_alternate) and i.search or None,
            i.description, i.category, i.subcategory, i.source,
            i.item.name if i.item else None, i.priority if i.priority != 1 else None,
            i.effective_start if i.effective_start != default_start else None,
            i.effective_end if i.effective_end != default_end else None,
            self.timestamp
          )
          for i in frepple.operations()
          if i.name not in primary_keys and not i.hidden and not isinstance(i, frepple.operation_itemsupplier) and i.name != 'setup operation' and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update operation \
        set fence=%s * interval '1 second', posttime=%s* interval '1 second', \
        sizeminimum=%s, sizemultiple=%s, sizemaximum=%s, type=%s, \
        duration=%s * interval '1 second', duration_per=%s * interval '1 second', \
        location_id=%s, cost=%s, search=%s, description=%s, \
        category=%s, subcategory=%s, source=%s, lastmodified=%s, \
        item_id=%s, priority=%s, effective_start=%s, effective_end=%s \
        where name=%s",
        [
          (
            i.fence, i.posttime, round(i.size_minimum, 8),
            round(i.size_multiple, 8),
            i.size_maximum < 9999999999999 and round(i.size_maximum, 8) or None,
            i.__class__.__name__[10:],
            isinstance(i, (frepple.operation_fixed_time, frepple.operation_time_per)) and i.duration or None,
            isinstance(i, frepple.operation_time_per) and i.duration_per or None,
            i.location and i.location.name or None, round(i.cost, 8),
            isinstance(i, frepple.operation_alternate) and i.search or None,
            i.description, i.category, i.subcategory, i.source, self.timestamp,
            i.item.name if i.item else None, i.priority,
            i.effective_start if i.effective_start != default_start else None,
            i.effective_end if i.effective_end != default_end else None,
            i.name
          )
          for i in frepple.operations()
          if i.name in primary_keys and not i.hidden and not isinstance(i, frepple.operation_itemsupplier) and i.name != 'setup operation' and (not self.source or self.source == i.source)
        ])
      print('Exported operations in %.2f seconds' % (time() - starttime))


  def exportSubOperations(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting suboperations...")
      starttime = time()
      cursor.execute("SELECT operation_id, suboperation_id FROM suboperation")
      primary_keys = set([ i for i in cursor.fetchall() ])

      def subops():
        for i in frepple.operations():
          if not i.hidden and isinstance(i, (frepple.operation_split, frepple.operation_routing, frepple.operation_alternate)):
            for j in i.suboperations:
              yield j

      cursor.executemany(
        "insert into suboperation \
        (operation_id,suboperation_id,priority,effective_start,effective_end,source,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s)",
        [
          (i.owner.name, i.operation.name, i.priority, i.effective_start, i.effective_end, i.source, self.timestamp)
          for i in subops()
          if (i.owner.name, i.operation.name) not in primary_keys and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update suboperation \
         set priority=%s, effective_start=%s, effective_end=%s, source=%s, lastmodified=%s \
         where operation_id=%s and suboperation_id=%s",
        [
          (i.priority, i.effective_start, i.effective_end, i.source, self.timestamp, i.owner.name, i.operation.name)
          for i in subops()
          if (i.owner.name, i.operation.name) in primary_keys and (not self.source or self.source == i.source)
        ])
      print('Exported suboperations in %.2f seconds' % (time() - starttime))


  def exportOperationMaterials(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      default_start = datetime.datetime(1971, 1, 1)
      default_end = datetime.datetime(2030, 12, 31)

      print("Exporting operation materials...")
      starttime = time()
      cursor.execute("SELECT operation_id, item_id, effective_start FROM operationmaterial")
      primary_keys = set([ (i[0], i[1], i[2] if i[2] else default_start) for i in cursor.fetchall() ])

      def flows(source):
        for o in frepple.operations():
          if o.hidden:
            continue
          for i in o.flows:
            if i.hidden:
              continue
            if not source or source == i.source:
              yield i
              
      cursor.executemany(
        "insert into operationmaterial \
        (operation_id,item_id,quantity,type,effective_start,effective_end,\
        name,priority,search,source,transferbatch,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (
            i.operation.name, i.buffer.item.name, round(i.quantity, 8),
            i.type[5:],
            i.effective_start if i.effective_start != default_start else None,
            i.effective_end if i.effective_end != default_end else None, i.name,
            i.priority, i.search != 'PRIORITY' and i.search or None, i.source,
            round(i.transferbatch, 8) if isinstance(i, frepple.flow_transfer_batch) else None,
            self.timestamp
          )
          for i in flows(self.source)
          if (i.operation.name, i.item.name, i.effective_start) not in primary_keys
        ])
      cursor.executemany(
        "update operationmaterial \
        set quantity=%s, type=%s, effective_end=%s, name=%s, \
        priority=%s, search=%s, source=%s, transferbatch=%s, lastmodified=%s \
        where operation_id=%s and item_id=%s and effective_start=%s",
        [
          (
            round(i.quantity, 8),
            i.type[5:], i.effective_end if i.effective_end != default_end else None,
            i.name, i.priority, i.search != 'PRIORITY' and i.search or None, i.source,
            round(i.transferbatch, 8) if isinstance(i, frepple.flow_transfer_batch) else None,
            self.timestamp, i.operation.name, i.item.name, i.effective_start
          )
          for i in flows(self.source)
          if (i.operation.name, i.item.name, i.effective_start) in primary_keys \
            and i.effective_start != default_start
        ])
      cursor.executemany(
        "update operationmaterial \
        set quantity=%s, type=%s, effective_end=%s, name=%s, \
        priority=%s, search=%s, source=%s, transferbatch=%s, lastmodified=%s \
        where operation_id=%s and item_id=%s and effective_start is null",
        [
          (
            round(i.quantity, 8),
            i.type[5:], i.effective_end if i.effective_end != default_end else None,
            i.name, i.priority, i.search != 'PRIORITY' and i.search or None, i.source,
            round(i.transferbatch, 8) if isinstance(i, frepple.flow_transfer_batch) else None,
            self.timestamp, i.operation.name, i.buffer.item.name
          )
          for i in flows(self.source)
          if (i.operation.name, i.item.name, i.effective_start) in primary_keys \
            and i.effective_start == default_start
        ])
      print('Exported operation materials in %.2f seconds' % (time() - starttime))


  def exportOperationResources(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting operation resources...")
      starttime = time()
      cursor.execute("SELECT operation_id, resource_id, effective_start FROM operationresource")
      primary_keys = set([ i for i in cursor.fetchall() ])

      def loads(source):
        for o in frepple.operations():
          if o.hidden:
            continue
          for i in o.loads:
            if i.hidden:
              continue
            if not source or source == i.source:
              yield i

      cursor.executemany(
        "insert into operationresource \
        (operation_id,resource_id,quantity,setup,effective_start, \
        effective_end,name,priority,search,source,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (
            i.operation.name, i.resource.name, round(i.quantity, 8),
            i.setup, str(i.effective_start), i.effective_end,
            i.name, i.priority, i.search != 'PRIORITY' and i.search or None,
            i.source, self.timestamp
          )
          for i in loads(self.source)
          if (i.operation.name, i.resource.name, i.effective_start) not in primary_keys
        ])
      cursor.executemany(
        "update operationresource \
        set quantity=%s, setup=%s, effective_start=%s, effective_end=%s, \
        name=%s, priority=%s, search=%s, source=%s, lastmodified=%s \
        where operation_id=%s and resource_id=%s",
        [
          (
            round(i.quantity, 8),
            i.setup, str(i.effective_start), str(i.effective_end),
            i.name, i.priority, i.search != 'PRIORITY' and i.search or None,
            i.source, self.timestamp, i.operation.name, i.resource.name,
          )
          for i in loads(self.source)
          if (i.operation.name, i.resource.name, i.effective_start) in primary_keys
        ])
      print('Exported operation resources in %.2f seconds' % (time() - starttime))


  def exportBuffers(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting buffers...")
      starttime = time()
      cursor.execute("SELECT name FROM buffer")
      primary_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into buffer \
        (name,description,location_id,item_id,onhand,minimum,minimum_calendar_id, \
        type,min_interval,category,subcategory,source,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s * interval '1 second',%s,%s,%s,%s)",
        [
          (
            i.name, i.description, i.location and i.location.name or None,
            i.item and i.item.name or None,
            round(i.onhand, 8), round(i.minimum, 8),
            i.minimum_calendar and i.minimum_calendar.name or None,
            i.__class__.__name__[7:], i.mininterval,
            i.category, i.subcategory, i.source, self.timestamp
          )
          for i in frepple.buffers()
          if i.name not in primary_keys and not i.hidden and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update buffer \
         set description=%s, location_id=%s, item_id=%s, onhand=%s, \
         minimum=%s, minimum_calendar_id=%s, type=%s, \
         min_interval=%s * interval '1 second', category=%s, \
         subcategory=%s, source=%s, lastmodified=%s \
         where name=%s",
        [
          (
            i.description, i.location and i.location.name or None, i.item and i.item.name or None,
            round(i.onhand, 8), round(i.minimum, 8),
            i.minimum_calendar and i.minimum_calendar.name or None,
            i.__class__.__name__[7:],
            (i.mininterval!=-1) and i.mininterval or None,
            i.category, i.subcategory, i.source, self.timestamp, i.name
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
      print('Exported buffers in %.2f seconds' % (time() - starttime))


  def exportCustomers(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
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
      print('Exported customers in %.2f seconds' % (time() - starttime))


  def exportSuppliers(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
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
      print('Exported suppliers in %.2f seconds' % (time() - starttime))


  def exportItemSuppliers(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):

      def itemsuppliers():
        for o in frepple.suppliers():
          for i in o.itemsuppliers:
            if not i.hidden:
              yield i

      print("Exporting item suppliers...")
      starttime = time()
      default_start = datetime.datetime(1971, 1, 1)
      default_end = datetime.datetime(2030, 12, 31)
      cursor.execute("SELECT supplier_id, item_id, location_id, effective_start FROM itemsupplier")
      primary_keys = set([ (i[0], i[1], i[2], i[3] if i[3] else default_start) for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into itemsupplier \
        (supplier_id,item_id,location_id,leadtime,sizeminimum,sizemultiple, \
         cost,priority,effective_start,effective_end,resource_id,resource_qty,source,lastmodified) \
        values(%s,%s,%s,%s * interval '1 second',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (i.supplier.name, i.item.name, i.location.name if i.location else None,
           i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_start if i.effective_start != default_start else None,
           i.effective_end if i.effective_end != default_end else None,
           i.resource.name if i.resource else None, i.resource_qty,
           i.source, self.timestamp)
          for i in itemsuppliers()
          if (i.supplier.name, i.item.name, i.location.name if i.location else None, i.effective_start) not in primary_keys and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update itemsupplier \
         set leadtime=%s * interval '1 second', sizeminimum=%s, sizemultiple=%s, \
         cost=%s, priority=%s, effective_end=%s, \
         source=%s, lastmodified=%s \
         where supplier_id=%s and item_id=%s and location_id=%s and effective_start=%s",
        [
          (i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp,
           i.supplier.name, i.item.name, i.location.name if i.location else None,
           i.effective_start)
          for i in itemsuppliers()
          if (i.supplier.name, i.item.name, i.location.name if i.location else None, i.effective_start) in primary_keys \
            and i.location is not None \
            and i.effective_start != default_start \
            and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update itemsupplier \
         set leadtime=%s * interval '1 second', sizeminimum=%s, sizemultiple=%s, \
         cost=%s, priority=%s, effective_end=%s, \
         source=%s, lastmodified=%s \
         where supplier_id=%s and item_id=%s and location_id=%s and effective_start is null",
        [
          (i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp,
           i.supplier.name, i.item.name, i.location.name if i.location else None)
          for i in itemsuppliers()
          if (i.supplier.name, i.item.name, i.location.name if i.location else None, i.effective_start) in primary_keys \
            and i.location is not None \
            and i.effective_start == default_start \
            and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update itemsupplier \
         set leadtime=%s * interval '1 second', sizeminimum=%s, sizemultiple=%s, \
         cost=%s, priority=%s, effective_end=%s, \
         source=%s, lastmodified=%s \
         where supplier_id=%s and item_id=%s and location_id is null and effective_start=%s",
        [
          (i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp,
           i.supplier.name, i.item.name, i.effective_start)
          for i in itemsuppliers()
          if (i.supplier.name, i.item.name, i.location.name if i.location else None, i.effective_start) in primary_keys \
            and i.location is None \
            and i.effective_start != default_start \
            and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update itemsupplier \
         set leadtime=%s * interval '1 second', sizeminimum=%s, sizemultiple=%s, \
         cost=%s, priority=%s, effective_end=%s, \
         source=%s, lastmodified=%s \
         where supplier_id=%s and item_id=%s and location_id is null and effective_start is null",
        [
          (i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp,
           i.supplier.name, i.item.name)
          for i in itemsuppliers()
          if (i.supplier.name, i.item.name, None, i.effective_start) in primary_keys \
            and i.location is None \
            and i.effective_start == default_start \
            and (not self.source or self.source == i.source)
        ])
      print('Exported item suppliers in %.2f seconds' % (time() - starttime))


  def exportItemDistributions(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):

      def itemdistributions():
        for o in frepple.items():
          for i in o.itemdistributions:
            if not i.hidden:
              yield i

      print("Exporting item distributions...")
      starttime = time()
      default_start = datetime.datetime(1971, 1, 1)
      default_end = datetime.datetime(2030, 12, 31)
      cursor.execute("SELECT origin_id, item_id, location_id, effective_start FROM itemdistribution")
      primary_keys = set([ (i[0], i[1], i[2], i[3] if i[3] else default_start) for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into itemdistribution \
        (origin_id,item_id,location_id,leadtime,sizeminimum,sizemultiple, \
         cost,priority,effective_start,effective_end,source,lastmodified) \
        values(%s,%s,%s,%s * interval '1 second',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (i.origin.name, i.item.name, i.destination.name if i.destination else None,
           i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_start if i.effective_start != default_start else None,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp)
          for i in itemdistributions()
          if (i.origin.name, i.item.name, i.destination.name if i.destination else None, i.effective_start) not in primary_keys and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update itemdistribution \
         set leadtime=%s * interval '1 second', sizeminimum=%s, \
         sizemultiple=%s, cost=%s, priority=%s, effective_end=%s, \
         source=%s, lastmodified=%s \
         where origin_id=%s and item_id=%s and location_id=%s and effective_start=%s",
        [
          (i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp, i.origin.name, i.item.name,
           i.destination.name if i.destination else None,
           i.effective_start)
          for i in itemdistributions()
          if (i.origin.name, i.item.name, i.destination.name if i.destination else None, i.effective_start) in primary_keys and i.effective_start != default_start and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update itemdistribution \
         set leadtime=%s * interval '1 second', sizeminimum=%s, sizemultiple=%s, \
         cost=%s, priority=%s, effective_end=%s, \
         source=%s, lastmodified=%s \
         where origin_id=%s and item_id=%s and location_id=%s and effective_start is null",
        [
          (i.leadtime, i.size_minimum, i.size_multiple, i.cost, i.priority,
           i.effective_end if i.effective_end != default_end else None,
           i.source, self.timestamp, i.origin.name, i.item.name,
           i.destination.name if i.destination else None)
          for i in itemdistributions()
          if (i.origin.name, i.item.name, i.destination.name if i.destination else None, i.effective_start) in primary_keys and i.effective_start == default_start and (not self.source or self.source == i.source)
        ])
      print('Exported item distributions in %.2f seconds' % (time() - starttime))


  def exportDemands(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting demands...")
      starttime = time()
      cursor.execute("SELECT name FROM demand")
      primary_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into demand \
        (name,due,quantity,priority,item_id,location_id,operation_id,customer_id, \
         minshipment,maxlateness,category,subcategory,source,lastmodified,status) \
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s * interval '1 second',%s,%s,%s,%s,%s)",
        [
          (
            i.name, str(i.due), round(i.quantity, 8), i.priority, i.item.name,
            i.location.name if i.location else None, i.operation.name if i.operation and not i.operation.hidden else None,
            i.customer.name if i.customer else None,
            round(i.minshipment, 8), i.maxlateness,
            i.category, i.subcategory, i.source, self.timestamp, i.status
          )
          for i in frepple.demands()
          if i.name not in primary_keys and isinstance(i, frepple.demand_default) and not i.hidden and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update demand \
         set due=%s, quantity=%s, priority=%s, item_id=%s, location_id=%s, \
         operation_id=%s, customer_id=%s, minshipment=%s, maxlateness=%s * interval '1 second', \
         category=%s, subcategory=%s, source=%s, lastmodified=%s, status=%s \
         where name=%s",
        [
          (
            str(i.due), round(i.quantity, 8), i.priority,
            i.item.name, i.location.name if i.location else None,
            i.operation.name if i.operation and not i.operation.hidden else None,
            i.customer.name if i.customer else None,
            round(i.minshipment, 8),
            i.maxlateness,
            i.category, i.subcategory, i.source, self.timestamp,
            i.status, i.name
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
      print('Exported demands in %.2f seconds' % (time() - starttime))


  def exportResources(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting resources...")
      starttime = time()
      cursor.execute("select name from resource")
      primary_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into resource \
        (name,description,maximum,maximum_calendar_id,location_id,type,cost, \
         maxearly,setup,setupmatrix_id,category,subcategory,efficiency, \
         available_id,source,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s,%s * interval '1 second',%s,%s,%s,%s,%s,%s,%s,%s)",
        [
          (
            i.name, i.description, i.maximum,
            i.maximum_calendar.name if i.maximum_calendar else None,
            i.location and i.location.name or None, i.__class__.__name__[9:],
            round(i.cost, 8), i.maxearly,
            i.setup, i.setupmatrix and i.setupmatrix.name or None,
            i.category, i.subcategory, i.efficiency,
            i.available.name if i.available else None,
            i.source, self.timestamp
          )
          for i in frepple.resources()
          if i.name not in primary_keys and not i.hidden and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update resource \
        set description=%s, maximum=%s, maximum_calendar_id=%s, location_id=%s, \
        type=%s, cost=%s, maxearly=%s * interval '1 second', setup=%s, setupmatrix_id=%s, \
        category=%s, subcategory=%s, efficiency=%s, available_id=%s, \
        source=%s, lastmodified=%s \
        where name=%s",
        [
          (
            i.description, i.maximum,
            i.maximum_calendar and i.maximum_calendar.name or None,
            i.location and i.location.name or None, i.__class__.__name__[9:],
            round(i.cost, 8), round(i.maxearly, 8),
            i.setup, i.setupmatrix and i.setupmatrix.name or None,
            i.category, i.subcategory, round(i.efficiency, 8),
            i.available.name if i.available else None,
            i.source, self.timestamp, i.name
          )
          for i in frepple.resources()
          if i.name in primary_keys and not i.hidden and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update resource set owner_id=%s where name=%s",
        [
          (i.owner.name, i.name)
          for i in frepple.resources()
          if i.owner and not i.hidden and (not self.source or self.source == i.source)
        ])
      print('Exported resources in %.2f seconds' % (time() - starttime))


  def exportSkills(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting skills...")
      starttime = time()
      cursor.execute("SELECT name FROM skill")
      primary_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into skill (name,source,lastmodified) values(%s,%s,%s)",
        [
          ( i.name, i.source, self.timestamp )
          for i in frepple.skills()
          if i.name not in primary_keys and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update skill set source=%s, lastmodified=%s where name=%s",
        [
          (i.source, self.timestamp, i.name)
          for i in frepple.skills()
          if i.name in primary_keys and (not self.source or self.source == i.source)
        ])
      print('Exported skills in %.2f seconds' % (time() - starttime))


  def exportResourceSkills(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting resource skills...")
      starttime = time()
      cursor.execute("SELECT resource_id, skill_id FROM resourceskill")  # todo resource&skill are not necesarily unique
      primary_keys = set([ i for i in cursor.fetchall() ])

      def res_skills():
        for s in frepple.skills():
          for r in s.resourceskills:
            yield (r.effective_start, r.effective_end, r.priority, r.source, self.timestamp, r.resource.name, s.name)

      cursor.executemany(
        "insert into resourceskill \
        (effective_start,effective_end,priority,source,lastmodified,resource_id,skill_id) \
        values(%s,%s,%s,%s,%s,%s,%s)",
        [
          i for i in res_skills()
          if (i[5],i[6]) not in primary_keys and (not self.source or self.source == i[3])
        ])
      cursor.executemany(
        "update resourceskill \
        set effective_start=%s, effective_end=%s, priority=%s, source=%s, lastmodified=%s \
        where resource_id=%s and skill_id=%s",
        [
          i for i in res_skills()
          if (i[5],i[6]) in primary_keys and (not self.source or self.source == i[3])
        ])
      print('Exported resource skills in %.2f seconds' % (time() - starttime))


  def exportSetupMatrices(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
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
      print('Exported setupmatrices in %.2f seconds' % (time() - starttime))


  def exportSetupMatricesRules(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
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
        values(%s,%s,%s,%s,%s * interval '1 second',%s,%s,%s)",
        [
         (
           i[0].name, i[1].priority, i[1].fromsetup, i[1].tosetup, i[1].duration,
           round(i[1].cost, 8),
           i.source, self.timestamp
         )
         for i in matrixrules()
         if (i[0].name, i[1].priority) not in primary_keys and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
         "update setuprule \
         set fromsetup=%s, tosetup=%s, duration=%s * interval '1 second', \
         cost=%s, source=%s, lastmodified=%s \
         where setupmatrix_id=%s and priority=%s",
        [
          (
            i[1].fromsetup, i[1].tosetup, i[1].duration, round(i[1].cost, 8),
            i.source, self.timestamp, i[0].name, i[1].priority
          )
          for i[1] in matrixrules()
          if (i[0].name, i[1].priority) in primary_keys and (not self.source or self.source == i.source)
        ])
      print('Exported setup matrix rules in %.2f seconds' % (time() - starttime))


  def exportItems(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      print("Exporting items...")
      starttime = time()
      cursor.execute("SELECT name FROM item")
      primary_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into item \
        (name,description,cost,category,subcategory,source,lastmodified) \
        values(%s,%s,%s,%s,%s,%s,%s)",
        [
          (
            i.name, i.description, round(i.cost, 8), i.category,
            i.subcategory, i.source, self.timestamp
          )
          for i in frepple.items()
          if i.name not in primary_keys and (not self.source or self.source == i.source)
        ])
      cursor.executemany(
        "update item \
         set description=%s, cost=%s, category=%s, subcategory=%s, source=%s, lastmodified=%s \
         where name=%s",
        [
          (
            i.description, round(i.cost, 8), i.category, i.subcategory,
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
      print('Exported items in %.2f seconds' % (time() - starttime))


  def exportParameters(self, cursor):
    with transaction.atomic(using=self.database, savepoint=False):
      if self.source:
        # Only complete export should save the current date
        return
      print("Exporting parameters...")
      starttime = time()
      # Update current date if the parameter already exists
      # If it doesn't exist, we want to continue using the system clock for the next run.
      cursor.execute(
        "update common_parameter set value=%s, lastmodified=%s where name='currentdate'",
        (frepple.settings.current.strftime("%Y-%m-%d %H:%M:%S"), self.timestamp)
        )
      print('Exported parameters in %.2f seconds' % (time() - starttime))


  def run(self):
    '''
    This function exports the data from the frePPLe memory into the database.
    '''
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp = settings.DEBUG
    settings.DEBUG = False
    self.timestamp = str(datetime.datetime.now())

    try:
      # Create a database connection
      cursor = connections[self.database].cursor()

      if False:
        # OPTION 1: Sequential export of each entity
        # The parallel export normally gives a better performance, but
        # you could still choose a sequential export.
        self.exportParameters(cursor)
        self.exportCalendars(cursor)
        self.exportCalendarBuckets(cursor)
        self.exportLocations(cursor)
        self.exportItems(cursor)
        self.exportOperations(cursor)
        self.exportSubOperations(cursor)
        self.exportOperationPlans(cursor)
        self.exportBuffers(cursor)
        self.exportOperationMaterials(cursor)
        self.exportSetupMatrices(cursor)
        self.exportSetupMatricesRules(cursor)
        self.exportResources(cursor)
        self.exportSkills(cursor)
        self.exportResourceSkills(cursor)
        self.exportOperationResources(cursor)
        self.exportCustomers(cursor)
        self.exportSuppliers(cursor)
        self.exportItemSuppliers(cursor)
        self.exportItemDistributions(cursor),
        self.exportDemands(cursor)

      else:
        # OPTION 2: Parallel export of entities in groups.
        # The groups are running in separate threads, and all functions in a group
        # are run in sequence.
        self.exportCalendars(cursor)
        self.exportLocations(cursor)
        self.exportItems(cursor)
        self.exportOperations(cursor)
        self.exportSetupMatrices(cursor)
        self.exportResources(cursor)
        tasks = (
          DatabaseTask(self, self.exportCalendarBuckets, self.exportSubOperations, self.exportParameters),
          DatabaseTask(self, self.exportBuffers, self.exportOperationMaterials, self.exportSuppliers, self.exportItemSuppliers, self.exportItemDistributions),
          DatabaseTask(self, self.exportSetupMatricesRules, self.exportSkills, self.exportResourceSkills, self.exportOperationResources),
          DatabaseTask(self, self.exportCustomers, self.exportDemands),
          )
        # Start all threads
        for i in tasks:
          i.start()
        # Wait for all threads to finish
        for i in tasks:
          i.join()

      # Cleanup unused records
      if self.source:
        cursor.execute("delete from operationmaterial where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from buffer where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute('''
          delete from operationplanmaterial
          where operationplan_id in (select id from operationplan
                inner join demand on operationplan.demand_id = demand.name
                where demand.source = %s and demand.lastmodified <> %s
                )''', (self.source, self.timestamp))
        cursor.execute('''
          delete from operationplanresource
          where operationplan_id in (select id from operationplan
                inner join demand on operationplan.demand_id = demand.name
                where demand.source = %s and demand.lastmodified <> %s
                )''', (self.source, self.timestamp))
        cursor.execute("delete from operationplan where demand_id in (select name from demand where source = %s and lastmodified <> %s)", (self.source, self.timestamp))
        cursor.execute("delete from demand where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from itemsupplier where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from itemdistribution where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from item where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute('''
          delete from operationplanmaterial
          where operationplan_id in (
            select operationplan.id
            from operationplan
            where operationplan.source = %s and operationplan.lastmodified <> %s
            )
          ''', (self.source, self.timestamp))
        cursor.execute('''
          delete from operationplanresource
          where operationplan_id in (
            select operationplan.id
            from operationplan
            where operationplan.source = %s and operationplan.lastmodified <> %s
            )
          ''', (self.source, self.timestamp))
        cursor.execute("delete from operationplan where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from suboperation where source = %s and lastmodified <> %s", (self.source, self.timestamp))
        cursor.execute("delete from operationresource where source = %s and lastmodified <> %s", (self.source, self.timestamp))
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
        cursor.execute("delete from supplier where source = %s and lastmodified <> %s", (self.source, self.timestamp))

      # Close the database connection
      cursor.close()

    finally:
      # Restore the previous setting
      settings.DEBUG = tmp


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
    # Create a database connection
    cursor = connections[self.export.database].cursor()

    # Run the functions sequentially
    for f in self.functions:
      try:
        f(cursor)
      except:
        traceback.print_exc()

    # Close the connection
    cursor.close()
