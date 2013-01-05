#
# Copyright (C) 2011-2012 by Johan De Taeye, frePPLe bvba
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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
Exports frePPLe information into a database.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

The code iterates over all objects in the C++ core engine, and creates
database records with the information. The Django database wrappers are used
to keep the code portable between different databases.
'''


from datetime import datetime
from time import time
from threading import Thread
import inspect, os

from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings

import frepple

if 'FREPPLE_DATABASE' in os.environ:
  database = os.environ['FREPPLE_DATABASE']
else:
  database = DEFAULT_DB_ALIAS

timestamp = str(datetime.now())


def exportLocations(cursor):
  print "Exporting locations..."  
  starttime = time()
  cursor.execute("SELECT name FROM location")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    "insert into location \
    (name,description,available_id,category,subcategory,lastmodified) \
    values(%s,%s,%s,%s,%s,%s)",
    [(
       i.name, i.description, i.available and i.available.name or None, i.category, i.subcategory, timestamp
     ) for i in frepple.locations() if i.name not in primary_keys
    ])
  cursor.executemany(
    "update location \
     set description=%s, available_id=%s, category=%s, subcategory=%s, lastmodified=%s \
     where name=%s",
    [(
       i.description, i.available and i.available.name or None, i.category, i.subcategory, timestamp, i.name
     ) for i in frepple.locations() if i.name in primary_keys
    ])
  cursor.executemany(
    "update location set owner_id=%s where name=%s",
    [(
       i.owner.name, i.name
     ) for i in frepple.locations() if i.owner 
    ])
  transaction.commit(using=database)
  print 'Exported locations in %.2f seconds' % (time() - starttime)


def exportCalendars(cursor): 
  print "Exporting calendars..."  
  starttime = time()
  cursor.execute("SELECT name FROM calendar")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    "insert into calendar \
    (name,defaultvalue,lastmodified) \
    values(%s,%s,%s)",
    [(
       i.name, round(i.default,settings.DECIMAL_PLACES), timestamp
     ) for i in frepple.calendars() if i.name not in primary_keys
    ])
  cursor.executemany(
    "update calendar \
     set defaultvalue=%s, lastmodified=%s \
     where name=%s",
    [(
       round(i.default,settings.DECIMAL_PLACES), timestamp, i.name
     ) for i in frepple.calendars() if i.name in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported calendars in %.2f seconds' % (time() - starttime)


def exportCalendarBuckets(cursor):
  print "Exporting calendar buckets..."  
  starttime = time()
  cursor.execute("SELECT calendar_id, id FROM calendarbucket")
  primary_keys = set([ i for i in cursor.fetchall() ]) 
  
  def buckets():
    for c in frepple.calendars():
      for i in c.buckets:
        yield i
       
  cursor.executemany(
    '''insert into calendarbucket
    (calendar_id,startdate,enddate,id,priority,value,
     monday,tuesday,wednesday,thursday,friday,saturday,sunday,
     starttime,endtime,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.calendar.name, str(i.start), str(i.end), i.id, i.priority, 
       round(i.value,settings.DECIMAL_PLACES), 
       (i.days & 1) and True or False, (i.days & 2) and True or False, (i.days & 4) and True or False,
       (i.days & 8) and True or False, (i.days & 16) and True or False, (i.days & 32) and True or False,
       (i.days & 64) and True or False, i.starttime, i.endtime, timestamp 
      ) for i in buckets() if (i.calendar.name, i.id) not in primary_keys 
    ])
  cursor.executemany(
    '''update calendarbucket 
     set enddate=%s, startdate=%s, priority=%s, value=%s, lastmodified=%s,
     sunday=%s, monday=%s, tuesday=%s, wednesday=%s, thursday=%s, friday=%s, saturday=%s,  
     starttime=%s, endtime=%s 
     where calendar_id=%s and id=%s''',
    [(
       str(i.end), str(i.start), i.priority, 
       round(i.value,settings.DECIMAL_PLACES), timestamp,
       (i.days & 1) and True or False, (i.days & 2) and True or False, (i.days & 4) and True or False,
       (i.days & 8) and True or False, (i.days & 16) and True or False, (i.days & 32) and True or False,
       (i.days & 64) and True or False, i.starttime, i.endtime, 
       i.calendar.name, i.id  
     ) for i in buckets() if (i.calendar.name, i.id) in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported calendar buckets in %.2f seconds' % (time() - starttime)    

  
def exportOperations(cursor):
  print "Exporting operations..."  
  starttime = time()
  cursor.execute("SELECT name FROM operation")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])  
  cursor.executemany(
    '''insert into operation
    (name,fence,pretime,posttime,sizeminimum,sizemultiple,sizemaximum,type,duration,
     duration_per,location_id,cost,search,description,category,subcategory,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.name, i.fence, i.pretime, i.posttime, round(i.size_minimum,settings.DECIMAL_PLACES),
       round(i.size_multiple,settings.DECIMAL_PLACES), 
       i.size_maximum<9999999999999 and round(i.size_maximum,settings.DECIMAL_PLACES) or None,
       i.__class__.__name__[10:], 
       isinstance(i,(frepple.operation_fixed_time,frepple.operation_time_per)) and i.duration or None,
       isinstance(i,frepple.operation_time_per) and i.duration_per or None,
       i.location and i.location.name or None, round(i.cost,settings.DECIMAL_PLACES),
       isinstance(i,frepple.operation_alternate) and i.search or None, 
       i.description, i.category, i.subcategory, timestamp 
      ) for i in frepple.operations() if i.name not in primary_keys and not i.hidden and i.name != 'setup operation'
    ])
  cursor.executemany(
    '''update operation 
     set fence=%s, pretime=%s, posttime=%s, sizeminimum=%s, sizemultiple=%s, 
     sizemaximum=%s, type=%s, duration=%s, duration_per=%s, location_id=%s, cost=%s, search=%s, 
     description=%s, category=%s, subcategory=%s, lastmodified=%s 
     where name=%s''',
    [(
       i.fence, i.pretime, i.posttime, round(i.size_minimum,settings.DECIMAL_PLACES),
       round(i.size_multiple,settings.DECIMAL_PLACES), 
       i.size_maximum<9999999999999 and round(i.size_maximum,settings.DECIMAL_PLACES) or None,
       i.__class__.__name__[10:],
       isinstance(i,(frepple.operation_fixed_time,frepple.operation_time_per)) and i.duration or None,
       isinstance(i,frepple.operation_time_per) and i.duration_per or None,
       i.location and i.location.name or None, round(i.cost,settings.DECIMAL_PLACES),
       isinstance(i,frepple.operation_alternate) and i.search or None, 
       i.description, i.category, i.subcategory, timestamp, i.name 
     ) for i in frepple.operations() if i.name in primary_keys and not i.hidden and i.name != 'setup operation'
    ])
  transaction.commit(using=database)
  print 'Exported operations in %.2f seconds' % (time() - starttime)
  

def exportSubOperations(cursor): 
  return # TODO
  print "Exporting suboperations..."  
  starttime = time()
  cursor.execute("SELECT operation_id, suboperation_id FROM suboperation")
  primary_keys = set([ i for i in cursor.fetchall() ])
  
  def subops():
    for i in frepple.operations():
      if isinstance(i,frepple.operation_alternate):
        for j in i.alternates:
          yield i, j
      if isinstance(i, frepple.operation_routing):
        for j in i.steps:    
          yield i, j
          
  for x in subops():
    print x
    
  cursor.executemany(
    "insert into suboperation \
    (operation_id,suboperation_id,priority,effective_start,effective_end,lastmodified) \
    values(%s,%s,%s,%s,%s,%s)",
    [(
       i[0].name, i[1].name, i[1].priority, i[1].effective_start, i[1].effective_end, timestamp
     ) for i in subops() if i not in primary_keys
    ])
  cursor.executemany(
    "update suboperation \
     set priority=%s, effective_start=%s, effective_end=%s, lastmodified=%s \
     where operation_id=%s and suboperation_id=%s",
    [(
       i[1].priority, i[1].effective_start, i[1].effective_end, timestamp, i[0].name, i[1].name
     ) for i in subops() if i in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported suboperations in %.2f seconds' % (time() - starttime)  


def exportFlows(cursor):
  print "Exporting flows..."  
  starttime = time()
  cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
  primary_keys = set([ i for i in cursor.fetchall() ]) 
  
  def flows():
    for o in frepple.operations():
      for i in o.flows:
        yield i
       
  cursor.executemany(
    '''insert into flow
    (operation_id,thebuffer_id,quantity,type,effective_start,effective_end,name,priority,
    search,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.operation.name, i.buffer.name, round(i.quantity,settings.DECIMAL_PLACES),
       i.__class__.__name__[5:], str(i.effective_start), str(i.effective_end), 
       i.name, i.priority, i.search != 'PRIORITY' and i.search or None, timestamp 
      ) for i in flows() if (i.operation.name, i.buffer.name) not in primary_keys and not i.hidden 
    ])
  cursor.executemany(
    '''update flow 
     set quantity=%s, type=%s, effective_start=%s, effective_end=%s, name=%s, 
     priority=%s, search=%s, lastmodified=%s 
     where operation_id=%s and thebuffer_id=%s''',
    [(
       round(i.quantity,settings.DECIMAL_PLACES),
       i.__class__.__name__[5:], str(i.effective_start), str(i.effective_end), 
       i.name, i.priority, i.search != 'PRIORITY' and i.search or None, timestamp, 
       i.operation.name, i.buffer.name, 
     ) for i in flows() if (i.operation.name, i.buffer.name) in primary_keys and not i.hidden
    ])
  transaction.commit(using=database)
  print 'Exported flows in %.2f seconds' % (time() - starttime)
  
  
