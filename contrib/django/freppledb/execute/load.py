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
# email : jdetaeye@users.sourceforge.net

from time import time
from xml.sax.saxutils import quoteattr, escape
from django.db import connection
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


def loadfrepple():
  '''
  This function is expected to be run by the python interpreter in the
  frepple application.
  It loads data from the database into the frepple memory.
  '''
  global header
  cursor = connection.cursor()

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
  frepple.readXMLdata('\n'.join(x),False,False)

  # Locations
  print 'Importing locations...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, owner_id FROM location")
  x = [ header, '<LOCATIONS>' ]
  for i,j,k in cursor.fetchall():
    cnt += 1
    x.append('<LOCATION NAME=%s>"' % quoteattr(i))
    if j: x.append('<DESCRIPTION>%s</DESCRIPTION>"' % escape(j))
    if k: x.append('<OWNER NAME=%s/>"' % quoteattr(k))
    x.append('</LOCATION>"')
  x.append('</LOCATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d locations in %.2f seconds' % (cnt, time() - starttime)

  # Calendar
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
  frepple.readXMLdata('\n'.join(x),False,False)
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, time() - starttime)

  # Customers
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d customers in %.2f seconds' % (cnt, time() - starttime)

  # Operations
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d operations in %.2f seconds' % (cnt, time() - starttime)

  # Suboperations
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d suboperations in %.2f seconds' % (cnt, time() - starttime)

  # Items
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d items in %.2f seconds' % (cnt, time() - starttime)

  # Buffers
  print 'Importing buffers...'
  cnt = 0
  starttime = time()
  cursor.execute('''SELECT name, description, location_id, item_id, onhand,
     minimum_id, producing_id, type, leadtime, min_inventory,
     max_inventory, min_interval, max_interval, size_minimum,
     size_multiple, size_maximum FROM buffer''')
  x = [ header, '<BUFFERS>' ]
  for i, j, k, l, m, n, o, q, f1, f2, f3, f4, f5, f6, f7, f8 in cursor.fetchall():
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d buffers in %.2f seconds' % (cnt, time() - starttime)

  # Resources
  print 'Importing resources...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT name, description, maximum_id, location_id, type FROM resource")
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d resources in %.2f seconds' % (cnt, time() - starttime)

  # Flows
  print 'Importing flows...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT operation_id, thebuffer_id, quantity, type FROM flow")
  x = [ header, '<FLOWS>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    if l:
      x.append('<FLOW xsi:type="%s"><OPERATION NAME=%s/><BUFFER NAME=%s/><QUANTITY>%s</QUANTITY></FLOW>' % (l, quoteattr(i), quoteattr(j), k))
    else:
      x.append('<FLOW><OPERATION NAME=%s/><BUFFER NAME=%s/><QUANTITY>%s</QUANTITY></FLOW>' % (quoteattr(i), quoteattr(j), k))
  x.append('</FLOWS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d flows in %.2f seconds' % (cnt, time() - starttime)

  # Loads
  print 'Importing loads...'
  cnt = 0
  starttime = time()
  cursor.execute("SELECT operation_id, resource_id, usagefactor FROM resourceload")
  x = [ header , '<LOADS>' ]
  for i, j, k in cursor.fetchall():
    cnt += 1
    x.append('<LOAD><OPERATION NAME=%s/><RESOURCE NAME=%s/><USAGE>%s</USAGE></LOAD>' % (quoteattr(i), quoteattr(j), k))
  x.append('</LOADS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d loads in %.2f seconds' % (cnt, time() - starttime)

  # OperationPlan
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
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d operationplans in %.2f seconds' % (cnt, time() - starttime)

  # Demand
  cursor.execute("SELECT name, due, quantity, priority, item_id, operation_id, customer_id, owner_id, policy FROM demand")
  cnt = 0
  starttime = time()
  print 'Importing demands...'
  x = [ header, '<DEMANDS>' ]
  for i, j, k, l, m, n, o, p, q in cursor.fetchall():
    cnt += 1
    x.append('<DEMAND NAME=%s DUE="%s" QUANTITY="%s" PRIORITY="%d">' % (quoteattr(i), j.isoformat(), k, l))
    if m: x.append( '<ITEM NAME=%s />' % quoteattr(m))
    if n: x.append( '<OPERATION NAME=%s />' % quoteattr(n))
    if o: x.append( '<CUSTOMER NAME=%s />' % quoteattr(o))
    if p: x.append( '<OWNER NAME=%s />' % quoteattr(p))
    if q: x.append( '<POLICY>%s</POLICY>' % q)
    x.append('</DEMAND>')
  x.append('</DEMANDS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d demands in %.2f seconds' % (cnt, time() - starttime)

  # Finalize
  print 'Done'
  cursor.close()
