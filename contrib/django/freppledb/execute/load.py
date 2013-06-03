#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

from time import time
from threading import Thread
import inspect, os
from datetime import datetime

from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

import frepple

database = DEFAULT_DB_ALIAS


def loadParameter(cursor):
  print 'Importing parameters...'
  try:
    cursor.execute("SELECT value FROM common_parameter where name='currentdate'")
    d = cursor.fetchone()
    frepple.settings.current = datetime.strptime(d[0], "%Y-%m-%d %H:%M:%S")
  except:
    print 'Invalid or missing currentdate parameter: using system clock instead'
    frepple.settings.current = datetime.now()


def loadLocations(cursor):
  print 'Importing locations...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id, available_id, category, subcategory FROM location")
  for i,j,k,l,m,n in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.location(name=i, description=j, category=m, subcategory=n)
      if k: x.owner = frepple.location(name=k)
      if l: x.available = frepple.calendar(name=l)
    except Exception as e: print "Error:", e
  print 'Loaded %d locations in %.2f seconds' % (cnt, time() - starttime)


def loadCalendars(cursor):
  print 'Importing calendars...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, defaultvalue FROM calendar")
  for i, j in cursor.fetchall():
    cnt += 1
    try: frepple.calendar(name=i, default=j)
    except Exception as e: print "Error:", e
  print 'Loaded %d calendars in %.2f seconds' % (cnt, time() - starttime)


def loadCalendarBuckets(cursor):
  print 'Importing calendar buckets...'
  cnt = 0
  starttime = time()
  cursor.execute('''
     SELECT 
       calendar_id, startdate, enddate, id, priority, value, 
       sunday, monday, tuesday, wednesday, thursday, friday, saturday, 
       starttime, endtime 
    FROM calendarbucket
    ORDER BY calendar_id, startdate desc
    ''')
  for i, j, k, l, m, n, o1, o2, o3, o4, o5, o6, o7, t1, t2 in cursor.fetchall():
    cnt += 1
    try:
      days = 0
      if o1: days += 1
      if o2: days += 2
      if o3: days += 4
      if o4: days += 8
      if o5: days += 16
      if o6: days += 32
      if o7: days += 64
      b = frepple.calendar(name=i).addBucket(l)
      b.value = n
      b.days = days
      if t1: b.starttime = t1.hour*3600 + t1.minute*60 + t1.second
      if t2: b.endtime = t2.hour*3600 + t2.minute*60 + t2.second + 1
      if m: b.priority = m
      if j: b.start = j
      if k: b.end = k
    except Exception as e: print "Error:", e
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime)


def loadCustomers(cursor):
  print 'Importing customers...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id, category, subcategory FROM customer")
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.customer(name=i, description=j, category=l, subcategory=m)
      if k: x.owner = frepple.customer(name=k)
    except Exception as e: print "Error:", e
  print 'Loaded %d customers in %.2f seconds' % (cnt, time() - starttime)


def loadOperations(cursor):
  print 'Importing operations...'
  cnt = 0
  starttime = time()
  cursor.execute('''
    SELECT
      name, fence, pretime, posttime, sizeminimum, sizemultiple, sizemaximum,
      type, duration, duration_per, location_id, cost, search, description,
      category, subcategory
    FROM operation
    ''')
  for i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x in cursor.fetchall():
    cnt += 1
    try:
      if not p or p == "fixed_time":
        x = frepple.operation_fixed_time(name=i, description=v, category=w, subcategory=x)
        if q: x.duration = q
      elif p == "time_per":
        x = frepple.operation_time_per(name=i, description=v, category=w, subcategory=x)
        if q: x.duration = q
        if r: x.duration_per = r
      elif p == "alternate":
        x = frepple.operation_alternate(name=i, description=v, category=w, subcategory=x)
      elif p == "routing":
        x = frepple.operation_routing(name=i, description=v, category=w, subcategory=x)
      else:
        raise ValueError("Operation type '%s' not recognized" % p)
      if j: x.fence = j
      if k: x.pretime = k
      if l: x.posttime = l
      if m: x.size_minimum = m
      if n: x.size_multiple = n
      if o: x.size_maximum = o
      if s: x.location = frepple.location(name=s)
      if t: x.cost = t
      if u: x.search = u
    except Exception as e: print "Error:", e
  print 'Loaded %d operations in %.2f seconds' % (cnt, time() - starttime)


