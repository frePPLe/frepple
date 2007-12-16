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


# The code in this file is executed NOT by Django, but by the embedded Python
# interpreter from the frePPLe engine.
# It extracts the information fields from the database, and then uses Python
# to compose an XML string that is then processed by the C++ core engine.


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

header = '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'


def timeformat(i):
  if i>=3600 or i<=-3600:
      minsec = i % 3600
      return '%d:%02d:%02d' % (i/3600, minsec/60, minsec%60)
  elif i>=60 or i<=-60:
    return '%d:%02d' % (i/60, i%60)
  else:
    return '%d' % i


def loadPlan(cursor):
  # Plan (limited to the first one only)
  print 'Import plan...'
  x = [ header ]
  cursor.execute("SELECT currentdate, name, description FROM plan")
  d = cursor.fetchone()
  if not d: raise ValueError('Missing a record in the plan table')
  i, j, k = d
  x.append('<CURRENT>%s</CURRENT>' % i.isoformat())
  if j: x.append('<NAME>%s</NAME>' % escape(j))
  if k: x.append('<DESCRIPTION>%s</DESCRIPTION>' % escape(k))
  x.append('</PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)


def loadLocations(cursor):

  print 'Importing locations...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM location")
  x = [ header, '<LOCATIONS>' ]
  for i,j,k in cursor.fetchall():
    cnt += 1
    x.append(u'<LOCATION NAME=%s>' % quoteattr(i))
    if j: x.append(u'<DESCRIPTION>%s</DESCRIPTION>' % escape(j))
    if k: x.append(u'<OWNER NAME=%s/>' % quoteattr(k))
    x.append('</LOCATION>')
  x.append('</LOCATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d locations in %.2f seconds' % (cnt, time() - starttime)


def loadCalendars(cursor):
  print 'Importing calendars...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description FROM calendar")
  x = [ header ]
  x.append('<CALENDARS>')
  for i, j in cursor.fetchall():
    cnt += 1
    if j: x.append('<CALENDAR NAME=%s DESCRIPTION=%s/>' % (quoteattr(i), quoteattr(j)))
    else: x.append('<CALENDAR NAME=%s/>' % quoteattr(i))
  x.append('</CALENDARS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d calendars in %.2f seconds' % (cnt, time() - starttime)

  # Bucket
  print 'Importing buckets...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT calendar_id, startdate, name, value FROM bucket")
  x = [ header ]
  x.append('<CALENDARS>')
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    if k: x.append('<CALENDAR NAME=%s><BUCKETS><BUCKET START="%s" NAME=%s VALUE="%s"/></BUCKETS></CALENDAR>' % (quoteattr(i), j.isoformat(), quoteattr(k), l))
    else: x.append('<CALENDAR NAME=%s><BUCKETS><BUCKET START="%s" VALUE="%s"/></BUCKETS></CALENDAR>' % (quoteattr(i), j.isoformat(), l))
  x.append('</CALENDARS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime)


def loadCustomers(cursor):
  print 'Importing customers...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM customer")
  x = [ header, '<CUSTOMERS>' ]
  for i, j, k in cursor.fetchall():
    cnt += 1
    x.append('<CUSTOMER NAME=%s>' % quoteattr(i))
    if j: x.append('<DESCRIPTION>%s</DESCRIPTION>' % escape(j))
    if k: x.append('<OWNER NAME=%s/>' % quoteattr(k))
    x.append('</CUSTOMER>')
  x.append('</CUSTOMERS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d customers in %.2f seconds' % (cnt, time() - starttime)


def loadOperations(cursor):
  print 'Importing operations...'
  cnt = 0
  starttime = time()
  x = [ header, '<OPERATIONS>' ]
  cursor.execute('''
    SELECT name, fence, pretime, posttime, sizeminimum, sizemultiple, type, duration, duration_per
    FROM operation
    ''')
  for i, j, k, l, m, n, p, q, r in cursor.fetchall():
    cnt += 1
    if p:
      x.append('<OPERATION NAME=%s xsi:type="%s">' % (quoteattr(i),p))
    else:
      x.append('<OPERATION NAME=%s>' % quoteattr(i))
    if j: x.append('<FENCE>%s</FENCE>' % timeformat(j))
    if k: x.append('<PRETIME>%s</PRETIME>' % timeformat(k))
    if l: x.append('<POSTTIME>%s</POSTTIME>' % timeformat(l))
    if m: x.append('<SIZE_MINIMUM>%d</SIZE_MINIMUM>' % m)
    if n: x.append('<SIZE_MULTIPLE>%d</SIZE_MULTIPLE>' % n)
    if q: x.append('<DURATION>%s</DURATION>' % timeformat(q))
    if r: x.append('<DURATION_PER>%s</DURATION_PER>' % timeformat(r))
    x.append('</OPERATION>')
  x.append('</OPERATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d operations in %.2f seconds' % (cnt, time() - starttime)


def loadSuboperations(cursor):
  print 'Importing suboperations...'
  cnt = 0
  starttime = time()
  x = [ header, '<OPERATIONS>' ]
  cursor.execute('''
    SELECT operation_id, suboperation_id, priority
    FROM suboperation, operation
    WHERE suboperation.operation_id = operation.name
    AND operation.type = 'OPERATION_ALTERNATE'
    ORDER BY operation_id, priority
    ''')
  curoper = ''
  for i, j, k in cursor.fetchall():
    cnt += 1
    if i != curoper:
      if curoper != '': x.append('</OPERATION>')
      x.append('<OPERATION NAME=%s xsi:type="OPERATION_ALTERNATE">' % quoteattr(i))
      curoper = i
    x.append('<ALTERNATE PRIORITY="%s"><OPERATION NAME=%s/></ALTERNATE>' % (k,quoteattr(j)))
  if curoper != '': x.append('</OPERATION>')
  x.append('</OPERATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d suboperations in %.2f seconds' % (cnt, time() - starttime)


def loadItems(cursor):
  print 'Importing items...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, operation_id, owner_id FROM item")
  x = [ header, '<ITEMS>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    x.append('<ITEM NAME=%s>' % quoteattr(i))
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % escape(j))
    if k: x.append( '<OPERATION NAME=%s/>' % quoteattr(k))
    if l: x.append( '<OWNER NAME=%s/>' % quoteattr(l))
    x.append('</ITEM>')
  x.append('</ITEMS></PLAN>')
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
  x = [ header, '<BUFFERS>' ]
  for i, j, k, l, m, n, o, q, f1, f2, f3, f4, f5, f6, f7, f8, f9 in cursor.fetchall():
    cnt += 1
    if q:
      x.append('<BUFFER NAME=%s xsi:type="%s">' % (quoteattr(i),q))
      if q == 'BUFFER_PROCURE':
        if f1: x.append( '<LEADTIME>%s</LEADTIME>' % timeformat(f1))
        if f2: x.append( '<MININVENTORY>%s</MININVENTORY>' % f2)
        if f3: x.append( '<MAXINVENTORY>%s</MAXINVENTORY>' % f3)
        if f4: x.append( '<MININTERVAL>%s</MININTERVAL>' % timeformat(f4))
        if f5: x.append( '<MAXINTERVAL>%s</MAXINTERVAL>' % timeformat(f5))
        if f6: x.append( '<SIZE_MINIMUM>%s</SIZE_MINIMUM>' % f6)
        if f7: x.append( '<SIZE_MULTIPLE>%s</SIZE_MULTIPLE>' % f7)
        if f8: x.append( '<SIZE_MAXIMUM>%s</SIZE_MAXIMUM>' % f8)
        if f9: x.append( '<FENCE>%s</FENCE>' % timeformat(f9))
    else:
      x.append('<BUFFER NAME=%s>' % quoteattr(i))
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % escape(j))
    if k: x.append( '<LOCATION NAME=%s />' % quoteattr(k))
    if l: x.append( '<ITEM NAME=%s />' % quoteattr(l))
    if m: x.append( '<ONHAND>%s</ONHAND>' % m)
    if n: x.append( '<MINIMUM NAME=%s />' % quoteattr(n))
    if o: x.append( '<PRODUCING NAME=%s />' % quoteattr(o))
    x.append('</BUFFER>')
  x.append('</BUFFERS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime)


def loadResources(cursor):
  print 'Importing resources...'
  cnt = 0
  starttime = time()
  cursor.execute('SELECT name, description, maximum_id, location_id, type FROM %s' % connection.ops.quote_name('resource'))
  x = [ header, '<RESOURCES>' ]
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    if m:
      x.append('<RESOURCE NAME=%s xsi:type="%s">' % (quoteattr(i),m))
    else:
      x.append('<RESOURCE NAME=%s>' % quoteattr(i))
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % escape(j))
    if k: x.append( '<MAXIMUM NAME=%s />' % quoteattr(k))
    if l: x.append( '<LOCATION NAME=%s />' % quoteattr(l))
    x.append('</RESOURCE>')
  x.append('</RESOURCES></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d resources in %.2f seconds' % (cnt, time() - starttime)


def loadFlows(cursor):
  print 'Importing flows...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT operation_id, thebuffer_id, quantity, type FROM flow order by operation_id, thebuffer_id")
  x = [ header, '<FLOWS>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    if l:
      x.append('<FLOW xsi:type="%s"><OPERATION NAME=%s/><BUFFER NAME=%s/><QUANTITY>%s</QUANTITY></FLOW>' % (l, quoteattr(i), quoteattr(j), k))
    else:
      x.append('<FLOW><OPERATION NAME=%s/><BUFFER NAME=%s/><QUANTITY>%s</QUANTITY></FLOW>' % (quoteattr(i), quoteattr(j), k))
  x.append('</FLOWS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d flows in %.2f seconds' % (cnt, time() - starttime)


def loadLoads(cursor):
  print 'Importing loads...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT operation_id, resource_id, usagefactor FROM resourceload order by operation_id, resource_id")
  x = [ header , '<LOADS>' ]
  for i, j, k in cursor.fetchall():
    cnt += 1
    x.append('<LOAD><OPERATION NAME=%s/><RESOURCE NAME=%s/><USAGE>%s</USAGE></LOAD>' % (quoteattr(i), quoteattr(j), k))
  x.append('</LOADS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d loads in %.2f seconds' % (cnt, time() - starttime)


def loadOperationPlans(cursor):
  print 'Importing operationplans...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT identifier, operation_id, quantity, startdate, enddate, locked FROM operationplan order by identifier asc")
  x = [ header , '<OPERATION_PLANS>' ]
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    x.append('<OPERATION_PLAN ID="%d" OPERATION=%s QUANTITY="%s">' % (i, quoteattr(j), k))
    if l: x.append( '<START>%s</START>' % l.isoformat())
    if m: x.append( '<END>%s</END>' % m.isoformat())
    if n: x.append( '<LOCKED>true</LOCKED>')
    x.append('</OPERATION_PLAN>')
  x.append('</OPERATION_PLANS></PLAN>')
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
  x = [ header, '<DEMANDS>' ]
  for i, j, k, l, m, n, o, p, q in cursor.fetchall():
    cnt += 1
    x.append('<DEMAND NAME=%s xsi:type="DEMAND_FORECAST" PRIORITY="%d">' % (quoteattr(i), l))
    if j: x.append( '<CUSTOMER NAME=%s />' % quoteattr(j))
    if k: x.append( '<ITEM NAME=%s />' % quoteattr(k))
    if m: x.append( '<OPERATION NAME=%s />' % quoteattr(m))
    if n: x.append( '<MINSHIPMENT>%s</MINSHIPMENT>' % n)
    if o: x.append( '<CALENDAR NAME=%s />' % quoteattr(o))
    if not p: x.append( '<DISCRETE>false<DISCRETE>')
    if q != None: x.append( '<MAXLATENESS>%s</MAXLATENESS>' % timeformat(q))
    x.append('</DEMAND>')
  x.append('</DEMANDS></PLAN>')
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
  x = [ header, '<DEMANDS>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    x.append('<DEMAND NAME=%s><BUCKETS><BUCKET START="%sT00:00:00" END="%sT00:00:00" TOTAL="%s"/></BUCKETS></DEMAND>' % (quoteattr(i), j.isoformat(), k.isoformat(), l))
  x.append('</DEMANDS></PLAN>')
  frepple.readXMLdata('\n'.join(x).encode('utf-8','ignore'),False,False)
  print 'Loaded %d forecast demands in %.2f seconds' % (cnt, time() - starttime)


def loadDemand(cursor):
  print 'Importing demands...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, due, quantity, priority, item_id, operation_id, customer_id, owner_id, minshipment, maxlateness FROM demand")
  x = [ header, '<DEMANDS>' ]
  for i, j, k, l, m, n, o, p, q, r in cursor.fetchall():
    cnt += 1
    x.append('<DEMAND NAME=%s DUE="%s" QUANTITY="%s" PRIORITY="%d">' % (quoteattr(i), j.isoformat(), k, l))
    if m: x.append( '<ITEM NAME=%s />' % quoteattr(m))
    if n: x.append( '<OPERATION NAME=%s />' % quoteattr(n))
    if o: x.append( '<CUSTOMER NAME=%s />' % quoteattr(o))
    if p: x.append( '<OWNER NAME=%s />' % quoteattr(p))
    if q: x.append( '<MINSHIPMENT>%s</MINSHIPMENT>' % q)
    if r != None: x.append( '<MAXLATENESS>%s</MAXLATENESS>' % timeformat(r))
    x.append('</DEMAND>')
  x.append('</DEMANDS></PLAN>')
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
