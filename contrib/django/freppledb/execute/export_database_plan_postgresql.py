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


from datetime import timedelta, datetime, date
from time import time, sleep
from threading import Thread
import inspect, os
from subprocess import Popen, PIPE

from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings
from django.core.management.color import no_style

import frepple

if 'FREPPLE_DATABASE' in os.environ:
  database = os.environ['FREPPLE_DATABASE']
else:
  database = DEFAULT_DB_ALIAS


def truncate(process):
  print "Emptying database plan tables..."
  starttime = time()
  process.stdin.write('truncate table out_demandpegging;\n')
  process.stdin.write('truncate table out_problem, out_resourceplan, out_constraint;\n')
  process.stdin.write('truncate table out_loadplan, out_flowplan, out_operationplan;\n') 
  process.stdin.write('truncate table out_demand, out_forecast;\n')
  print "Emptied plan tables in %.2f seconds" % (time() - starttime)


def exportProblems(process):
  print "Exporting problems..."
  starttime = time()
  process.stdin.write('COPY out_problem (entity, name, owner, description, startdate, enddate, weight) FROM STDIN;\n')
  for i in frepple.problems(): 
    process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
       i.entity, i.name,
       isinstance(i.owner,frepple.operationplan) and str(i.owner.operation) or str(i.owner),
       i.description[0:settings.NAMESIZE+20], str(i.start), str(i.end),
       round(i.weight,settings.DECIMAL_PLACES)
    ))
  process.stdin.write('\\.\n')
  print 'Exported problems in %.2f seconds' % (time() - starttime)


def exportConstraints(process):
  print "Exporting constraints..."
  starttime = time()
  process.stdin.write('COPY out_constraint (demand,entity,name,owner,description,startdate,enddate,weight) FROM STDIN;\n')
  for d in frepple.demands():
    for i in d.constraints:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
         d.name,i.entity, i.name,
         isinstance(i.owner,frepple.operationplan) and str(i.owner.operation) or str(i.owner),
         i.description[0:settings.NAMESIZE+20], str(i.start), str(i.end),
         round(i.weight,settings.DECIMAL_PLACES)
       ))
  process.stdin.write('\\.\n')
  print 'Exported constraints in %.2f seconds' % (time() - starttime)


def exportOperationplans(process):
  print "Exporting operationplans..."
  starttime = time()
  process.stdin.write('COPY out_operationplan (id,operation,quantity,startdate,enddate,locked,unavailable,owner) FROM STDIN;\n')
  for i in frepple.operations():
    for j in i.operationplans:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
        j.id, i.name[0:settings.NAMESIZE],
        round(j.quantity,settings.DECIMAL_PLACES), str(j.start), str(j.end),
        j.locked, j.unavailable, j.owner and j.owner.id or "\\N"
        ))
  process.stdin.write('\\.\n')
  print 'Exported operationplans in %.2f seconds' % (time() - starttime)


def exportFlowplans(process):
  print "Exporting flowplans..."
  starttime = time()
  process.stdin.write('COPY out_flowplan (operationplan_id, thebuffer, quantity, flowdate, onhand) FROM STDIN;\n')
  for i in frepple.buffers():
    for j in i.flowplans:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\n" % (
         j.operationplan.id, j.buffer.name,
         round(j.quantity,settings.DECIMAL_PLACES),
         str(j.date), round(j.onhand,settings.DECIMAL_PLACES)
         ))
  process.stdin.write('\\.\n')
  print 'Exported flowplans in %.2f seconds' % (time() - starttime)


def exportLoadplans(process):
  print "Exporting loadplans..."
  starttime = time()
  process.stdin.write('COPY out_loadplan (operationplan_id, theresource, quantity, startdate, enddate, setup) FROM STDIN;\n')
  for i in frepple.resources():
    for j in i.loadplans:
      if j.quantity > 0:
        process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (
         j.operationplan.id, j.resource.name,
         round(j.quantity,settings.DECIMAL_PLACES),
         str(j.startdate), str(j.enddate), j.setup
       ))
  process.stdin.write('\\.\n')
  print 'Exported loadplans in %.2f seconds' % (time() - starttime)


def exportResourceplans(process):
  print "Exporting resourceplans..."
  starttime = time()
  
  # Determine start and end date of the reporting horizon
  # The start date is computed as 5 weeks before the start of the earliest loadplan in 
  # the entire plan.
  # The end date is computed as 5 weeks after the end of the latest loadplan in 
  # the entire plan.
  # If no loadplans exist at all we use the current date +- 1 month.
  startdate = datetime.max
  enddate = datetime.min
  for i in frepple.resources():
    for j in i.loadplans:
      if j.startdate < startdate: startdate = j.startdate
      if j.enddate > enddate: enddate = j.enddate
  if startdate == datetime.max: startdate = frepple.settings.current 
  if enddate == datetime.min: enddate = frepple.settings.current
  startdate -= timedelta(days=30)
  enddate += timedelta(days=30)
    
  # Build a list of horizon buckets
  buckets = []
  while startdate < enddate:
    buckets.append(startdate)
    startdate += timedelta(days=1)
  
  # Loop over all reporting buckets of all resources
  process.stdin.write('COPY out_resourceplan (theresource,startdate,available,unavailable,setup,load,free) FROM STDIN;\n')
  for i in frepple.resources():
	for j in i.plan(buckets):
	  process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
		 i.name, str(j['start']),
		 round(j['available'],settings.DECIMAL_PLACES),
		 round(j['unavailable'],settings.DECIMAL_PLACES),
		 round(j['setup'],settings.DECIMAL_PLACES),
		 round(j['load'],settings.DECIMAL_PLACES),
		 round(j['free'],settings.DECIMAL_PLACES)           
	   ))
  process.stdin.write('\\.\n')
  print 'Exported resourceplans in %.2f seconds' % (time() - starttime)