def loadSuboperations(cursor):
  print 'Importing suboperations...'
  cnt = 0
  starttime = time()
  cursor.execute('''
    SELECT operation_id, suboperation_id, priority, effective_start, effective_end, operation.type
    FROM suboperation, operation
    WHERE suboperation.operation_id = operation.name
      AND priority >= 0
    ORDER BY operation_id, priority
    ''')
  curopername = None
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    try:
      if i != curopername:
        curopername = i
        if n == 'alternate':
          curoper = frepple.operation_alternate(name=curopername)
        else:
          curoper = frepple.operation_routing(name=curopername)
      if isinstance(curoper,frepple.operation_routing):
        curoper.addStep(frepple.operation(name=j))
      else:
        if l:
          if m:
            curoper.addAlternate(operation=frepple.operation(name=j),priority=k,effective_start=l,effective_end=m)
          else:
            curoper.addAlternate(operation=frepple.operation(name=j),priority=k,effective_start=l)
        elif m:
            curoper.addAlternate(operation=frepple.operation(name=j),priority=k,effective_end=m)
        else:
          curoper.addAlternate(operation=frepple.operation(name=j),priority=k)
    except Exception as e: print "Error:", e
  print 'Loaded %d suboperations in %.2f seconds' % (cnt, time() - starttime)


def loadItems(cursor):
  print 'Importing items...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT
      name, description, operation_id, owner_id,
      price, category, subcategory
      FROM item''')
  for i,j,k,l,m,n,o in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.item(name=i, description=j, category=n, subcategory=o)
      if k: x.operation = frepple.operation(name=k)
      if l: x.owner = frepple.item(name=l)
      if m: x.price = m
    except Exception as e: print "Error:", e
  print 'Loaded %d items in %.2f seconds' % (cnt, time() - starttime)


def loadBuffers(cursor):
  print 'Importing buffers...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT name, description, location_id, item_id, onhand,
     minimum, minimum_calendar_id, producing_id, type, leadtime, min_inventory,
     max_inventory, min_interval, max_interval, size_minimum,
     size_multiple, size_maximum, fence, carrying_cost,
     category, subcategory FROM buffer''')
  for i,j,k,l,m,t,n,o,q,f1,f2,f3,f4,f5,f6,f7,f8,f9,p,r,s in cursor.fetchall():
    cnt += 1
    if q == "procure":
      b = frepple.buffer_procure(
        name=i, description=j, item=frepple.item(name=l), onhand=m,
        category=r, subcategory=s
        )
      if f1: b.leadtime = f1
      if f2: b.mininventory = f2
      if f3: b.maxinventory = f3
      if f4: b.mininterval = f4
      if f5: b.maxinterval = f5
      if f6: b.size_minimum = f6
      if f7: b.size_multiple = f7
      if f8: b.size_maximum = f8
      if f9: b.fence = f9
    elif q == "infinite":
      b = frepple.buffer_infinite(
        name=i, description=j, item=frepple.item(name=l), onhand=m,
        category=r, subcategory=s
        )
    elif not q or q == "default":
      b = frepple.buffer(
        name=i, description=j, item=frepple.item(name=l), onhand=m,
        category=r, subcategory=s
        )
    else:
      raise ValueError("Buffer type '%s' not recognized" % q)
    if k: b.location = frepple.location(name=k)
    if t: b.minimum = t
    if n: b.minimum_calendar = frepple.calendar(name=n)
    if o: b.producing = frepple.operation(name=o)
    if p: b.carrying_cost = p
  print 'Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime)


