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

r'''
Load information from a database in frePPLe memory.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

It extracts the information fields from the database, and then uses the Python
API of frePPLe to bring the data into the frePPLe C++ core engine.
'''
from datetime import datetime
import os
from time import time

from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.boot import getAttributes
from freppledb.input.models import Resource, Item

import frepple


class loadData(object):

  def __init__(self, database=None, filter=None):
    if database:
      self.database = database
    elif 'FREPPLE_DATABASE' in os.environ:
      self.database = os.environ['FREPPLE_DATABASE']
    else:
      self.database = DEFAULT_DB_ALIAS
    if filter:
      self.filter_and = "and %s " % filter
      self.filter_where = "where %s " % filter
    else:
      self.filter_and = ""
      self.filter_where = ""


  def loadParameter(self):
    print('Importing parameters...')
    self.cursor.execute('''
      SELECT name, value
      FROM common_parameter
      where name in ('currentdate', 'plan.calendar')
      ''')
    default_current_date = True
    for rec in self.cursor.fetchall():
      if rec[0] == 'currentdate':
        try:
          frepple.settings.current = datetime.strptime(rec[1], "%Y-%m-%d %H:%M:%S")
          default_current_date = False
        except:
          pass
      elif rec[0] == 'plan.calendar' and rec[1]:
        frepple.settings.calendar = frepple.calendar(name=rec[1])
        print('Bucketized planning using calendar %s' % rec[1])
    if default_current_date:
      frepple.settings.current = datetime.now().replace(microsecond=0)
    print('Current date: %s' % frepple.settings.current)


  def loadLocations(self):
    print('Importing locations...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, description, owner_id, available_id, category, subcategory, source
      FROM location %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        x = frepple.location(name=i[0], description=i[1], category=i[4], subcategory=i[5], source=i[6])
        if i[2]:
          x.owner = frepple.location(name=i[2])
        if i[3]:
          x.available = frepple.calendar(name=i[3])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d locations in %.2f seconds' % (cnt, time() - starttime))


  def loadCalendars(self):
    print('Importing calendars...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, defaultvalue, source, 0 hidden
      FROM calendar %s
      union
      SELECT
        name, 0, 'common_bucket', 1 hidden
      FROM common_bucket
      order by name asc
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        frepple.calendar(name=i[0], default=i[1], source=i[2], hidden=i[3])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d calendars in %.2f seconds' % (cnt, time() - starttime))


  def loadCalendarBuckets(self):
    print('Importing calendar buckets...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
       SELECT
         calendar_id, startdate, enddate, priority, value,
         sunday, monday, tuesday, wednesday, thursday, friday, saturday,
         starttime, endtime, source
      FROM calendarbucket %s
      ORDER BY calendar_id, startdate desc
      ''' % self.filter_where)
    prevcal = None
    for i in self.cursor.fetchall():
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
          end=i[2],
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
        print("Error:", e)
    print('Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime))


  def loadCustomers(self):
    print('Importing customers...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, description, owner_id, category, subcategory, source
      FROM customer %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        x = frepple.customer(name=i[0], description=i[1], category=i[3], subcategory=i[4], source=i[5])
        if i[2]:
          x.owner = frepple.customer(name=i[2])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d customers in %.2f seconds' % (cnt, time() - starttime))


  def loadSuppliers(self):
    print('Importing suppliers...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, description, owner_id, category, subcategory, source
      FROM supplier %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        x = frepple.supplier(name=i[0], description=i[1], category=i[3], subcategory=i[4], source=i[5])
        if i[2]:
          x.owner = frepple.supplier(name=i[2])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d suppliers in %.2f seconds' % (cnt, time() - starttime))


  def loadOperations(self):
    print('Importing operations...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, fence, posttime, sizeminimum, sizemultiple, sizemaximum,
        type, duration, duration_per, location_id, cost, search, description,
        category, subcategory, source, item_id, priority, effective_start,
        effective_end
      FROM operation %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
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
      except Exception as e:
        print("Error:", e)
    print('Loaded %d operations in %.2f seconds' % (cnt, time() - starttime))


  def loadSuboperations(self):
    print('Importing suboperations...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT operation_id, suboperation_id, priority, effective_start, effective_end,
        (select type
         from operation
         where suboperation.operation_id = operation.name) as type
      FROM suboperation
      WHERE priority >= 0 %s
      ORDER BY operation_id, priority
      ''' % self.filter_and)
    curopername = None
    for i in self.cursor.fetchall():
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
        print("Error:", e)
    print('Loaded %d suboperations in %.2f seconds' % (cnt, time() - starttime))


  def loadItems(self):
    print('Importing items...')
    cnt = 0
    starttime = time()
    attrs = [ f[0] for f in getAttributes(Item) ]
    if attrs:
      attrsql = ', %s' % ', '.join(attrs)
    else:
      attrsql = ''
    self.cursor.execute('''
      SELECT
        name, description, owner_id,
        price, category, subcategory, source %s
      FROM item %s
      ''' % (attrsql, self.filter_where))
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        x = frepple.item(name=i[0], description=i[1], category=i[4], subcategory=i[5], source=i[6])
        if i[2]:
          x.owner = frepple.item(name=i[2])
        if i[3]:
          x.price = i[3]
        idx = 7
        for a in attrs:
          setattr(x, a, i[idx])
          idx += 1
      except Exception as e:
        print("Error:", e)
    print('Loaded %d items in %.2f seconds' % (cnt, time() - starttime))


  def loadItemSuppliers(self):
    print('Importing item suppliers...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        supplier_id, item_id, location_id, sizeminimum, sizemultiple,
        cost, priority, effective_start, effective_end, source, leadtime,
        resource_id, resource_qty, fence
      FROM itemsupplier %s
      ORDER BY supplier_id, item_id, location_id, priority desc
      ''' % self.filter_where)
    cursuppliername = None
    curitemname = None
    for i in self.cursor.fetchall():
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
        if i[6]:
          curitemsupplier.priority = i[6]
        if i[7]:
          curitemsupplier.effective_start = i[7]
        if i[8]:
          curitemsupplier.effective_end = i[8]
        if i[11]:
          curitemsupplier.resource = frepple.resource(name=i[11])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d item suppliers in %.2f seconds' % (cnt, time() - starttime))


  def loadItemDistributions(self):
    print('Importing item distributions...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        origin_id, item_id, location_id, sizeminimum, sizemultiple,
        cost, priority, effective_start, effective_end, source,
        leadtime, resource_id, resource_qty, fence
      FROM itemdistribution %s
      ORDER BY origin_id, item_id, location_id, priority desc
      ''' % self.filter_where)
    curoriginname = None
    curitemname = None
    for i in self.cursor.fetchall():
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
        if i[6]:
          curitemdistribution.priority = i[6]
        if i[7]:
          curitemdistribution.effective_start = i[7]
        if i[8]:
          curitemdistribution.effective_end = i[8]
        if i[11]:
          curitemdistribution.resource = frepple.resource(name=i[11])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d item itemdistributions in %.2f seconds' % (cnt, time() - starttime))


  def loadBuffers(self):
    print('Importing buffers...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT name, description, location_id, item_id, onhand,
        minimum, minimum_calendar_id, type,
        min_interval, category, subcategory, source
      FROM buffer %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      if i[7] == "infinite":
        b = frepple.buffer_infinite(
          name=i[0], description=i[1], location=frepple.location(name=i[2]),
          item=frepple.item(name=i[3]), onhand=i[4],
          category=i[9], subcategory=i[10], source=i[11]
          )
      elif not i[7] or i[7] == "default":
        b = frepple.buffer(
          name=i[0], description=i[1], location=frepple.location(name=i[2]),
          item=frepple.item(name=i[3]), onhand=i[4],
          category=i[9], subcategory=i[10], source=i[11]
          )
        if i[8]:
          b.mininterval = i[8].total_seconds()
      else:
        raise ValueError("Buffer type '%s' not recognized" % i[7])
      if i[11] == 'tool':
        b.tool = True
      if i[5]:
        b.minimum = i[5]
      if i[6]:
        b.minimum_calendar = frepple.calendar(name=i[6])
    print('Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime))


  def loadSetupMatrices(self):
    print('Importing setup matrix rules...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        setupmatrix_id, priority, fromsetup, tosetup, duration, cost, source
      FROM setuprule %s
      ORDER BY setupmatrix_id, priority DESC
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        r = frepple.setupmatrix(name=i[0], source=i[6]).addRule(priority=i[1])
        if i[2]:
          r.fromsetup = i[2]
        if i[3]:
          r.tosetup = i[3]
        if i[4]:
          r.duration = i[4].total_seconds()
        if i[5]:
          r.cost = i[5]
      except Exception as e:
        print("Error:", e)
    print('Loaded %d setup matrix rules in %.2f seconds' % (cnt, time() - starttime))


  def loadResources(self):
    print('Importing resources...')
    cnt = 0
    starttime = time()
    Resource.rebuildHierarchy(database=self.database)
    self.cursor.execute('''
      SELECT
        name, description, maximum, maximum_calendar_id, location_id, type, cost,
        maxearly, setup, setupmatrix_id, category, subcategory, owner_id, source
      FROM %s %s
      ORDER BY lvl ASC, name
      ''' % (connections[self.cursor.db.alias].ops.quote_name('resource'), self.filter_where) )
    for i in self.cursor.fetchall():
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
          if i[3]:
            x.maximum_calendar = frepple.calendar(name=i[3])
          if i[7]:
            x.maxearly = i[7]
        elif not i[5] or i[5] == "default":
          x = frepple.resource_default(
            name=i[0], description=i[1], category=i[10], subcategory=i[11], source=i[13]
            )
          if i[3]:
            x.maximum_calendar = frepple.calendar(name=i[3])
          if i[7]:
            x.maxearly = i[7].total_seconds()
          if i[2]:
            x.maximum = i[2]
        else:
          raise ValueError("Resource type '%s' not recognized" % i[5])
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
      except Exception as e:
        print("Error:", e)
    print('Loaded %d resources in %.2f seconds' % (cnt, time() - starttime))


  def loadResourceSkills(self):
    print('Importing resource skills...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        resource_id, skill_id, effective_start, effective_end, priority, source
      FROM resourceskill %s
      ORDER BY skill_id, priority, resource_id
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
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
        print("Error:", e)
    print('Loaded %d resource skills in %.2f seconds' % (cnt, time() - starttime))


  def loadOperationMaterials(self):
    print('Importing operation materials...')
    cnt = 0
    starttime = time()
    # Note: The sorting of the flows is not really necessary, but helps to make
    # the planning progress consistent across runs and database engines.
    self.cursor.execute('''
      SELECT
        operation_id, item_id, quantity, type, effective_start,
        effective_end, name, priority, search, source
      FROM operationmaterial %s
      ORDER BY operation_id, item_id
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        curflow = frepple.flow(
          operation=frepple.operation(name=i[0]),
          item=frepple.item(name=i[1]),
          quantity=i[2],
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
      except Exception as e:
        print("Error:", e)
    print('Loaded %d operation materials in %.2f seconds' % (cnt, time() - starttime))

    # Check for operations where:
    #  - operation.item is still blank
    #  - they have a single operationmaterial item with quantity > 0
    # If found we update
    starttime = time()
    cnt = 0
    print('Auto-update operation items...')
    for oper in frepple.operations():
      if oper.hidden or oper.item:
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
    print('Auto-update of %s operation items in %.2f seconds' % (cnt, time() - starttime))


  def loadOperationResources(self):
    print('Importing operation resources...')
    cnt = 0
    starttime = time()
    # Note: The sorting of the loads is not really necessary, but helps to make
    # the planning progress consistent across runs and database engines.
    self.cursor.execute('''
      SELECT
        operation_id, resource_id, quantity, effective_start, effective_end, name,
        priority, setup, search, skill_id, source
      FROM operationresource %s
      ORDER BY operation_id, resource_id
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
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
        print("Error:", e)
    print('Loaded %d resource loads in %.2f seconds' % (cnt, time() - starttime))


  def loadOperationPlans(self):   # TODO if we are going to replan anyway, we can skip loading the proposed operationplans
    print('Importing operationplans...')
    if 'supply' in os.environ:
      confirmed_filter = " and operationplan.status = 'confirmed'"
    else:
      confirmed_filter = ""
    cnt_mo = 0
    cnt_po = 0
    cnt_do = 0
    cnt_dlvr = 0
    starttime = time()
    self.cursor.execute('''
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
      ORDER BY operationplan.id ASC
      ''' % (self.filter_and, confirmed_filter))
    for i in self.cursor.fetchall():
      try:
        if i[7] == 'MO':
          cnt_mo += 1
          opplan = frepple.operationplan(
            operation=frepple.operation(name=i[0]), id=i[1],
            quantity=i[2], source=i[6], start=i[3], end=i[4],
            status=i[5], reference=i[13]
            )
        elif i[7] == 'PO':
          cnt_po += 1
          opplan = frepple.operationplan(
            location=frepple.location(name=i[12]), ordertype=i[7],
            id=i[1], reference=i[12],
            item=frepple.item(name=i[11]) if i[11] else None,
            supplier=frepple.supplier(name=i[10]) if i[10] else None,
            quantity=i[2], start=i[3], end=i[4],
            status=i[5], source=i[6]
            )
        elif i[7] == 'DO':
          cnt_do += 1
          opplan = frepple.operationplan(
            location=frepple.location(name=i[9]) if i[9] else None,
            id=i[1], reference=i[12], ordertype=i[7],
            item=frepple.item(name=i[11]) if i[11] else None,
            origin=frepple.location(name=i[8]) if i[8] else None,
            quantity=i[2], start=i[3], end=i[4],
            status=i[5], source=i[6]
            )
        elif i[7] == 'DLVR':
          cnt_dlvr += 1
          opplan = frepple.operationplan(
            location=frepple.location(name=i[12]) if i[12] else None,
            id=i[1], reference=i[12], ordertype=i[7],
            item=frepple.item(name=i[11]) if i[11] else None,
            origin=frepple.location(name=i[8]) if i[8] else None,
            demand=frepple.demand(name=i[14]) if i[14] else None,
            quantity=i[2], start=i[3], end=i[4],
            status=i[5], source=i[6]
            )
          opplan = None
        else:          
          print("Warning: unhandled operationplan type '%s'" % i[7])
          continue
        if i[14] and opplan:
          opplan.demand = frepple.demand(name=i[14])
      except Exception as e:
        print("Error:", e)
    self.cursor.execute('''
      SELECT
        operationplan.operation_id, operationplan.id, operationplan.quantity,
        operationplan.startdate, operationplan.enddate, operationplan.status,
        operationplan.owner_id, operationplan.source, coalesce(dmd.name, null)
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
      ORDER BY operationplan.id ASC
      ''' % (self.filter_and, confirmed_filter))
    for i in self.cursor.fetchall():
      cnt_mo += 1
      opplan = frepple.operationplan(
        operation=frepple.operation(name=i[0]),
        id=i[1], quantity=i[2], source=i[7],
        owner=frepple.operationplan(id=i[6]),
        start=i[3], end=i[4], status=i[5]
        )
      if i[8]:
        opplan.demand = frepple.demand(name=i[8])
    print('Loaded %d manufacturing orders, %d purchase orders, %d distribution orders and %s deliveries in %.2f seconds' % (cnt_mo, cnt_po, cnt_do, cnt_dlvr, time() - starttime))

    # Assure the operationplan ids will be unique.
    # We call this method only at the end, as calling it earlier gives a slower
    # performance to load operationplans
    self.cursor.execute('''
      select coalesce(max(id),1) + 1 as max_id
      from operationplan
      ''')
    d = self.cursor.fetchone()
    frepple.settings.id = d[0]


  def loadDemand(self):
    print('Importing demands...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, due, quantity, priority, item_id,
        operation_id, customer_id, owner_id, minshipment, maxlateness,
        category, subcategory, source, location_id, status
      FROM demand
      WHERE (status IS NULL OR status ='open' OR status = 'quote') %s
      ''' % self.filter_and)
    for i in self.cursor.fetchall():
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
        if i[8]:
          x.minshipment = i[8]
        if i[9] is not None:
          x.maxlateness = i[9].total_seconds()
        if i[13]:
          x.location = frepple.location(name=i[13])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d demands in %.2f seconds' % (cnt, time() - starttime))


  def runStatic(self):
    '''
    This function is expected to be run by the python interpreter in the
    frepple application.
    It loads data from the database into the frepple memory.
    '''
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    settings.DEBUG = False

    # Create a database connection
    self.cursor = connections[self.database].cursor()

    # Sequential load of all entities
    # Some entities could be loaded in parallel threads, but in preliminary tests
    # we haven't seen a clear performance gain. It is unclear what the limiting
    # bottleneck is: python or frepple, definitely not the database...
    self.loadParameter()
    self.loadCalendars()
    self.loadCalendarBuckets()
    self.loadLocations()
    self.loadCustomers()
    self.loadSuppliers()
    self.loadOperations()
    self.loadSuboperations()
    self.loadItems()
    self.loadBuffers()
    self.loadSetupMatrices()
    self.loadResources()
    self.loadResourceSkills()
    self.loadItemSuppliers()
    self.loadItemDistributions()
    self.loadOperationMaterials()
    self.loadOperationResources()
 
    # Close the database connection
    self.cursor.close()


  def runDynamic(self):
    '''
    This function is expected to be run by the python interpreter in the
    frepple application.
    It loads data from the database into the frepple memory.
    '''
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    settings.DEBUG = False

    # Create a database connection
    self.cursor = connections[self.database].cursor()

    # Sequential load of all entities
    self.loadDemand()
    self.loadOperationPlans()

    # Close the database connection
    self.cursor.close()
