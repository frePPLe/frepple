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

from freppledb.input.models import *
from freppledb.output.models import *
from datetime import datetime
from django.db import connection
from os import times

dateformat = '%Y-%m-%dT%H:%M:%S'
header = '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'

def timeformat(int):
  if int>=3600 or int<=-3600:
      minsec = l % 3600
      return '%d:%02d:%02d' % (int/3600, minsec/60, minsec%60)
  elif int>=60 or int<=-60:
    return '%d:%02d' % (int/60, int%60)
  else:
    return '%d' % int


def dumpfrepple():
  '''
  This function exports the data from the frepple memory into the
  database.
  '''
  print "Emptying database plan tables..."
  cursor = connection.cursor()
  cursor.connection.autocommit(True)
  starttime = times()[4]
  cursor.execute('delete from frepple.output_problem')
  cursor.execute('delete from frepple.output_operationplan')
  print "Emptied plan tables in %.2f seconds" % (times()[4] - starttime)

  print "Exporting problems..."
  cnt = 0
  sql = []
  first = True
  starttime = times()[4]
  for i in frepple.iterator():
     # The Django api to create objects is fine but it is soooo much slower
     # than the direct database API...
     #prob = Problem(name=j, description=i, start=strptime(k), end=strptime(l))
     #prob.save()
     if first:
        sql.append("insert into frepple.output_problem (name,description,start,end) values('%s','%s','%s','%s')" %
           (i['type'], i['description'].replace("'","''"), i['start'], i['end']))
        first = False
     else:
        sql.append(",('%s','%s','%s','%s')" % (i['type'], i['description'].replace("'","''"), i['start'], i['end']))
     cnt += 1
     if cnt % 5000 == 0: 
       cursor.execute(' '.join(sql))
       sql = []
       first = True
  if not first: cursor.execute(' '.join(sql))
  print 'Exported %d problems in %.2f seconds' % (cnt, times()[4] - starttime)

  print "Exporting operationplans..."
  cnt = 0
  starttime = times()[4]
  sql = []
  first = True
  for i in frepple.operationplan():
     if first:   
        sql.append("insert into frepple.output_operationplan (identifier, operation_id,quantity,start,end) values (%s ,'%s' ,%s ,'%s' ,'%s')" % 
           (i['identifier'], i['operation'].replace("'","''"), i['quantity'], i['start'], i['end']))
        first = False
     else:
        sql.append(",(%s ,'%s' ,%s ,'%s' ,'%s')" % 
            (i['identifier'], i['operation'].replace("'","''"), i['quantity'], i['start'], i['end']))
     cnt += 1
     if cnt % 5000 == 0: 
       cursor.execute(' '.join(sql))
       sql = []
       first = True
  if not first: cursor.execute(' '.join(sql))
  print 'Exported %d operationplans in %.2f seconds' % (cnt, times()[4] - starttime)