def loadSetupMatrices(cursor):
  print 'Importing setup matrix rules...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT setupmatrix_id, priority, fromsetup, tosetup, duration, cost
    FROM setuprule
    order by setupmatrix_id, priority desc''')
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    try:
      r = frepple.setupmatrix(name=i).addRule(priority=j)
      if k: r.fromsetup = k
      if l: r.tosetup = l
      if m: r.duration = m
      if n: r.cost = n
    except Exception as e: print "Error:", e
  print 'Loaded %d setup matrix rules in %.2f seconds' % (cnt, time() - starttime)


def loadResources(cursor):
  print 'Importing resources...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT
    name, description, maximum, maximum_calendar_id, location_id, type, cost,
    maxearly, setup, setupmatrix_id, category, subcategory
    FROM %s''' % connections[database].ops.quote_name('resource'))
  for i,j,t,k,l,m,n,o,p,q,r,s in cursor.fetchall():
    cnt += 1
    try:
      if m == "infinite":
        x = frepple.resource_infinite(name=i,description=j,category=r,subcategory=s)
      elif not m or m == "default":
        x = frepple.resource_default(name=i,description=j,category=r,subcategory=s)
        if k: x.maximum_calendar = frepple.calendar(name=k)
        if o: x.maxearly = o
        if t: x.maximum = t
      else:
        raise ValueError("Resource type '%s' not recognized" % m)
      if l: x.location = frepple.location(name=l)
      if n: x.cost = n
      if p: x.setup = p
      if q: x.setupmatrix = frepple.setupmatrix(name=q)
    except Exception as e: print "Error:", e
  print 'Loaded %d resources in %.2f seconds' % (cnt, time() - starttime)


