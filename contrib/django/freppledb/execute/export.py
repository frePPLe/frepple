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

from datetime import datetime
from os import times
from django.db import connection
from django.db import transaction

import frepple
from freppledb.input.models import *
from freppledb.output.models import *

header = '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'

def timeformat(i):
  if i>=3600 or i<=-3600:
      minsec = i % 3600
      return '%d:%02d:%02d' % (i/3600, minsec/60, minsec%60)
  elif i>=60 or i<=-60:
    return '%d:%02d' % (i/60, i%60)
  else:
    return '%d' % i


@transaction.commit_manually
def dumpfrepple():
  '''
  This function exports the data from the frepple memory into the database.
  '''
  print "Emptying database plan tables..."
  cursor = connection.cursor()
  starttime = times()[4]
  cursor.execute('delete from output_problem')
  transaction.commit()
  cursor.execute('delete from output_flowplan')
  transaction.commit()
  cursor.execute('delete from output_loadplan')
  transaction.commit()
  cursor.execute('delete from output_operationplan')
  transaction.commit()
  print "Emptied plan tables in %.2f seconds" % (times()[4] - starttime)

  print "Exporting problems..."
  starttime = times()[4]
  cursor.executemany(
    "insert into output_problem (entity,name,description,startdatetime,enddatetime,startdate,enddate) values(%s,%s,%s,%s,%s,%s,%s)",
    [ (i['ENTITY'], i['TYPE'], i['DESCRIPTION'], str(i['START']), str(i['END']), str(i['START']), str(i['END'])) for i in frepple.problem() ]
    )
  transaction.commit()
  cursor.execute("select count(*) from output_problem")
  print 'Exported %d problems in %.2f seconds' % (cursor.fetchone()[0], times()[4] - starttime)

  print "Exporting operationplans..."
  starttime = times()[4]
  cursor.executemany(
    "insert into output_operationplan (identifier,operation_id,quantity,startdatetime,enddatetime,startdate,enddate,demand_id,locked) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
    [ (i['IDENTIFIER'], i['OPERATION'].replace("'","''"), i['QUANTITY'], str(i['START']), str(i['END']), str(i['START']), str(i['END']), i['DEMAND'], str(i['LOCKED'])) for i in frepple.operationplan() ]
    )
  transaction.commit()
  cursor.execute("select count(*) from output_operationplan")
  print 'Exported %d operationplans in %.2f seconds' % (cursor.fetchone()[0], times()[4] - starttime)

  print "Exporting flowplans..."
  starttime = times()[4]
  for i in frepple.buffer():
    cursor.executemany(
      "insert into output_flowplan (operationplan_id,operation_id,thebuffer_id,quantity,date,datetime,onhand) values (%s,%s,%s,%s,%s,%s,%s)",
      [ (j['OPERATIONPLAN'], j['OPERATION'], j['BUFFER'], j['QUANTITY'], str(j['DATE']), str(j['DATE']), j['ONHAND']) for j in i['FLOWPLANS'] ]
      )
  transaction.commit()
  cursor.execute("select count(*) from output_flowplan")
  print 'Exported %d flowplans in %.2f seconds' % (cursor.fetchone()[0], times()[4] - starttime)

  print "Exporting loadplans..."
  starttime = times()[4]
  for i in frepple.resource():
    cursor.executemany(
      "insert into output_loadplan (operationplan_id,operation_id,resource_id,quantity,date,datetime,onhand,maximum) values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [ (j['OPERATIONPLAN'], j['OPERATION'], j['RESOURCE'], j['QUANTITY'], str(j['DATE']), str(j['DATE']), j['ONHAND'], j['MAXIMUM']) for j in i['LOADPLANS'] ]
      )
  transaction.commit()
  cursor.execute("select count(*) from output_loadplan")
  print 'Exported %d loadplans in %.2f seconds' % (cursor.fetchone()[0], times()[4] - starttime)


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
  cursor.execute("SELECT current, name, description FROM input_plan")
  d = cursor.fetchone()
  if not d: raise ValueError('Missing a record in the plan table')
  i, j, k = d
  x.append('<CURRENT>%s</CURRENT>' % i.isoformat())
  if j: x.append('<NAME>%s</NAME>' % j)
  if k: x.append('<DESCRIPTION>%s</DESCRIPTION>' % k)
  x.append('</PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Locations
  print 'Importing locations...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, owner_id FROM input_location")
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
  cursor.execute("SELECT name, description FROM input_calendar")
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
  cursor.execute("SELECT calendar_id, startdate, name, value FROM input_bucket")
  x = [ header ]
  x.append('<CALENDARS>')
  for i, j, k, l in cursor.fetchall():
    cnt += 1
    if k: x.append('<CALENDAR NAME="%s"><BUCKETS><BUCKET START="%s" NAME="%s" VALUE="%s"/></BUCKETS></CALENDAR>' % (i, j.isoformat(), k, l))
    else: x.append('<CALENDAR NAME="%s"><BUCKETS><BUCKET START="%s" VALUE="%s"/></BUCKETS></CALENDAR>' % (i, j.isoformat(), l))
  x.append('</CALENDARS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d calendar buckets in %.2f seconds' % (cnt, times()[4] - starttime)

  # Customers
  print 'Importing customers...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, owner_id FROM input_customer")
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
  x = [ header, '<OPERATIONS>' ]
  cursor.execute('''
    SELECT name, fence, pretime, posttime, sizeminimum, sizemultiple, type, duration, duration_per
    FROM input_operation
    ''')
  for i, j, k, l, m, n, p, q, r in cursor.fetchall():
    cnt += 1
    if p:
      x.append('<OPERATION NAME="%s" xsi:type="%s">' % (i,p))
    else:
      x.append('<OPERATION NAME="%s">' % i)
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
  print 'Loaded %d operations in %.2f seconds' % (cnt, times()[4] - starttime)

  # Suboperations
  print 'Importing suboperations...'
  cnt = 0
  starttime = times()[4]
  x = [ header, '<OPERATIONS>' ]
  cursor.execute('''
    SELECT operation_id, suboperation_id, priority
    FROM input_suboperation, input_operation
    WHERE input_suboperation.operation_id = input_operation.name
    AND input_operation.type = 'OPERATION_ALTERNATE'
    ORDER BY operation_id, priority
    ''')
  curoper = ''
  for i, j, k in cursor.fetchall():
    cnt += 1
    if i != curoper:
      if curoper != '': x.append('</OPERATION>')
      x.append('<OPERATION NAME="%s" xsi:type="OPERATION_ALTERNATE">' % i)
      curoper = i
    x.append('<ALTERNATE PRIORITY="%s"><OPERATION NAME="%s"/></ALTERNATE>' % (k,j))
  if curoper != '': x.append('</OPERATION>')
  x.append('</OPERATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d suboperations in %.2f seconds' % (cnt, times()[4] - starttime)

  # Items
  print 'Importing items...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, operation_id, owner_id FROM input_item")
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
  cursor.execute("SELECT name, description, location_id, item_id, onhand, minimum_id, producing_id, type FROM input_buffer")
  x = [ header, '<BUFFERS>' ]
  for i, j, k, l, m, n, o, q in cursor.fetchall():
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
    x.append('</BUFFER>')
  x.append('</BUFFERS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d buffers in %.2f seconds' % (cnt, times()[4] - starttime)

  # Resources
  print 'Importing resources...'
  cnt = 0
  starttime = times()[4]
  cursor.execute("SELECT name, description, maximum_id, location_id, type FROM input_resource")
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
  cursor.execute("SELECT operation_id, thebuffer_id, quantity, type FROM input_flow")
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
  cursor.execute("SELECT operation_id, resource_id, usagefactor FROM input_load")
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
  cursor.execute("SELECT identifier, operation_id, quantity, startdate, enddate, locked FROM input_operationplan order by identifier asc")
  x = [ header , '<OPERATION_PLANS>' ]
  for i, j, k, l, m, n in cursor.fetchall():
    cnt += 1
    x.append('<OPERATION_PLAN ID="%d" OPERATION="%s" QUANTITY="%s">' % (i, j, k))
    if l: x.append( '<START>%s</START>' % l.isoformat())
    if m: x.append( '<END>%s</END>' % m.isoformat())
    if n: x.append( '<LOCKED>true</LOCKED>')
    x.append('</OPERATION_PLAN>')
  x.append('</OPERATION_PLANS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d operationplans in %.2f seconds' % (cnt, times()[4] - starttime)

  # Demand
  cursor.execute("SELECT name, due, quantity, priority, item_id, operation_id, customer_id, owner_id, policy FROM input_demand")
  cnt = 0
  starttime = times()[4]
  print 'Importing demands...'
  x = [ header, '<DEMANDS>' ]
  for i, j, k, l, m, n, o, p, q in cursor.fetchall():
    cnt += 1
    x.append('<DEMAND NAME="%s" DUE="%s" QUANTITY="%s" PRIORITY="%d">' % (i, j.isoformat(), k, l))
    if m: x.append( '<ITEM NAME="%s" />' % m)
    if n: x.append( '<OPERATION NAME="%s" />' % n)
    if o: x.append( '<CUSTOMER NAME="%s" />' % o)
    if p: x.append( '<OWNER NAME="%s" />' % p)
    if q: x.append( '<POLICY>%s</POLICY>' % q)
    x.append('</DEMAND>')
  x.append('</DEMANDS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  print 'Loaded %d demands in %.2f seconds' % (cnt, times()[4] - starttime)

  # Finalize
  print 'Done'
  cursor.close()