def exportLoads(cursor): 
  print "Exporting loads..."  
  starttime = time()
  cursor.execute("SELECT operation_id, resource_id FROM resourceload")
  primary_keys = set([ i for i in cursor.fetchall() ]) 
  
  def loads():
    for o in frepple.operations():
      for i in o.loads:
        yield i
       
  cursor.executemany(
    '''insert into resourceload
    (operation_id,resource_id,quantity,setup,effective_start,effective_end,name,priority,
    search,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.operation.name, i.resource.name, round(i.quantity,settings.DECIMAL_PLACES),
       i.setup, str(i.effective_start), str(i.effective_end), 
       i.name, i.priority, i.search != 'PRIORITY' and i.search or None, timestamp 
      ) for i in loads() if (i.operation.name, i.resource.name) not in primary_keys and not i.hidden 
    ])
  cursor.executemany(
    '''update resourceload 
     set quantity=%s, setup=%s, effective_start=%s, effective_end=%s, name=%s, 
     priority=%s, search=%s, lastmodified=%s 
     where operation_id=%s and resource_id=%s''',
    [(
       round(i.quantity,settings.DECIMAL_PLACES),
       i.setup, str(i.effective_start), str(i.effective_end), 
       i.name, i.priority, i.search != 'PRIORITY' and i.search or None, timestamp, 
       i.operation.name, i.resource.name, 
     ) for i in loads() if (i.operation.name, i.resource.name) in primary_keys and not i.hidden
    ])
  transaction.commit(using=database)
  print 'Exported loads in %.2f seconds' % (time() - starttime)


def exportBuffers(cursor): 
  print "Exporting buffers..."  
  starttime = time()
  cursor.execute("SELECT name FROM buffer")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])  
  cursor.executemany(
    '''insert into buffer
    (name,description,location_id,item_id,onhand,minimum,minimum_calendar_id,
     producing_id,type,leadtime,min_inventory,
     max_inventory,min_interval,max_interval,size_minimum,
     size_multiple,size_maximum,fence,
     carrying_cost,category,subcategory,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.name, i.description, i.location and i.location.name or None, 
       i.item and i.item.name or None, 
       round(i.onhand,settings.DECIMAL_PLACES), round(i.minimum,settings.DECIMAL_PLACES), 
       i.minimum_calendar and i.minimum_calendar.name or None,
       i.producing and i.producing.name or None, i.__class__.__name__[7:], 
       isinstance(i,frepple.buffer_procure) and i.leadtime or None, 
       isinstance(i,frepple.buffer_procure) and round(i.mininventory,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and round(i.maxinventory,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and i.mininterval or None,
       isinstance(i,frepple.buffer_procure) and i.maxinterval or None,
       isinstance(i,frepple.buffer_procure) and round(i.size_minimum,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and round(i.size_multiple,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and i.size_maximum<9999999999999 and round(i.size_maximum,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and i.fence or None,       
       round(i.carrying_cost,settings.DECIMAL_PLACES), i.category, i.subcategory, timestamp 
      ) for i in frepple.buffers() if i.name not in primary_keys and not i.hidden 
    ])
  cursor.executemany(
    '''update buffer 
     set description=%s, location_id=%s, item_id=%s, onhand=%s, minimum=%s, minimum_calendar_id=%s,
     producing_id=%s, type=%s, leadtime=%s, min_inventory=%s, max_inventory=%s, min_interval=%s,
     max_interval=%s, size_minimum=%s, size_multiple=%s, size_maximum=%s, fence=%s,
     carrying_cost=%s, category=%s, subcategory=%s, lastmodified=%s 
     where name=%s''',
    [(
       i.description, i.location and i.location.name or None, i.item and i.item.name or None, 
       round(i.onhand,settings.DECIMAL_PLACES), round(i.minimum,settings.DECIMAL_PLACES), 
       i.minimum_calendar and i.minimum_calendar.name or None,
       i.producing and i.producing.name or None, i.__class__.__name__[7:], 
       isinstance(i,frepple.buffer_procure) and i.leadtime or None, 
       isinstance(i,frepple.buffer_procure) and round(i.mininventory,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and round(i.maxinventory,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and i.mininterval or None,
       isinstance(i,frepple.buffer_procure) and i.maxinterval or None,
       isinstance(i,frepple.buffer_procure) and round(i.size_minimum,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and round(i.size_multiple,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and round(i.size_maximum,settings.DECIMAL_PLACES) or None, 
       isinstance(i,frepple.buffer_procure) and i.fence or None,       
       round(i.carrying_cost,settings.DECIMAL_PLACES), i.category, i.subcategory, timestamp, i.name  
     ) for i in frepple.buffers() if i.name in primary_keys and not i.hidden
    ])
  cursor.executemany(
    "update buffer set owner_id=%s where name=%s",
    [(
       i.owner.name, i.name
     ) for i in frepple.buffers() if i.owner and not i.hidden
    ])
  transaction.commit(using=database)
  print 'Exported buffers in %.2f seconds' % (time() - starttime)

def exportCustomers(cursor): 
  print "Exporting customers..."  
  starttime = time()
  cursor.execute("SELECT name FROM customer")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    "insert into customer \
    (name,description,category,subcategory,lastmodified) \
    values(%s,%s,%s,%s,%s)",
    [(
       i.name, i.description, i.category, i.subcategory, timestamp
     ) for i in frepple.customers() if i.name not in primary_keys
    ])
  cursor.executemany(
    "update customer \
     set description=%s, category=%s, subcategory=%s, lastmodified=%s \
     where name=%s",
    [(
       i.description, i.category, i.subcategory, timestamp, i.name
     ) for i in frepple.customers() if i.name in primary_keys
    ])
  cursor.executemany(
    "update customer set owner_id=%s where name=%s",
    [(
       i.owner.name, i.name
     ) for i in frepple.customers() if i.owner 
    ])
  transaction.commit(using=database)
  print 'Exported customers in %.2f seconds' % (time() - starttime)
  
  
def exportDemands(cursor):
  print "Exporting demands..."  
  starttime = time()
  cursor.execute("SELECT name FROM demand")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    '''insert into demand 
    (name,due,quantity,priority,item_id,operation_id,customer_id, 
     minshipment,maxlateness,category,subcategory,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.name, str(i.due), round(i.quantity,settings.DECIMAL_PLACES), i.priority, i.item.name, 
       i.operation and i.operation.name or None, i.customer and i.customer.name or None, 
       round(i.minshipment,settings.DECIMAL_PLACES), round(i.maxlateness,settings.DECIMAL_PLACES), 
       i.category, i.subcategory, timestamp
     ) for i in frepple.demands() 
     if i.name not in primary_keys and isinstance(i,frepple.demand_default) and not i.hidden
    ])
  cursor.executemany(
    '''update demand 
     set due=%s, quantity=%s, priority=%s, item_id=%s, operation_id=%s, customer_id=%s, 
     minshipment=%s, maxlateness=%s, category=%s, subcategory=%s, lastmodified=%s 
     where name=%s''',
    [(
       str(i.due), round(i.quantity,settings.DECIMAL_PLACES), i.priority, i.item.name, 
       i.operation and i.operation.name or None, i.customer and i.customer.name or None, 
       round(i.minshipment,settings.DECIMAL_PLACES), round(i.maxlateness,settings.DECIMAL_PLACES), 
       i.category, i.subcategory, timestamp, i.name
     ) for i in frepple.demands() 
     if i.name in primary_keys and isinstance(i,frepple.demand_default) and not i.hidden
    ])
  cursor.executemany(
    "update demand set owner_id=%s where name=%s",
    [(
       i.owner.name, i.name
     ) for i in frepple.demands() if i.owner and isinstance(i,frepple.demand_default)
    ])
  transaction.commit(using=database)
  print 'Exported demands in %.2f seconds' % (time() - starttime) 


def exportForecasts(cursor): 
  # Detect whether the forecast module is available
  if not 'demand_forecast' in [ a[0] for a in inspect.getmembers(frepple) ]:
    return 
  print "Exporting forecast..."  
  starttime = time()
  cursor.execute("SELECT name FROM forecast")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    '''insert into forecast 
    (name,customer_id,item_id,priority,operation_id,minshipment,
     calendar_id,discrete,maxlateness,category,subcategory,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.name, i.customer and i.customer.name or None, i.item.name, i.priority, 
       i.operation and i.operation.name or None, round(i.minshipment,settings.DECIMAL_PLACES), 
       i.calendar.name, i.discrete, round(i.maxlateness,settings.DECIMAL_PLACES), 
       i.category, i.subcategory, timestamp
     ) for i in frepple.demands() if i.name not in primary_keys and isinstance(i,frepple.demand_forecast)
    ])
  cursor.executemany(
    '''update forecast 
     set customer_id=%s, item_id=%s, priority=%s, operation_id=%s, minshipment=%s,
     calendar_id=%s, discrete=%s,maxlateness=%s, category=%s, subcategory=%s, lastmodified=%s 
     where name=%s''',
    [(
       i.customer and i.customer.name or None, i.item.name, i.priority, 
       i.operation and i.operation.name or None, round(i.minshipment,settings.DECIMAL_PLACES), 
       i.calendar.name, i.discrete, round(i.maxlateness,settings.DECIMAL_PLACES), 
       i.category, i.subcategory, timestamp, i.name, 
     ) for i in frepple.demands() if i.name in primary_keys and isinstance(i,frepple.demand_forecast)
    ])
  transaction.commit(using=database)
  print 'Exported forecasts in %.2f seconds' % (time() - starttime) 
  

def exportForecastDemands(cursor): 
  # Detect whether the forecast module is available
  if not 'demand_forecast' in [ a[0] for a in inspect.getmembers(frepple) ]:
    return
  print "Exporting forecast demands..."  
  starttime = time()
  cursor.execute("SELECT forecast_id, startdate, enddate FROM forecastdemand")
  primary_keys = set([ i for i in cursor.fetchall() ])
  cursor.executemany(
    '''insert into forecastdemand 
    (forecast_id,startdate,enddate,quantity,lastmodified) 
    values(%s,%s,%s,%s,%s)''',
    [(
       i.owner.name, str(i.startdate.date()), str(i.enddate.date()), 
       round(i.total,settings.DECIMAL_PLACES), timestamp
     ) for i in frepple.demands() if isinstance(i,frepple.demand_forecastbucket) and (i.owner.name,i.startdate.date(),i.enddate.date()) not in primary_keys
    ])
  cursor.executemany(
    '''update forecastdemand 
     set quantity=%s, lastmodified=%s
     where forecast_id=%s and startdate=%s and enddate=%s''',
    [(
       round(i.total,settings.DECIMAL_PLACES), timestamp, 
       i.owner.name, str(i.startdate.date()), str(i.enddate.date()), 
     ) for i in frepple.demands() if isinstance(i,frepple.demand_forecastbucket) and (i.owner.name,i.startdate.date(),i.enddate.date()) in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported forecast demands in %.2f seconds' % (time() - starttime) 
  

def exportOperationPlans(cursor): 
  '''
  Only locked operationplans are exported. That because we assume that
  all of those were given as input. 
  '''
  print "Exporting operationplans..."  
  starttime = time()
  cursor.execute("SELECT id FROM operationplan")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    '''insert into operationplan
    (id,operation_id,quantity,startdate,enddate,locked,lastmodified) 
    values(%s,%s,%s,%s,%s,%s,%s)''',
    [(
       i.id, i.operation.name, round(i.quantity,settings.DECIMAL_PLACES), 
       str(i.start), str(i.end), i.locked, timestamp
     ) for i in frepple.operationplans() 
     if i.locked and not i.operation.hidden and i.id not in primary_keys
    ])
  cursor.executemany(
    '''update operationplan 
     set operation_id=%s, quantity=%s, startdate=%s, enddate=%s, locked=%s, lastmodified=%s 
     where id=%s''',
    [(
       i.operation.name, round(i.quantity,settings.DECIMAL_PLACES), 
       str(i.start), str(i.end), i.locked, timestamp, i.id
     ) for i in frepple.operationplans() 
     if i.locked and not i.operation.hidden and i.id in primary_keys
    ])
  cursor.executemany(
    "update operationplan set owner_id=%s where id=%s",
    [(
       i.owner.id, i.id
     ) for i in frepple.operationplans() if i.owner and not i.operation.hidden and i.locked
    ])
  transaction.commit(using=database)
  print 'Exported operationplans in %.2f seconds' % (time() - starttime) 

    
def exportResources(cursor): 
  print "Exporting resources..."  
  starttime = time()
  cursor.execute("SELECT name FROM %s" % connections[database].ops.quote_name('resource'))
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    '''insert into %s
    (name,description,maximum,maximum_calendar_id,location_id,type,cost,
     maxearly,setup,setupmatrix_id,category,subcategory,lastmodified)
    values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)''' % connections[database].ops.quote_name('resource'),
    [(
       i.name, i.description, i.maximum, i.maximum_calendar and i.maximum_calendar.name or None, 
       i.location and i.location.name or None, i.__class__.__name__[9:], 
       round(i.cost,settings.DECIMAL_PLACES), round(i.maxearly,settings.DECIMAL_PLACES),
       i.setup, i.setupmatrix and i.setupmatrix.name or None, 
       i.category, i.subcategory, timestamp
     ) for i in frepple.resources() 
     if i.name not in primary_keys and not i.hidden
    ])
  cursor.executemany(
    '''update %s \
     set description=%%s, maximum=%%s, maximum_calendar_id=%%s, location_id=%%s, 
     type=%%s, cost=%%s, maxearly=%%s, setup=%%s, setupmatrix_id=%%s, category=%%s, 
     subcategory=%%s, lastmodified=%%s
     where name=%%s''' % connections[database].ops.quote_name('resource'),
    [(
       i.description, i.maximum, i.maximum_calendar and i.maximum_calendar.name or None, 
       i.location and i.location.name or None, i.__class__.__name__[9:], 
       round(i.cost,settings.DECIMAL_PLACES), round(i.maxearly,settings.DECIMAL_PLACES),
       i.setup, i.setupmatrix and i.setupmatrix.name or None, 
       i.category, i.subcategory, timestamp, i.name 
     ) for i in frepple.resources() 
     if i.name in primary_keys and not i.hidden
    ])
  cursor.executemany(
    "update %s set owner_id=%%s where name=%%s" % connections[database].ops.quote_name('resource'),
    [(
       i.owner.name, i.name
     ) for i in frepple.resources() if i.owner and not i.hidden
    ])
  transaction.commit(using=database)
  print 'Exported resources in %.2f seconds' % (time() - starttime)


def exportSkills(cursor): 
  print "Exporting skills..."  
  starttime = time()
  cursor.execute("SELECT name FROM skill")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    '''insert into skill (name,lastmodified) values(%s,%s)''',
    [( i.name, timestamp ) for i in frepple.skills() 
     if i.name not in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported skills in %.2f seconds' % (time() - starttime)


def exportResourceSkills(cursor):
  print "Exporting resource skills..."  
  starttime = time()
  cursor.execute("SELECT resource_id, skill_id FROM resourceskill")
  primary_keys = set([ i for i in cursor.fetchall() ]) 
  
  def res_skills():
    for s in frepple.skills():
      for r in s.resources:
        yield (r.name, s.name)
       
  cursor.executemany(
    '''insert into resourceskill
    (resource_id,skill_id,lastmodified) 
    values(%s,%s,%s)''',
    [(
       i[0], i[1], timestamp 
      ) for i in res_skills() if i not in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported resource skills in %.2f seconds' % (time() - starttime)
    

def exportSetupMatrices(cursor): 
  print "Exporting setup matrices..."  
  starttime = time()
  cursor.execute("SELECT name FROM setupmatrix")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    "insert into setupmatrix \
    (name,lastmodified) \
    values(%s,%s)",
    [(
       i.name, timestamp
     ) for i in frepple.setupmatrices() if i.name not in primary_keys
    ])
  cursor.executemany(
    "update setupmatrix \
     set lastmodified=%s \
     where name=%s",
    [(
       timestamp, i.name
     ) for i in frepple.setupmatrices() if i.name in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported setupmatrices in %.2f seconds' % (time() - starttime)


def exportSetupMatricesRules(cursor): 
  print "Exporting setup matrix rules..."  
  starttime = time()
  cursor.execute("SELECT setupmatrix_id, priority FROM setuprule")
  primary_keys = set([ i for i in cursor.fetchall() ])
  
  def matrixrules():
    for m in frepple.setupmatrices():
      for i in m.rules:
        yield m, i
        
  cursor.executemany(
    "insert into setuprule \
    (setupmatrix_id,priority,fromsetup,tosetup,duration,cost,lastmodified) \
    values(%s,%s,%s,%s,%s,%s,%s)",
    [(
       i[0].name, i[1].priority, i[1].fromsetup, i[1].tosetup, i[1].duration, 
       round(i[1].cost,settings.DECIMAL_PLACES), timestamp 
     ) for i in matrixrules() if (i[0].name,i[1].priority) not in primary_keys
    ])
  cursor.executemany(
    "update setuprule \
     set fromsetup=%s, tosetup=%s, duration=%s, cost=%s, lastmodified=%s \
     where setupmatrix_id=%s and priority=%s",
    [(
       i[1].fromsetup, i[1].tosetup, i[1].duration, round(i[1].cost,settings.DECIMAL_PLACES), 
       timestamp, i[0].name, i[1].priority 
     ) for i[1] in matrixrules() if (i[0].name,i[1].priority) in primary_keys
    ])
  transaction.commit(using=database)
  print 'Exported setup matrix rules in %.2f seconds' % (time() - starttime)


def exportItems(cursor):
  print "Exporting items..."  
  starttime = time()
  cursor.execute("SELECT name FROM item")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  cursor.executemany(
    "insert into item \
    (name,description,operation_id,price,category,subcategory,lastmodified) \
    values(%s,%s,%s,%s,%s,%s,%s)",
    [(
       i.name, i.description, i.operation and i.operation.name or None, 
       round(i.price,settings.DECIMAL_PLACES), i.category, i.subcategory, timestamp
     ) for i in frepple.items() if i.name not in primary_keys
    ])
  cursor.executemany(
    "update item \
     set description=%s, operation_id=%s, price=%s, category=%s, subcategory=%s, lastmodified=%s \
     where name=%s",
    [(
       i.description, i.operation and i.operation.name or None, 
       round(i.price,settings.DECIMAL_PLACES), i.category, i.subcategory, timestamp, i.name
     ) for i in frepple.items() if i.name in primary_keys
    ])
  cursor.executemany(
    "update item set owner_id=%s where name=%s",
    [(
       i.owner.name, i.name
     ) for i in frepple.items() if i.owner 
    ])
  transaction.commit(using=database)
  print 'Exported items in %.2f seconds' % (time() - starttime)


def exportParameters(cursor):
  print "Exporting parameters..."  
  starttime = time()
  cursor.execute("SELECT name FROM common_parameter")
  primary_keys = set([ i[0] for i in cursor.fetchall() ])
  data = [      
    ('currentdate', frepple.settings.current.strftime("%Y-%m-%d %H:%M:%S")),
    ]
  cursor.executemany(
    "INSERT INTO common_parameter (name,value,lastmodified) VALUES (%s,%s,%s)",
    [ (i[0],i[1],timestamp) for i in data if i[0] not in primary_keys ]
    )
  cursor.executemany(
    "UPDATE common_parameter SET value=%s, lastmodified=%s WHERE name=%s",
    [ (i[1],timestamp,i[0]) for i in data if i[0] in primary_keys ]
    )
  transaction.commit(using=database)
  print 'Exported parameters in %.2f seconds' % (time() - starttime)


class DatabaseTask(Thread):
  '''
  An auxiliary class that allows us to run a function with its own
  database connection in its own thread.
  '''
  def __init__(self, *f):
    super(DatabaseTask, self).__init__()
    self.functions = f

  @transaction.commit_manually(using=database)
  def run(self):
    # Create a database connection
    cursor = connections[database].cursor()
    if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
      cursor.execute('PRAGMA temp_store = MEMORY;')
      cursor.execute('PRAGMA synchronous = OFF')
      cursor.execute('PRAGMA cache_size = 8000')
    elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.oracle':
      cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")

    # Run the functions sequentially
    for f in self.functions:
      try: f(cursor)
      except Exception as e: print e

    # Close the connection
    cursor.close()
    transaction.commit(using=database)


@transaction.commit_manually(using=database)
def exportfrepple():
  '''
  This function exports the data from the frePPLe memory into the database.
  '''
  # Make sure the debug flag is not set!
  # When it is set, the django database wrapper collects a list of all sql
  # statements executed and their timings. This consumes plenty of memory
  # and cpu time.
  settings.DEBUG = False
  global timestamp 
  timestamp = str(datetime.now())
  
  # Create a database connection
  cursor = connections[database].cursor()
  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
    cursor.execute('PRAGMA temp_store = MEMORY;')
    cursor.execute('PRAGMA synchronous = OFF')
    cursor.execute('PRAGMA cache_size = 8000')
  elif settings.DATABASES[database]['ENGINE'] == 'oracle':
    cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")

  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
    # OPTION 1: Sequential export of each entity
    # For SQLite this is required since a writer blocks the database file.
    # For other databases the parallel export normally gives a better
    # performance, but you could still choose a sequential export.
    try:
      exportParameters(cursor)
      exportCalendars(cursor)
      exportCalendarBuckets(cursor)
      exportLocations(cursor)
      exportOperations(cursor)
      exportSubOperations(cursor)
      exportOperationPlans(cursor)
      exportItems(cursor)
      exportBuffers(cursor)
      exportFlows(cursor)
      exportSetupMatrices(cursor)
      exportSetupMatricesRules(cursor)
      exportResources(cursor)
      exportSkills(cursor)
      exportResourceSkills(cursor)
      exportLoads(cursor)
      exportCustomers(cursor)
      exportDemands(cursor)
      exportForecasts(cursor)
      exportForecastDemands(cursor)
    except Exception as e:
      print e

  else:
    # OPTION 2: Parallel export of entities in groups.
    # The groups are running in separate threads, and all functions in a group
    # are run in sequence.
    try:
      exportCalendars(cursor)
      exportLocations(cursor)
      exportOperations(cursor)
      exportItems(cursor)
      tasks = (
        DatabaseTask(exportCalendarBuckets, exportSubOperations, exportOperationPlans, exportParameters),
        DatabaseTask(exportBuffers, exportFlows),
        DatabaseTask(exportSetupMatrices, exportSetupMatricesRules, exportResources, exportSkills, exportResourceSkills, exportLoads),
        DatabaseTask(exportCustomers, exportDemands, exportForecasts, exportForecastDemands),
        )
      # Start all threads
      for i in tasks: i.start()
      # Wait for all threads to finish
      for i in tasks: i.join()
    except Exception as e:
      print e

  # Analyze
  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
    print "Analyzing database tables..."
    cursor.execute("analyze")

  # Close the database connection
  cursor.close()
  transaction.commit(using=database)