def loadResourceSkills(cursor):
  print 'Importing resource skills...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT
    resource_id, skill_id, effective_start, effective_end, priority
    FROM resourceskill
    ORDER BY skill_id, priority, resource_id''')
  for i,j,k,l,m in cursor.fetchall():
    cnt += 1
    try:
      cur = frepple.resourceskill(resource=frepple.resource(name=i), skill=frepple.skill(name=j), priority=m or 1)
      if k: cur.effective_start = k
      if l: cur.effective_end = l
    except Exception as e: print "Error:", e
  print 'Loaded %d resource skills in %.2f seconds' % (cnt, time() - starttime)


def loadFlows(cursor):
  print 'Importing flows...'
  cnt = 0
  starttime = time()
  # Note: The sorting of the flows is not really necessary, but helps to make
  # the planning progress consistent across runs and database engines.
  cursor.execute('''SELECT
      operation_id, thebuffer_id, quantity, type, effective_start,
      effective_end, name, priority, search
    FROM flow
    WHERE alternate IS NULL OR alternate = ''
    ORDER BY operation_id, thebuffer_id
    ''')
  curbufname = None
  for i, j, k, l, m, n, o, p, q in cursor.fetchall():
    cnt += 1
    try:
      if j != curbufname:
        curbufname = j
        curbuf = frepple.buffer(name=curbufname)
      curflow = frepple.flow(operation=frepple.operation(name=i), type="flow_%s" % l, buffer=curbuf, quantity=k)
      if m: curflow.effective_start = m
      if n: curflow.effective_end = n
      if o: curflow.name = o
      if p: curflow.priority = p
      if q: curflow.search = q
    except Exception as e: print "Error:", e
  cursor.execute('''
    SELECT
      operation_id, thebuffer_id, quantity, type, effective_start,
      effective_end, name, alternate, priority, search
    FROM flow
    WHERE alternate IS NOT NULL AND alternate <> ''
    ORDER BY operation_id, thebuffer_id
    ''')
  curbufname = None
  for i, j, k, l, m, n, o, p, q, r in cursor.fetchall():
    cnt += 1
    try:
      if j != curbufname:
        curbufname = j
        curbuf = frepple.buffer(name=curbufname)
      curflow = frepple.flow(operation=frepple.operation(name=i), type=l, buffer=curbuf, quantity=k)
      if m: curflow.effective_start = m
      if n: curflow.effective_end = n
      if o: curflow.name = o
      if p: curflow.alternate = p
      if q: curflow.priority = q
      if r: curflow.search = r
    except Exception as e: print "Error:", e
  print 'Loaded %d flows in %.2f seconds' % (cnt, time() - starttime)


def loadLoads(cursor):
  print 'Importing loads...'
  cnt = 0
  starttime = time()
  # Note: The sorting of the loads is not really necessary, but helps to make
  # the planning progress consistent across runs and database engines.
  cursor.execute('''
    SELECT
      operation_id, resource_id, quantity, effective_start, effective_end, name,
      priority, setup, search, skill_id
    FROM resourceload
    WHERE alternate IS NULL OR alternate = ''
    ORDER BY operation_id, resource_id
    ''')
  curresname = None
  for i, j, k, l, m, n, o, p, q, r in cursor.fetchall():
    cnt += 1
    try:
      if j != curresname:
        curresname = j
        curres = frepple.resource(name=curresname)
      curload = frepple.load(operation=frepple.operation(name=i), resource=curres, quantity=k)
      if l: curload.effective_start = l
      if m: curload.effective_end = m
      if n: curload.name = n
      if o: curload.priority = o
      if p: curload.setup = p
      if q: curload.search = q
      if r: curload.skill = frepple.skill(name=r)
    except Exception as e: print "Error:", e
  cursor.execute('''
    SELECT
      operation_id, resource_id, quantity, effective_start, effective_end,
      name, alternate, priority, setup, search, skill_id
    FROM resourceload
    WHERE alternate IS NOT NULL AND alternate <> ''
    ORDER BY operation_id, resource_id
    ''')
  curresname = None
  for i, j, k, l, m, n, o, p, q, r, s in cursor.fetchall():
    cnt += 1
    try:
      if j != curresname:
        curresname = j
        curres = frepple.resource(name=curresname)
      curload = frepple.load(operation=frepple.operation(name=i), resource=curres, quantity=k)
      if l: curload.effective_start = l
      if m: curload.effective_end = m
      if n: curload.name = n
      if o: curload.alternate = o
      if p: curload.priority = p
      if q: curload.setup = q
      if r: curload.search = r
      if s: curload.skill = frepple.skill(name=s)
    except Exception as e: print "Error:", e
  print 'Loaded %d loads in %.2f seconds' % (cnt, time() - starttime)


def loadOperationPlans(cursor):  
  print 'Importing operationplans...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT operation_id, id, quantity, startdate, enddate, locked 
     FROM operationplan
     where owner_id is null 
     order by id asc''')
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    frepple.operationplan(operation=frepple.operation(name=i),
      id=j, quantity=k, start=l, end=m).locked = n
  cursor.execute('''SELECT operation_id, id, quantity, startdate, enddate, locked, owner_id 
     FROM operationplan
     where owner_id is not null 
     order by id asc''')
  for i, j, k, l, m, n, o in cursor.fetchall():
    cnt += 1
    frepple.operationplan(operation=frepple.operation(name=i),
      id=j, quantity=k, start=l, end=m, owner=frepple.operationplan(id=o)).locked = n
  print 'Loaded %d operationplans in %.2f seconds' % (cnt, time() - starttime)


def loadForecast(cursor):
  # Detect whether the forecast module is available
  if not 'demand_forecast' in [ a[0] for a in inspect.getmembers(frepple) ]:
    return

  print 'Importing forecast...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT name, customer_id, item_id, priority,
    operation_id, minshipment, calendar_id, discrete, maxlateness,
    category,subcategory
    FROM forecast''')
  for i,j,k,l,m,n,o,p,q,r,s in cursor.fetchall():
    cnt += 1
    fcst = frepple.demand_forecast(name=i, priority=l, category=r, subcategory=s)
    if j: fcst.customer = frepple.customer(name=j)
    if k: fcst.item = frepple.item(name=k)
    if m: fcst.operation = frepple.operation(name=m)
    if n: fcst.minshipment = n
    if o: fcst.calendar = frepple.calendar(name=o)
    if not p: fcst.discrete = False
    if q != None: fcst.maxlateness = q
  print 'Loaded %d forecasts in %.2f seconds' % (cnt, time() - starttime)


def loadForecastdemand(cursor):
  # Detect whether the forecast module is available
  if not 'demand_forecast' in [ a[0] for a in inspect.getmembers(frepple) ]:
    return

  print 'Importing forecast demand...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT forecast_id, quantity, startdate, enddate FROM forecastdemand")
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    frepple.demand_forecast(name=i).setQuantity(j,k,l)
  print 'Loaded %d forecast demands in %.2f seconds' % (cnt, time() - starttime)


def loadDemand(cursor):
  print 'Importing demands...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT name, due, quantity, priority, item_id,
     operation_id, customer_id, owner_id, minshipment, maxlateness,
     category, subcategory
     FROM demand''')
  for i,j,k,l,m,n,o,p,q,r,s,t in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.demand( name=i, due=j, quantity=k, priority=l, item=frepple.item(name=m),category=s,subcategory=t)
      if n: x.operation = frepple.operation(name=n)
      if o: x.customer = frepple.customer(name=o)
      if p: x.owner = frepple.demand(name=p)
      if q: x.minshipment = q
      if r != None: x.maxlateness = r
    except Exception as e: print "Error:", e
  print 'Loaded %d demands in %.2f seconds' % (cnt, time() - starttime)


