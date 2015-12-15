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

from freppledb.input.models import Resource

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
    try:
      self.cursor.execute("SELECT value FROM common_parameter where name='currentdate'")
      d = self.cursor.fetchone()
      frepple.settings.current = datetime.strptime(d[0], "%Y-%m-%d %H:%M:%S")
    except:
      frepple.settings.current = datetime.now().replace(microsecond=0)
      print('Using system clock as current date: %s' % frepple.settings.current)
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
        name, defaultvalue, source
      FROM calendar %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        frepple.calendar(name=i[0], default=i[1], source=i[2])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d calendars in %.2f seconds' % (cnt, time() - starttime))


  def loadCalendarBuckets(self):
    print('Importing calendar buckets...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
       SELECT
         calendar_id, startdate, enddate, id, priority, value,
         sunday, monday, tuesday, wednesday, thursday, friday, saturday,
         starttime, endtime, source
      FROM calendarbucket %s
      ORDER BY calendar_id, startdate desc
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        days = 0
        if i[6]:
          days += 1
        if i[7]:
          days += 2
        if i[8]:
          days += 4
        if i[9]:
          days += 8
        if i[10]:
          days += 16
        if i[11]:
          days += 32
        if i[12]:
          days += 64
        b = frepple.calendar(name=i[0]).addBucket(i[3])
        b.value = i[5]
        b.days = days
        if i[13]:
          b.starttime = i[13].hour * 3600 + i[13].minute * 60 + i[13].second
        if i[14]:
          b.endtime = i[14].hour * 3600 + i[14].minute * 60 + i[14].second + 1
        if i[4]:
          b.priority = i[4]
        if i[1]:
          b.start = i[1]
        if i[2]:
          b.end = i[2]
        if i[15]:
          b.source = i[15]
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
        category, subcategory, source
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
            x.duration = i[7]
        elif i[6] == "time_per":
          x = frepple.operation_time_per(
            name=i[0], description=i[12], category=i[13], subcategory=i[14], source=i[15]
            )
          if i[7]:
            x.duration = i[7]
          if i[8]:
            x.duration_per = i[8]
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
          x.fence = i[1]
        if i[2]:
          x.posttime = i[2]
        if i[3]:
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
    self.cursor.execute('''
      SELECT
        name, description, operation_id, owner_id,
        price, category, subcategory, source
      FROM item %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        x = frepple.item(name=i[0], description=i[1], category=i[5], subcategory=i[6], source=i[7])
        if i[2]:
          x.operation = frepple.operation(name=i[2])
        if i[3]:
          x.owner = frepple.item(name=i[3])
        if i[4]:
          x.price = i[4]
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
        cost, priority, effective_start, effective_end, source, leadtime
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
        curitemsupplier = frepple.itemsupplier(supplier=cursupplier, item=curitem, source=i[9], leadtime=i[10] or 0)
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
        cost, priority, effective_start, effective_end, source, leadtime
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
        curitemdistribution = frepple.itemdistribution(origin=curorigin, item=curitem, source=i[9], leadtime=i[10] or 0)
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
      except Exception as e:
        print("Error:", e)
    print('Loaded %d item itemdistributions in %.2f seconds' % (cnt, time() - starttime))


  def loadBuffers(self):
    print('Importing buffers...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT name, description, location_id, item_id, onhand,
        minimum, minimum_calendar_id, producing_id, type, leadtime, min_inventory,
        max_inventory, min_interval, max_interval, size_minimum,
        size_multiple, size_maximum, fence, category, subcategory, source
      FROM buffer %s
      ''' % self.filter_where)
    for i in self.cursor.fetchall():
      cnt += 1
      if i[8] == "procure":
        b = frepple.buffer_procure(
          name=i[0], description=i[1], item=frepple.item(name=i[3]), onhand=i[4],
          category=i[18], subcategory=i[19], source=i[20]
          )
        if i[9]:
          b.leadtime = i[9]
        if i[10]:
          b.mininventory = i[10]
        if i[11]:
          b.maxinventory = i[11]
        if i[14]:
          b.size_minimum = i[14]
        if i[15]:
          b.size_multiple = i[15]
        if i[16]:
          b.size_maximum = i[16]
        if i[17]:
          b.fence = i[17]
      elif i[8] == "infinite":
        b = frepple.buffer_infinite(
          name=i[0], description=i[1], item=frepple.item(name=i[3]), onhand=i[4],
          category=i[18], subcategory=i[19], source=i[20]
          )
      elif not i[8] or i[8] == "default":
        b = frepple.buffer(
          name=i[0], description=i[1], item=frepple.item(name=i[3]), onhand=i[4],
          category=i[18], subcategory=i[19], source=i[20]
          )
      else:
        raise ValueError("Buffer type '%s' not recognized" % i[8])
      if i[20] == 'tool':
        b.tool = True
      if i[2]:
        b.location = frepple.location(name=i[2])
      if i[5]:
        b.minimum = i[5]
      if i[6]:
        b.minimum_calendar = frepple.calendar(name=i[6])
      if i[7]:
        b.producing = frepple.operation(name=i[7])
      if i[12]:
        b.mininterval = i[12]
      if i[13]:
        b.maxinterval = i[13]
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
          r.duration = i[4]
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
            x.maxearly = i[7]
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


  def loadFlows(self):
    print('Importing flows...')
    cnt = 0
    starttime = time()
    # Note: The sorting of the flows is not really necessary, but helps to make
    # the planning progress consistent across runs and database engines.
    self.cursor.execute('''
      SELECT
        operation_id, thebuffer_id, quantity, type, effective_start,
        effective_end, name, priority, search, source
      FROM flow %s
      ORDER BY operation_id, thebuffer_id
      ''' % self.filter_where)
    curbufname = None
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        if i[1] != curbufname:
          curbufname = i[1]
          curbuf = frepple.buffer(name=curbufname)
        curflow = frepple.flow(operation=frepple.operation(name=i[0]), type="flow_%s" % i[3], buffer=curbuf, quantity=i[2], source=i[9])
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
    self.cursor.execute('''
      SELECT count(*)
      FROM flow
      WHERE alternate IS NOT NULL AND alternate <> ''
      ''')
    if self.cursor.fetchone()[0]:
      raise ValueError("Flow.alternate field is not used any longer. Use only flow.name")
    print('Loaded %d flows in %.2f seconds' % (cnt, time() - starttime))


  def loadLoads(self):
    print('Importing loads...')
    cnt = 0
    starttime = time()
    # Note: The sorting of the loads is not really necessary, but helps to make
    # the planning progress consistent across runs and database engines.
    self.cursor.execute('''
      SELECT
        operation_id, resource_id, quantity, effective_start, effective_end, name,
        priority, setup, search, skill_id, source
      FROM resourceload %s
      ORDER BY operation_id, resource_id
      ''' % self.filter_where)
    curresname = None
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        if i[1] != curresname:
          curresname = i[1]
          curres = frepple.resource(name=curresname)
        curload = frepple.load(operation=frepple.operation(name=i[0]), resource=curres, quantity=i[2], source=i[10])
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
    self.cursor.execute('''
      SELECT count(*)
      FROM resourceload
      WHERE alternate IS NOT NULL AND alternate <> ''
      ''')
    if self.cursor.fetchone()[0]:
      raise ValueError("Load.alternate field is not used any longer. Use only load.name")
    print('Loaded %d loads in %.2f seconds' % (cnt, time() - starttime))


  def loadOperationPlans(self):
    print('Importing operationplans...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        operation_id, id, quantity, startdate, enddate, status, source
      FROM operationplan
      WHERE owner_id IS NULL and quantity >= 0 and status <> 'closed' %s
      ORDER BY id ASC
      ''' % self.filter_and)
    for i in self.cursor.fetchall():
      cnt += 1
      opplan = frepple.operationplan(
        operation=frepple.operation(name=i[0]),
        id=i[1], quantity=i[2], source=i[6]
        )
      if i[3]:
        opplan.start = i[3]
      if i[4]:
        opplan.end = i[4]
      opplan.status = i[5]
    self.cursor.execute('''
      SELECT
        operation_id, id, quantity, startdate, enddate, status, owner_id, source
      FROM operationplan
      WHERE owner_id IS NOT NULL and quantity >= 0 and status <> 'closed' %s
      ORDER BY id ASC
      ''' % self.filter_and)
    for i in self.cursor.fetchall():
      cnt += 1
      opplan = frepple.operationplan(
        operation=frepple.operation(name=i[0]),
        id=i[1], quantity=i[2], source=i[7],
        owner=frepple.operationplan(id=i[6])
        )
      if i[3]:
        opplan.start = i[3]
      if i[4]:
        opplan.end = i[4]
      opplan.status = i[5]
    print('Loaded %d operationplans in %.2f seconds' % (cnt, time() - starttime))


  def loadPurchaseOrders(self):
    print('Importing purchase orders...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        location_id, id, reference, item_id, supplier_id, quantity, startdate, enddate, status, source
      FROM purchase_order
      WHERE status <> 'closed' %s
      ORDER BY location_id, id ASC
      ''' % self.filter_and)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        frepple.operation_itemsupplier.createOrder(
          location=frepple.location(name=i[0]),
          id=i[1], reference=i[2],
          item=frepple.item(name=i[3]) if i[3] else None,
          supplier=frepple.supplier(name=i[4]) if i[4] else None,
          quantity=i[5], start=i[6], end=i[7],
          status=i[8], source=i[9]
          )
      except Exception as e:
        print("Error:", e)
    print('Loaded %d purchase orders in %.2f seconds' % (cnt, time() - starttime))


  def loadDistributionOrders(self):
    print('Importing distribution orders...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        destination_id, id, reference, item_id, origin_id, quantity, startdate,
        enddate, consume_material, status, source
      FROM distribution_order
      WHERE status <> 'closed' %s
      ORDER BY destination_id, id ASC
      ''' % self.filter_and)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        frepple.operation_itemdistribution.createOrder(
          destination=frepple.location(name=i[0]),
          id=i[1], reference=i[2],
          item=frepple.item(name=i[3]) if i[3] else None,
          origin=frepple.location(name=i[4]) if i[4] else None,
          quantity=i[5], start=i[6], end=i[7],
          consume_material=i[8] if i[8] != None else True,
          status=i[9], source=i[10]
          )
      except Exception as e:
        print("Error:", e)
    print('Loaded %d distribution orders in %.2f seconds' % (cnt, time() - starttime))


  def loadDemand(self):
    print('Importing demands...')
    cnt = 0
    starttime = time()
    self.cursor.execute('''
      SELECT
        name, due, quantity, priority, item_id,
        operation_id, customer_id, owner_id, minshipment, maxlateness,
        category, subcategory, source, location_id
      FROM demand
      WHERE (status IS NULL OR status ='open' OR status = 'quote') %s
      ''' % self.filter_and)
    for i in self.cursor.fetchall():
      cnt += 1
      try:
        x = frepple.demand(
          name=i[0], due=i[1], quantity=i[2], priority=i[3],
          item=frepple.item(name=i[4]), category=i[10], subcategory=i[11], source=i[12]
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
          x.maxlateness = i[9]
        if i[13]:
          x.location = frepple.location(name=i[13])
      except Exception as e:
        print("Error:", e)
    print('Loaded %d demands in %.2f seconds' % (cnt, time() - starttime))


  def run(self):
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
    self.loadItemSuppliers()
    self.loadItemDistributions()
    self.loadBuffers()
    self.loadSetupMatrices()
    self.loadResources()
    self.loadResourceSkills()
    self.loadFlows()
    self.loadLoads()
    self.loadOperationPlans()
    self.loadPurchaseOrders()
    self.loadDistributionOrders()
    self.loadDemand()

    # Close the database connection
    self.cursor.close()

    # Finalize
    print('Done')