def loadfrepple():
  '''
  This function is expected to be run by the python interpreter in the
  frepple application.
  It loads data from the database into the frepple memory.
  '''
  global dateformat
  global header
  cursor = connection.cursor()

  # Plan (limited to the first one only)
  print 'Import plan...'
  x = [ header ]
  cursor.execute("SELECT current, name, description FROM frepple.input_plan")
  i, j, k = cursor.fetchone()
  x.append('<CURRENT>%s</CURRENT>' % i.strftime(dateformat))
  if j: x.append('<NAME>%s</NAME>' % j)
  if k: x.append('<DESCRIPTION>%s</DESCRIPTION>' % k)
  x.append('</PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Locations
  print 'Importing locations...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, owner_id FROM frepple.input_location")
  x = [ header, '<LOCATIONS>' ]
  for i,j,k in cursor.fetchall():
    cnt += 1
    x.append('<LOCATION NAME="%s">"' % i)
    if j: x.append('<DESCRIPTION>%s</DESCRIPTION>"' % j)
    if k: x.append('<OWNER NAME="%s"/>"' % k)
    x.append('</LOCATION>"')
  x.append('</LOCATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d locations in %.2f seconds' % (cnt, times()[4] - starttime)

  # Calendar
  print 'Importing calendars...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description FROM frepple.input_calendar")
  x = [ header ]
  x.append('<CALENDARS>')
  for i, j in cursor.fetchall():
    cnt += 1
    if j: x.append('<CALENDAR NAME="%s" DESCRIPTION="%s"/>' % (i, j))
    else: x.append('<CALENDAR NAME="%s"/>' % i)
  x.append('</CALENDARS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d calendars in %.2f seconds' % (cnt, times()[4] - starttime)

  # Bucket
  print 'Importing buckets...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT calendar_id, start, name, value FROM frepple.input_bucket")
  x = [ header ]
  x.append('<CALENDARS>')
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    if k: x.append('<CALENDAR NAME="%s"><BUCKETS><BUCKET START="%s" NAME="%s" VALUE="%s"/></BUCKETS></CALENDAR>' % (i, j, k, l))
    else: x.append('<CALENDAR NAME="%s"><BUCKETS><BUCKET START="%s" VALUE="%s"/></BUCKETS></CALENDAR>' % (i, j, l))
  x.append('</CALENDARS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, times()[4] - starttime)

  # Customers
  print 'Importing customers...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, owner_id FROM frepple.input_customer")
  x = [ header, '<CUSTOMERS>' ]
  for i, j, k in cursor.fetchall():
    cnt += 1
    x.append('<CUSTOMER NAME="%s">' % i)
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % j)
    if k: x.append( '<OWNER NAME="%s"/>' % k)
    x.append('</CUSTOMER>')
  x.append('</CUSTOMERS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d customers in %.2f seconds' % (cnt, times()[4] - starttime)

  # Operations
  print 'Importing operations...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, fence, pretime, posttime, sizeminimum, sizemultiple, owner_id FROM frepple.input_operation")
  x = [ header, '<OPERATIONS>' ]
  for i, j, k, l, m, n, o in cursor.fetchall():
    cnt += 1
    x.append('<OPERATION NAME="%s">' % i)
    if j: x.append( '<FENCE>%s</FENCE>' % timeformat(j))
    if k: x.append( '<PRETIME>%f</PRETIME>' % k)
    if l: x.append( '<POSTTIME>%f</POSTTIME>' % l)
    if m: x.append( '<SIZE_MINIMUM>%d</SIZE_MINIMUM>' % m)
    if n: x.append( '<SIZE_MULTIPLE>%d</SIZE_MULTIPLE>' % n)
    if o: x.append( '<OWNER NAME="%s"/>' % o)
    x.append('</OPERATION>')
  x.append('</OPERATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d operations in %.2f seconds' % (cnt, times()[4] - starttime)

  # Items
  print 'Importing items...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, operation_id, owner_id FROM frepple.input_item")
  x = [ header, '<ITEMS>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    x.append('<ITEM NAME="%s">' % i)
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % j)
    if k: x.append( '<OPERATION NAME="%s"/>' % k)
    if l: x.append( '<OWNER NAME="%s"/>' % l)
    x.append('</ITEM>')
  x.append('</ITEMS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d items in %.2f seconds' % (cnt, times()[4] - starttime)

  # Buffers
  print 'Importing buffers...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, location_id, item_id, onhand, minimum_id, producing_id, consuming_id, type FROM frepple.input_buffer")
  x = [ header, '<BUFFERS>' ]
  for i, j, k, l, m, n, o, p, q in cursor.fetchall():
    cnt += 1
    if q:
      x.append('<BUFFER NAME="%s" xsi:type="%s">' % (i,q))
    else:
      x.append('<BUFFER NAME="%s">' % i)
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % j)
    if k: x.append( '<LOCATION NAME="%s" />' % k)
    if l: x.append( '<ITEM NAME="%s" />' % l)
    if m: x.append( '<ONHAND>%s</ONHAND>' % m)
    if n: x.append( '<MINIMUM NAME="%s" />' % n)
    if o: x.append( '<PRODUCING NAME="%s" />' % o)
    if p: x.append( '<CONSUMING NAME="%s" />' % p)
    x.append('</BUFFER>')
  x.append('</BUFFERS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d buffers in %.2f seconds' % (cnt, times()[4] - starttime)

  # Resources
  print 'Importing resources...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, maximum_id, location_id, type FROM frepple.input_resource")
  x = [ header, '<RESOURCES>' ]
  for i, j, k, l, m in cursor.fetchall():
    cnt += 1
    if m:
      x.append('<RESOURCE NAME="%s" xsi:type="%s">' % (i,m))
    else:
      x.append('<RESOURCE NAME="%s">' % i)
    if j: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % j)
    if k: x.append( '<MAXIMUM NAME="%s" />' % k)
    if l: x.append( '<LOCATION NAME="%s" />' % l)
    x.append('</RESOURCE>')
  x.append('</RESOURCES></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d resources in %.2f seconds' % (cnt, times()[4] - starttime)

  # Flows
  print 'Importing flows...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT operation_id, thebuffer_id, quantity, type FROM frepple.input_flow")
  x = [ header, '<FLOWS>' ]
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    if l:
      x.append('<FLOW xsi:type="%s"><OPERATION NAME="%s"/><BUFFER NAME="%s"/><QUANTITY>%s</QUANTITY></FLOW>' % (l, i, j, k))
    else:
      x.append('<FLOW><OPERATION NAME="%s"/><BUFFER NAME="%s"/><QUANTITY>%s</QUANTITY></FLOW>' % (i, j, k))
  x.append('</FLOWS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d flows in %.2f seconds' % (cnt, times()[4] - starttime)

  # Loads
  print 'Importing loads...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT operation_id, resource_id, usagefactor FROM frepple.input_load")
  x = [ header , '<LOADS>' ]
  for i, j, k in cursor.fetchall():
    cnt += 1
    x.append('<LOAD><OPERATION NAME="%s"/><RESOURCE NAME="%s"/><USAGE>%s</USAGE></LOAD>' % (i, j, k))
  x.append('</LOADS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d loads in %.2f seconds' % (cnt, times()[4] - starttime)

  # OperationPlan
  print 'Importing operationplans...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT identifier, operation_id, quantity, start, end, locked FROM frepple.input_operationplan order by identifier asc")
  x = [ header , '<OPERATION_PLANS>' ]
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    x.append('<OPERATION_PLAN ID="%d" OPERATION="%s" QUANTITY="%s">' % (i, j, k))
    if l: x.append( '<START>%s</START>' % l.strftime(dateformat))
    if m: x.append( '<START>%s</START>' % m.strftime(dateformat))
    if n: x.append( '<LOCKED>true</LOCKED>')
    x.append('</OPERATION_PLAN>')
  x.append('</OPERATION_PLANS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d operationplans in %.2f seconds' % (cnt, times()[4] - starttime)

  # Demand
  cursor.execute("SELECT name, due, quantity, priority, item_id, operation_id, customer_id, owner_id FROM frepple.input_demand")
  cnt = 0
  starttime = times()[4]
  print 'Importing demands...'
  x = [ header, '<DEMANDS>' ]
  for i, j, k, l, m, n, o, p in cursor.fetchall():
    cnt += 1
    x.append('<DEMAND NAME="%s" DUE="%s" QUANTITY="%s" PRIORITY="%d">' % (i, j.strftime(dateformat), k, l))
    if m: x.append( '<ITEM NAME="%s" />' % m)
    if n: x.append( '<OPERATION NAME="%s" />' % n)
    if o: x.append( '<CUSTOMER NAME="%s" />' % o)
    if p: x.append( '<OWNER NAME="%s" />' % p)
    x.append('</DEMAND>')
  x.append('</DEMANDS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d demands in %.2f seconds' % (cnt, times()[4] - starttime)

  # Finalize
  print 'Done'
  cursor.close()