class DatabaseTask(Thread):
  '''
  An auxiliary class that allows us to run a function with its own
  database connection in its own thread.
  '''
  def __init__(self, *f):
    super(DatabaseTask, self).__init__()
    self.functions = f

  def run(self):
    # Create a database connection
    cursor = connections[database].cursor()

    # Run the functions sequentially
    for f in self.functions:
      try: f(cursor)
      except Exception as e: print e

    # Close the connection
    cursor.close()


def loadfrepple():
  '''
  This function is expected to be run by the python interpreter in the
  frepple application.
  It loads data from the database into the frepple memory.
  '''
  # Make sure the debug flag is not set!
  # When it is set, the django database wrapper collects a list of all sql
  # statements executed and their timings. This consumes plenty of memory
  # and cpu time.
  global database
  settings.DEBUG = False

  if 'FREPPLE_DATABASE' in os.environ:
    database = os.environ['FREPPLE_DATABASE']

  if True:
    # Create a database connection
    cursor = connections[database].cursor()

    # Sequential load of all entities
    loadParameter(cursor)
    loadCalendars(cursor)
    loadCalendarBuckets(cursor)
    loadLocations(cursor)
    loadCustomers(cursor)
    loadOperations(cursor)
    loadSuboperations(cursor)
    loadItems(cursor)
    loadBuffers(cursor)
    loadSetupMatrices(cursor)
    loadResources(cursor)
    loadResourceSkills(cursor)
    loadFlows(cursor)
    loadLoads(cursor)
    loadOperationPlans(cursor)
    loadForecast(cursor)
    loadForecastdemand(cursor)
    loadDemand(cursor)

    # Close the database connection
    cursor.close()
  else:
    # Loading of entities in a number of 'groups'.
    # The groups are executed in sequence, while the tasks within a group
    # are executed in parallel.
    # The entities are grouped based on their relations.
    #
    # The parallel loading is currently not enabled by default, since we
    # don't see a clear performance gain.
    # It is unclear what the limiting bottleneck is: python or frepple, definately
    # not the database...
    tasks = (
      DatabaseTask(loadParameter, loadLocations),
      DatabaseTask(loadCalendars, loadCalendarBuckets),
      DatabaseTask(loadCustomers),
      )
    for i in tasks: i.start()
    for i in tasks: i.join()
    tasks = (
      DatabaseTask(loadOperations,loadSuboperations),
      DatabaseTask(loadForecast),
      )
    for i in tasks: i.start()
    for i in tasks: i.join()
    loadItems(cursor)
    tasks = (
      DatabaseTask(loadBuffers,loadFlows),
      DatabaseTask(loadSetupMatrices, loadResources, loadLoads),
      )
    for i in tasks: i.start()
    for i in tasks: i.join()
    tasks = (
      DatabaseTask(loadOperationPlans),
      DatabaseTask(loadForecastdemand,loadDemand),
      )
    for i in tasks: i.start()
    for i in tasks: i.join()

  # Finalize
  print 'Done'