def exportDemand(process):

  def deliveries(d):
    cumplanned = 0
    n = d and d.name or 'unspecified'
    # Loop over all delivery operationplans
    for i in d.operationplans:
      cumplanned += i.quantity
      cur = i.quantity
      if cumplanned > d.quantity:
        cur -= cumplanned - d.quantity
        if cur < 0: cur = 0
      yield (
        n, d.item.name, d.customer and d.customer.name or None, str(d.due),
        round(cur,settings.DECIMAL_PLACES), str(i.end),
        round(i.quantity,settings.DECIMAL_PLACES), i.id
        )
    # Extra record if planned short
    if cumplanned < d.quantity:
      yield (
        n, d.item.name, d.customer and d.customer.name or None, str(d.due),
        round(d.quantity - cumplanned,settings.DECIMAL_PLACES), "\\N",
        "\\N", "\\N"
        )

  print "Exporting demand plans..."
  starttime = time()
  process.stdin.write('COPY out_demand (demand,item,customer,due,quantity,plandate,planquantity,operationplan) FROM STDIN;\n')
  for i in frepple.demands():
    if i.quantity == 0: continue
    for j in deliveries(i):
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % j)
  process.stdin.write('\\.\n')
  print 'Exported demand plans in %.2f seconds' % (time() - starttime)


def exportPegging(process):
  print "Exporting pegging..."
  starttime = time()
  process.stdin.write('COPY out_demandpegging (demand,depth,cons_operationplan,cons_date,prod_operationplan,prod_date, buffer,item,quantity_demand,quantity_buffer) FROM STDIN;\n')
  for i in frepple.demands():
    # Find non-hidden demand owner
    n = i
    while n.hidden and n.owner: n = n.owner
    n = n and n.name or 'unspecified'
    # Export pegging
    for j in i.pegging:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
        n, str(j.level),
        j.consuming and j.consuming.id or '0', str(j.consuming_date),
        j.producing and j.producing.id or '0', str(j.producing_date),
        j.buffer and j.buffer.name or '',
        (j.buffer and j.buffer.item and j.buffer.item.name) or '',
        round(j.quantity_demand,settings.DECIMAL_PLACES),
        round(j.quantity_buffer,settings.DECIMAL_PLACES)
       ))
  process.stdin.write('\\.\n')
  print 'Exported pegging in %.2f seconds' % (time() - starttime)


def exportForecast(process):
  # Detect whether the forecast module is available
  if not 'demand_forecast' in [ a[0] for a in inspect.getmembers(frepple) ]:
    return

  print "Exporting forecast plans..."
  starttime = time()
  process.stdin.write('COPY out_forecast (forecast,startdate,enddate,total,net,consumed) FROM STDIN;\n')
  for i in frepple.demands():
    if not isinstance(i, frepple.demand_forecastbucket) or i.total <= 0.0:
      continue
    process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (
         i.owner.name, str(i.startdate), str(i.enddate),
         round(i.total,settings.DECIMAL_PLACES),
         round(i.quantity,settings.DECIMAL_PLACES),
         round(i.consumed,settings.DECIMAL_PLACES)
       ))
  process.stdin.write('\\.\n')
  print 'Exported forecast plans in %.2f seconds' % (time() - starttime)


def exportfrepple():
  '''
  This function exports the data from the frePPLe memory into the database.
  '''
  test = 'FREPPLE_TEST' in os.environ  

  # Start a PSQL process
  process = Popen("psql -q -U%s %s%s%s" % (
      settings.DATABASES[database]['USER'],
     settings.DATABASES[database]['HOST'] and ("-h %s " % settings.DATABASES[database]['HOST']) or '',
     settings.DATABASES[database]['PORT'] and ("-p %s " % settings.DATABASES[database]['PORT']) or '',
     test and settings.DATABASES[database]['TEST_NAME'] or settings.DATABASES[database]['NAME'],
   ), stdin=PIPE, stderr=PIPE, bufsize=0, universal_newlines=True)  
  
  # Send all output to the PSQL process through a pipe
  try:
    truncate(process)
    exportProblems(process)
    exportConstraints(process)
    exportOperationplans(process)
    exportFlowplans(process)
    exportLoadplans(process)
    exportResourceplans(process)
    exportDemand(process)
    exportPegging(process)
    exportForecast(process)
  finally:
    # Close the pipe and PSQL process
    process.stdin.write('\\q\n')
    process.stdin.close()
    # Collect error messages
    print process.communicate()[1]
  
  cursor = connections[database].cursor()
  cursor.execute('''
    select 'out_problem', count(*) from out_problem 
    union select 'out_constraint', count(*) from out_constraint 
    union select 'out_operationplan', count(*) from out_operationplan 
    union select 'out_flowplan', count(*) from out_flowplan 
    union select 'out_loadplan', count(*) from out_loadplan 
    union select 'out_resourceplan', count(*) from out_resourceplan
    union select 'out_forecast', count(*) from out_forecast
    union select 'out_demandpegging', count(*) from out_demandpegging 
    union select 'out_demand', count(*) from out_demand
    order by 1
    ''')	 
  for table, recs in cursor.fetchall():
    print "Table %s: %d records" % (table, recs)

