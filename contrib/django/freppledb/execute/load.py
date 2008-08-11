#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
Load information from a database in frePPLe memory.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

It extracts the information fields from the database, and then uses the Python
API of frePPLe to bring the data into the frePPLe C++ core engine.
'''

from time import time
from xml.sax.saxutils import quoteattr
from threading import Thread

from django.db import connection
from django.conf import settings

import frepple

header = '<?xml version="1.0" encoding="UTF-8" ?><plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'


def loadPlan(cursor):
  # Plan (limited to the first one only)
  print 'Import plan...'
  x = [ header ]
  cursor.execute("SELECT currentdate, name, description FROM plan")
  d = cursor.fetchone()
  if not d: raise ValueError('Missing a record in the plan table')
  frepple.settings.current = d[0]
  frepple.settings.name = d[1]
  frepple.settings.description = d[2]


def loadLocations(cursor):
  '''
  Importing locations happens in a different way than the other entities.
  Rather than preparing an XML document, the python code is directly interacting
  with the C++ frePPLe API.
  This interaction is at least 2-3 times faster than the XML way. It also
  allows much more flexibility to interact with the objects in a more
  productive and more complex way.
  '''
  print 'Importing locations...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM location")
  for i,j,k in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.location(name=i, description=j)
      if k: x.owner=frepple.location(name=k)
    except Exception, e: print "Error:", e
  print 'Loaded %d locations in %.2f seconds' % (cnt, time() - starttime)


def loadCalendars(cursor):
  print 'Importing calendars...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, defaultvalue FROM calendar")
  for i, j in cursor.fetchall():
    cnt += 1
    try: frepple.calendar(name=i, default=j)
    except Exception, e: print "Error:", e
  print 'Loaded %d calendars in %.2f seconds' % (cnt, time() - starttime)

  # Bucket
  print 'Importing buckets...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT calendar_id, startdate, enddate, name, priority, value FROM bucket")
  x = [ header ]
  x.append('<calendars>')
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    x.append('<calendar name=%s><buckets><bucket%s%s%s%s value="%f"/></buckets></calendar>' % (
       quoteattr(i),
       (j and ' start="%s"' % j.isoformat()) or '',
       (k and ' end="%s"' % k.isoformat()) or '',
       (l and ' name=%s' % quoteattr(l)) or '',
       (m and ' priority="%s"' % m) or '',
       n,
      ))
  x.append('</calendars></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime)


def loadCustomers(cursor):
  print 'Importing customers...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM customer")
  for i, j, k in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.customer(name=i, description=j)
      if k: x.owner = frepple.customer(name=k)
    except Exception, e: print "Error:", e
  print 'Loaded %d customers in %.2f seconds' % (cnt, time() - starttime)


def loadOperations(cursor):
  print 'Importing operations...'
  cnt = 0
  starttime = time()
  cursor.execute('''
    SELECT
      name, fence, pretime, posttime, sizeminimum, sizemultiple, type,
      duration, duration_per, location_id, cost
    FROM operation
    ''')
  for i, j, k, l, m, n, p, q, r, s, t in cursor.fetchall():
    cnt += 1
    try:
      if not p or p == "operation_fixed_time":
        x = frepple.operation_fixed_time(name=i)
        if q: x.duration = q
      elif p == "operation_time_per":
        x = frepple.operation_time_per(name=i)
        if q: x.duration = q
        if r: x.duration_per = r
      elif p == "operation_alternate":
        x = frepple.operation_alternate(name=i)
      elif p == "operation_routing":
        x = frepple.operation_routing(name=i)
      else:
        raise ValueError("Operation type '%s' not recognized" % p)
      if j: x.fence = j
      if k: x.pretime = k
      if l: x.posttime = l
      if m: x.size_minimum = m
      if n: x.size_multiple = n
      if s: x.location = frepple.location(name=s)
      if t: x.cost = t
    except Exception, e: print "Error:", e
  print 'Loaded %d operations in %.2f seconds' % (cnt, time() - starttime)


def loadSuboperations(cursor):
  print 'Importing suboperations...'
  cnt = 0
  starttime = time()
  x = [ header, '<operations>' ]
  cursor.execute('''
    SELECT operation_id, suboperation_id, priority, effective_start, effective_end
    FROM suboperation, operation
    WHERE suboperation.operation_id = operation.name
    AND operation.type = 'operation_alternate'
    ORDER BY operation_id, priority
    ''')
  curoper = ''
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    if i != curoper:
      if curoper != '': x.append('</operation>')
      x.append('<operation name=%s xsi:type="operation_alternate">' % quoteattr(i))
      curoper = i
    x.append('<alternate priority="%s"><operation name=%s/>' % (k,quoteattr(j)))
    if l: x.append('<effective_start>%s</effective_start>' % l.isoformat())
    if m: x.append('<effective_end>%s</effective_end>' % m.isoformat())
    x.append('</alternate>')
  if curoper != '': x.append('</operation>')
  x.append('</operations></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d suboperations in %.2f seconds' % (cnt, time() - starttime)


def loadItems(cursor):
  print 'Importing items...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, operation_id, owner_id, price FROM item")
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.item(name=i, description=j)
      if k: x.operation = frepple.operation(name=k)
      if l: x.owner = frepple.item(name=l)
      if m: x.price = m
    except Exception, e: print "Error:", e
  print 'Loaded %d items in %.2f seconds' % (cnt, time() - starttime)


def loadBuffers(cursor):
  print 'Importing buffers...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT name, description, location_id, item_id, onhand,
     minimum_id, producing_id, type, leadtime, min_inventory,
     max_inventory, min_interval, max_interval, size_minimum,
     size_multiple, size_maximum, fence, carrying_cost FROM buffer''')
  for i, j, k, l, m, n, o, q, f1, f2, f3, f4, f5, f6, f7, f8, f9, p in cursor.fetchall():
    cnt += 1
    if q == "buffer_procure":
      b = frepple.buffer_procure(
        name=i, description=j, location=frepple.location(name=k),
        item=frepple.item(name=l), onhand=m
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
    elif q == "buffer_infinite":
      b = frepple.buffer_infinite(
        name=i, description=j, location=frepple.location(name=k),
        item=frepple.item(name=l), onhand=m
        )
    elif not q:
      b = frepple.buffer(
        name=i, description=j, location=frepple.location(name=k),
        item=frepple.item(name=l), onhand=m
        )
    else:
      raise ValueError("Buffer type '%s' not recognized" % q)
    if n: b.minimum = frepple.calendar(name=n)
    if o: b.producing = frepple.operation(name=o)
    if p: b.carrying_cost = p
  print 'Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime)


def loadResources(cursor):
  print 'Importing resources...'
  cnt = 0
  starttime = time()
  cursor.execute('SELECT name, description, maximum_id, location_id, type, cost FROM %s' % connection.ops.quote_name('resource'))
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    try:
      if m == "resource_infinite":
        x = frepple.resource_infinite(
          name=i,
          description=j,
          location=frepple.location(name=l),
          )
      elif not m:
        x = frepple.resource(
          name=i,
          description=j,
          maximum=frepple.calendar(name=k),
          location=frepple.location(name=l),
          )
      else:
        raise ValueError("Resource type '%s' not recognized" % m)
      if n: x.cost = n
    except Exception, e: print "Error:", e
  print 'Loaded %d resources in %.2f seconds' % (cnt, time() - starttime)


def loadFlows(cursor):
  print 'Importing flows...'
  cnt = 0
  starttime = time()
  # Note: The sorting of the flows is not really necessary, but helps to make
  # the planning progress consistent across runs and database engines.
  cursor.execute('''
    SELECT operation_id, thebuffer_id, quantity, type, effective_start, effective_end
    FROM flow
    ORDER BY operation_id, thebuffer_id
    ''')
  x = [ header, '<flows>' ]
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    if l:
      x.append('<flow xsi:type="%s"><operation name=%s/><buffer name=%s/><quantity>%s</quantity>' % (l, quoteattr(i), quoteattr(j), k))
    else:
      x.append('<flow><operation name=%s/><buffer name=%s/><quantity>%s</quantity>' % (quoteattr(i), quoteattr(j), k))
    if m: x.append('<effective_start>%s</effective_start>' % m.isoformat())
    if n: x.append('<effective_end>%s</effective_end>' % n.isoformat())
    x.append('</flow>')
  x.append('</flows></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d flows in %.2f seconds' % (cnt, time() - starttime)


def loadLoads(cursor):
  print 'Importing loads...'
  cnt = 0
  starttime = time()
  # Note: The sorting of the loads is not really necessary, but helps to make
  # the planning progress consistent across runs and database engines.
  cursor.execute('''
    SELECT operation_id, resource_id, quantity, effective_start, effective_end
    FROM resourceload
    ORDER BY operation_id, resource_id
    ''')
  x = [ header , '<loads>' ]
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    x.append('<load><operation name=%s/><resource name=%s/><quantity>%s</quantity>' % (quoteattr(i), quoteattr(j), k))
    if l: x.append('<effective_start>%s</effective_start>' % l.isoformat())
    if m: x.append('<effective_end>%s</effective_end>' % m.isoformat())
    x.append('</load>')
  x.append('</loads></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d loads in %.2f seconds' % (cnt, time() - starttime)


def loadOperationPlans(cursor):
  print 'Importing operationplans...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT identifier, operation_id, quantity, startdate, enddate, locked FROM operationplan order by identifier asc")
  x = [ header , '<operationplans>' ]
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    x.append('<operationplan id="%d" operation=%s quantity="%s">' % (i, quoteattr(j), k))
    if l: x.append( '<start>%s</start>' % l.isoformat())
    if m: x.append( '<end>%s</end>' % m.isoformat())
    if n: x.append( '<locked>true</locked>')
    x.append('</operationplan>')
  x.append('</operationplans></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d operationplans in %.2f seconds' % (cnt, time() - starttime)


def loadForecast(cursor):
  # Detect whether the forecast module is available
  try: import freppleforecast
  except: return

  print 'Importing forecast...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, customer_id, item_id, priority, operation_id, minshipment, calendar_id, discrete, maxlateness FROM forecast")
  x = [ header, '<demands>' ]
  for i, j, k, l, m, n, o, p, q in cursor.fetchall():
    cnt += 1
    x.append('<demand name=%s xsi:type="demand_forecast" priority="%d">' % (quoteattr(i), l))
    if j: x.append( '<customer name=%s />' % quoteattr(j))
    if k: x.append( '<item name=%s />' % quoteattr(k))
    if m: x.append( '<operation name=%s />' % quoteattr(m))
    if n: x.append( '<minshipment>%s</minshipment>' % n)
    if o: x.append( '<calendar name=%s />' % quoteattr(o))
    if not p: x.append( '<discrete>false<discrete>')
    if q != None: x.append( '<maxlateness>PT%sS</maxlateness>' % int(q))
    x.append('</demand>')
  x.append('</demands></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d forecasts in %.2f seconds' % (cnt, time() - starttime)


def loadForecastdemand(cursor):
  # Detect whether the forecast module is available
  try: import freppleforecast
  except: return

  print 'Importing forecast demand...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT forecast_id, startdate, enddate, quantity FROM forecastdemand")
  x = [ header, '<demands>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    x.append('<demand name=%s><buckets><bucket start="%sT00:00:00" end="%sT00:00:00" total="%s"/></buckets></demand>' % (quoteattr(i), j.isoformat(), k.isoformat(), l))
  x.append('</demands></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d forecast demands in %.2f seconds' % (cnt, time() - starttime)


def loadDemand(cursor):
  print 'Importing demands...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, due, quantity, priority, item_id, operation_id, customer_id, owner_id, minshipment, maxlateness FROM demand")
  for i, j, k, l, m, n, o, p, q, r in cursor.fetchall():
    cnt += 1
    try:
      x = frepple.demand( name=i, due=j, quantity=k, priority=l, item=frepple.item(name=m))
      if n: x.operation = frepple.operation(name=n)
      if o: x.customer = frepple.customer(name=o)
      if p: x.owner = frepple.demand(name=p)
      if q: x.minshipment = q
      if r != None: x.maxlateness = r
    except Exception, e: print "Error:", e
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
    cursor = connection.cursor()
    # Run the functions sequentially
    for f in self.functions:
      try: f(cursor)
      except Exception, e: print e


def loadfrepple():
  '''
  This function is expected to be run by the python interpreter in the
  frepple application.
  It loads data from the database into the frepple memory.
  '''
  cursor = connection.cursor()

  # Make sure the debug flag is not set!
  # When it is set, the django database wrapper collects a list of all sql
  # statements executed and their timings. This consumes plenty of memory
  # and cpu time.
  settings.DEBUG = False

  if True:
    # Sequential load of all entities
    loadPlan(cursor)
    loadCalendars(cursor)
    loadLocations(cursor)
    loadCustomers(cursor)
    loadOperations(cursor)
    loadSuboperations(cursor)
    loadItems(cursor)
    loadBuffers(cursor)
    loadResources(cursor)
    loadFlows(cursor)
    loadLoads(cursor)
    loadOperationPlans(cursor)
    loadForecast(cursor)
    loadForecastdemand(cursor)
    loadDemand(cursor)
  else:
    # Loading of entities in a number of 'groups'.
    # The groups are executed in sequence, while the tasks within a group
    # are executed in parallel.
    # The entities are grouped based on their relations.
    #
    # The parallel loading is currently in a "experimental" state only.
    # Reason being that so far parallel loading doesn't bring a clear
    # performance gain.
    # Unclear what the limiting bottleneck is: python or frepple, definately
    # not the database...
    tasks = (
      DatabaseTask(loadPlan),
      DatabaseTask(loadCalendars, loadLocations),
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
      DatabaseTask(loadResources, loadLoads),
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
  cursor.close()
