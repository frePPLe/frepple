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

It extracts the information fields from the database, and then uses Python
to compose an XML string that is then processed by the C++ core engine.
'''

# A small experiment with an alternative design showed an interesting
# performance improvement. By composing the XML documents in the database (and
# thus keeping the processing in Python minimal) a speedup with a factor 2
# can easily be achieved.
# However, since the SQL statements for such an extract are quickly becoming
# non-portable between databases :-( I decided to stick to the current design.
# After all, the performance of the current adapters is pretty okay anyway...


from time import time
from xml.sax.saxutils import quoteattr, escape
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
  i, j, k = d
  x.append('<current>%s</current>' % i.isoformat())
  if j: x.append('<name>%s</name>' % escape(j))
  if k: x.append('<description>%s</description>' % escape(k))
  x.append('</plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)


def loadLocations(cursor):
  print 'Importing locations...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM location")
  x = [ header, '<locations>' ]
  for i,j,k in cursor.fetchall():
    cnt += 1
    x.append(u'<location name=%s>' % quoteattr(i))
    if j: x.append(u'<description>%s</description>' % escape(j))
    if k: x.append(u'<owner name=%s/>' % quoteattr(k))
    x.append('</location>')
  x.append('</locations></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d locations in %.2f seconds' % (cnt, time() - starttime)


def loadCalendars(cursor):
  print 'Importing calendars...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, defaultvalue FROM calendar")
  x = [ header ]
  x.append('<calendars>')
  for i, j, k in cursor.fetchall():
    cnt += 1
    if j and k: x.append('<calendar name=%s description=%s default="%s"/>' % (quoteattr(i), quoteattr(j), k))
    elif j: x.append('<calendar name=%s description=%s/>' % (quoteattr(i), quoteattr(j)))
    elif k: x.append('<calendar name=%s default="%s"/>' % (quoteattr(i), k))
    else: x.append('<calendar name=%s/>' % quoteattr(i))
  x.append('</calendars></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
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
    x.append('<calendar name=%s><buckets><bucket%s%s%s%s%s/></buckets></calendar>' % (
       quoteattr(i),
       (j and ' start="%s"' % j.isoformat()) or '',
       (k and ' end="%s"' % k.isoformat()) or '',
       (l and ' name=%s' % quoteattr(l)) or '',
       (m and ' priority="%s"' % m) or '',
       (n and ' value="%s"' % n) or '',
      ))
  x.append('</calendars></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime)


def loadCustomers(cursor):
  print 'Importing customers...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM customer")
  x = [ header, '<customers>' ]
  for i, j, k in cursor.fetchall():
    cnt += 1
    x.append('<customer name=%s>' % quoteattr(i))
    if j: x.append('<description>%s</description>' % escape(j))
    if k: x.append('<owner name=%s/>' % quoteattr(k))
    x.append('</customer>')
  x.append('</customers></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d customers in %.2f seconds' % (cnt, time() - starttime)


def loadOperations(cursor):
  print 'Importing operations...'
  cnt = 0
  starttime = time()
  x = [ header, '<operations>' ]
  cursor.execute('''
    SELECT
      name, fence, pretime, posttime, sizeminimum, sizemultiple, type,
      duration, duration_per, location_id
    FROM operation
    ''')
  for i, j, k, l, m, n, p, q, r, s in cursor.fetchall():
    cnt += 1
    if p:
      x.append('<operation name=%s xsi:type="%s">' % (quoteattr(i),p))
    else:
      x.append('<operation name=%s>' % quoteattr(i))
    if j: x.append('<fence>PT%sS</fence>' % int(j))
    if k: x.append('<pretime>PT%sS</pretime>' % int(k))
    if l: x.append('<posttime>PT%sS</posttime>' % int(l))
    if m: x.append('<size_minimum>%d</size_minimum>' % m)
    if n: x.append('<size_multiple>%d</size_multiple>' % n)
    if q: x.append('<duration>PT%sS</duration>' % int(q))
    if r: x.append('<duration_per>PT%sS</duration_per>' % int(r))
    if s: x.append('<location name=%s/>' % quoteattr(s))
    x.append('</operation>')
  x.append('</operations></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
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
  cursor.execute("SELECT name, description, operation_id, owner_id FROM item")
  x = [ header, '<items>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    x.append('<item name=%s>' % quoteattr(i))
    if j: x.append( '<description>%s</description>' % escape(j))
    if k: x.append( '<operation name=%s/>' % quoteattr(k))
    if l: x.append( '<owner name=%s/>' % quoteattr(l))
    x.append('</item>')
  x.append('</items></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d items in %.2f seconds' % (cnt, time() - starttime)


def loadBuffers(cursor):
  print 'Importing buffers...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT name, description, location_id, item_id, onhand,
     minimum_id, producing_id, type, leadtime, min_inventory,
     max_inventory, min_interval, max_interval, size_minimum,
     size_multiple, size_maximum, fence FROM buffer''')
  x = [ header, '<buffers>' ]
  for i, j, k, l, m, n, o, q, f1, f2, f3, f4, f5, f6, f7, f8, f9 in cursor.fetchall():
    cnt += 1
    if q:
      x.append('<buffer name=%s xsi:type="%s">' % (quoteattr(i),q))
      if q == 'buffer_procure':
        if f1: x.append( '<leadtime>PT%sS</leadtime>' % int(f1))
        if f2: x.append( '<mininventory>%s</mininventory>' % f2)
        if f3: x.append( '<maxinventory>%s</maxinventory>' % f3)
        if f4: x.append( '<mininterval>PT%sS</mininterval>' % int(f4))
        if f5: x.append( '<maxinterval>PT%sS</maxinterval>' % int(f5))
        if f6: x.append( '<size_minimum>%s</size_minimum>' % f6)
        if f7: x.append( '<size_multiple>%s</size_multiple>' % f7)
        if f8: x.append( '<size_maximum>%s</size_maximum>' % f8)
        if f9: x.append( '<fence>PT%sS</fence>' % int(f9))
    else:
      x.append('<buffer name=%s>' % quoteattr(i))
    if j: x.append( '<description>%s</description>' % escape(j))
    if k: x.append( '<location name=%s />' % quoteattr(k))
    if l: x.append( '<item name=%s />' % quoteattr(l))
    if m: x.append( '<onhand>%s</onhand>' % m)
    if n: x.append( '<minimum name=%s />' % quoteattr(n))
    if o: x.append( '<producing name=%s />' % quoteattr(o))
    x.append('</buffer>')
  x.append('</buffers></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime)


def loadResources(cursor):
  print 'Importing resources...'
  cnt = 0
  starttime = time()
  cursor.execute('SELECT name, description, maximum_id, location_id, type FROM %s' % connection.ops.quote_name('resource'))
  x = [ header, '<resources>' ]
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    if m:
      x.append('<resource name=%s xsi:type="%s">' % (quoteattr(i),m))
    else:
      x.append('<resource name=%s>' % quoteattr(i))
    if j: x.append( '<description>%s</description>' % escape(j))
    if k: x.append( '<maximum name=%s />' % quoteattr(k))
    if l: x.append( '<location name=%s />' % quoteattr(l))
    x.append('</resource>')
  x.append('</resources></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
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
    SELECT operation_id, resource_id, usagefactor, effective_start, effective_end
    FROM resourceload
    ORDER BY operation_id, resource_id
    ''')
  x = [ header , '<loads>' ]
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    x.append('<load><operation name=%s/><resource name=%s/><usage>%s</usage>' % (quoteattr(i), quoteattr(j), k))
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
  x = [ header , '<operation_plans>' ]
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    x.append('<operation_plan id="%d" operation=%s quantity="%s">' % (i, quoteattr(j), k))
    if l: x.append( '<start>%s</start>' % l.isoformat())
    if m: x.append( '<end>%s</end>' % m.isoformat())
    if n: x.append( '<locked>true</locked>')
    x.append('</operation_plan>')
  x.append('</operation_plans></plan>')
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
  x = [ header, '<demands>' ]
  for i, j, k, l, m, n, o, p, q, r in cursor.fetchall():
    cnt += 1
    x.append('<demand name=%s due="%s" quantity="%s" priority="%d">' % (quoteattr(i), j.isoformat(), k, l))
    if m: x.append( '<item name=%s />' % quoteattr(m))
    if n: x.append( '<operation name=%s />' % quoteattr(n))
    if o: x.append( '<customer name=%s />' % quoteattr(o))
    if p: x.append( '<owner name=%s />' % quoteattr(p))
    if q: x.append( '<minshipment>%s</minshipment>' % q)
    if r != None: x.append( '<maxlateness>PT%sS</maxlateness>' % int(r))
    x.append('</demand>')
  x.append('</demands></plan>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
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
  global header
  cursor = connection.cursor()

  # Make sure the debug flag is not set!
  # When it is set, the django database wrapper collects a list of all sql
  # statements executed and their timings. This consumes plenty of memory
  # and cpu time.
  settings.DEBUG = False

  if True:
    # Sequential load of all entities
    loadPlan(cursor)
    loadLocations(cursor)
    loadCalendars(cursor)
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
      DatabaseTask(loadLocations),
      DatabaseTask(loadCalendars),
      DatabaseTask(loadCustomers),
      DatabaseTask(loadOperations,loadSuboperations),
      )
    for i in tasks: i.start()
    for i in tasks: i.join()
    loadItems(cursor)
    tasks = (
      DatabaseTask(loadBuffers,loadFlows),
      DatabaseTask(loadResources, loadLoads),
      DatabaseTask(loadForecast),
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
