#
# Copyright (C) 2007-2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
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


from time import time
from threading import Thread
import inspect, os

from django.db import connections, DEFAULT_DB_ALIAS
from django.db import transaction
from django.conf import settings

import frepple

if 'FREPPLE_DATABASE' in os.environ: 
  database = os.environ['FREPPLE_DATABASE']
else:
  database = DEFAULT_DB_ALIAS


def truncate(cursor):
  print "Emptying database plan tables..."
  starttime = time()
  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.postgresql_psycopg2': 
    delete = "truncate table %s cascade"
  elif settings.DATABASES[database]['ENGINE'] == 'django.db.backends.mysql':
    delete = "truncate table %s"
  else:
    delete = "delete from %s"
  for table in ['out_problem', 'out_demandpegging', 'out_operationplan', 
                'out_flowplan', 'out_loadplan', 'out_demand', 'out_forecast',
                'out_constraint', 
               ]:
    cursor.execute(delete % table)
    transaction.commit(using=database)
  print "Emptied plan tables in %.2f seconds" % (time() - starttime)


def exportProblems(cursor):
  print "Exporting problems..."
  starttime = time()
  cursor.executemany(
    "insert into out_problem \
    (entity,name,owner,description,startdate,enddate,weight) \
    values(%s,%s,%s,%s,%s,%s,%s)",
    [(
       i.entity, i.name, 
       isinstance(i.owner,frepple.operationplan) and str(i.owner.operation) or str(i.owner), 
       i.description[0:settings.NAMESIZE+20], str(i.start), str(i.end),
       round(i.weight,settings.DECIMAL_PLACES)
     ) for i in frepple.problems()
    ])
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_problem")
  print 'Exported %d problems in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportConstraints(cursor):
  print "Exporting constraints..."
  starttime = time()
  cnt = 0
  for d in frepple.demands():
    cursor.executemany(
      "insert into out_constraint \
      (demand,entity,name,owner,description,startdate,enddate,weight) \
      values(%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         d.name,i.entity, i.name, 
         isinstance(i.owner,frepple.operationplan) and str(i.owner.operation) or str(i.owner), 
         i.description[0:settings.NAMESIZE+20], str(i.start), str(i.end),
         round(i.weight,settings.DECIMAL_PLACES)
       ) for i in d.constraints
      ])
    cnt += 1
    if cnt % 300 == 0: transaction.commit(using=database)
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_constraint")
  print 'Exported %d constraints in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportOperationplans(cursor):
  print "Exporting operationplans..."
  starttime = time()
  cnt = 0
  for i in frepple.operations():
    cursor.executemany(
      "insert into out_operationplan \
       (id,operation,quantity,startdate,enddate,locked,unavailable,owner) \
       values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
        j.id, i.name.replace("'","''"),
        round(j.quantity,settings.DECIMAL_PLACES), str(j.start), str(j.end),
        j.locked, j.unavailable, j.owner and j.owner.id or None
       ) for j in i.operationplans ])
    cnt += 1
    if cnt % 300 == 0: transaction.commit(using=database)
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_operationplan")
  print 'Exported %d operationplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportFlowplans(cursor):
  print "Exporting flowplans..."
  starttime = time()
  cnt = 0
  for i in frepple.buffers():
    cursor.executemany(
      "insert into out_flowplan \
      (operationplan_id, thebuffer, quantity, flowdate, onhand) \
      values (%s,%s,%s,%s,%s)",
      [(
         j.operationplan.id, j.buffer.name, 
         round(j.quantity,settings.DECIMAL_PLACES),
         str(j.date), round(j.onhand,settings.DECIMAL_PLACES)
       ) for j in i.flowplans
      ])
    cnt += 1
    if cnt % 300 == 0: transaction.commit(using=database)
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_flowplan")
  print 'Exported %d flowplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportLoadplans(cursor):
  print "Exporting loadplans..."
  starttime = time()
  cnt = 0
  for i in frepple.resources():
    cursor.executemany(
      "insert into out_loadplan \
      (operationplan_id, theresource, quantity, startdate, enddate, setup) \
      values (%s,%s,%s,%s,%s,%s)",
      [(
         j.operationplan.id, j.resource.name,
         round(j.quantity,settings.DECIMAL_PLACES),
         str(j.startdate), str(j.enddate), j.setup
       ) for j in i.loadplans
      ])
    cnt += 1
    if cnt % 100 == 0: transaction.commit(using=database)
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_loadplan")
  print 'Exported %d loadplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportDemand(cursor):

  def deliveries(d):
    cumplanned = 0
    n = d
    while n.hidden and n.owner: n = n.owner
    n = n and n.name or 'unspecified'
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
        round(d.quantity - cumplanned,settings.DECIMAL_PLACES), None,
        None, None
        )

  print "Exporting demand plans..."
  starttime = time()
  cnt = 0
  for i in frepple.demands():
    if i.quantity == 0: continue
    cursor.executemany(
      "insert into out_demand \
      (demand,item,customer,due,quantity,plandate,planquantity,operationplan) \
      values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [ j for j in deliveries(i) ] )
    cnt += 1
    if cnt % 500 == 0: transaction.commit(using=database)
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_demand")
  print 'Exported %d demand plans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportPegging(cursor):
  print "Exporting pegging..."
  starttime = time()
  cnt = 0
  for i in frepple.demands():
    # Find non-hidden demand owner
    n = i
    while n.hidden and n.owner: n = n.owner
    n = n and n.name or 'unspecified'
    # Export pegging
    cursor.executemany(
      "insert into out_demandpegging \
      (demand,depth,cons_operationplan,cons_date,prod_operationplan,prod_date, \
       buffer,item,quantity_demand,quantity_buffer) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         n, str(j.level),
         j.consuming and j.consuming.id or '0', str(j.consuming_date),
         j.producing and j.producing.id or '0', str(j.producing_date),
         j.buffer and j.buffer.name or '',
         (j.buffer and j.buffer.item and j.buffer.item.name) or '',
         round(j.quantity_demand,settings.DECIMAL_PLACES),
         round(j.quantity_buffer,settings.DECIMAL_PLACES)
       ) for j in i.pegging
      ])
    cnt += 1
    if cnt % 500 == 0: transaction.commit(using=database)
  transaction.commit(using=database)
  cursor.execute("select count(*) from out_demandpegging")
  print 'Exported %d pegging in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportForecast(cursor):
  # Detect whether the forecast module is available
  if not 'demand_forecastbucket' in [ a for a, b in inspect.getmembers(frepple) ]:
    return

  print "Exporting forecast plans..."
  starttime = time()
  cnt = 0
  for i in frepple.demands():
    if not isinstance(i, frepple.demand_forecastbucket) or i.total <= 0.0:
      continue
    cursor.executemany(
      "insert into out_forecast \
      (forecast,startdate,enddate,total,net,consumed) \
      values (%s,%s,%s,%s,%s,%s)",
      [(
         i.owner.name, str(i.startdate), str(i.enddate),
         round(i.total,settings.DECIMAL_PLACES),
         round(i.quantity,settings.DECIMAL_PLACES),
         round(i.consumed,settings.DECIMAL_PLACES)
       )
      ])
    cnt += 1
    if cnt % 1000 == 0: transaction.commit(using=database)

  transaction.commit(using=database)
  cursor.execute("select count(*) from out_forecast")
  print 'Exported %d forecast plans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


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
      except Exception, e: print e

    # Close the connection
    cursor.close()


@transaction.commit_manually(using=database)
def exportfrepple():
  '''
  This function exports the data from the frepple memory into the database.
  '''
  # Make sure the debug flag is not set!
  # When it is set, the django database wrapper collects a list of all sql
  # statements executed and their timings. This consumes plenty of memory
  # and cpu time.
  settings.DEBUG = False

  # Create a database connection
  cursor = connections[database].cursor()
  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
    cursor.execute('PRAGMA temp_store = MEMORY;')
    cursor.execute('PRAGMA synchronous = OFF')
    cursor.execute('PRAGMA cache_size = 8000')
  elif settings.DATABASES[database]['ENGINE'] == 'oracle':
    cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")

  # Erase previous output
  truncate(cursor)

  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
    # OPTION 1: Sequential export of each entity
    # For sqlite this is required since a writer blocks the database file.
    # For other databases the parallel export normally gives a better
    # performance, but you could still choose a sequential export.
    exportProblems(cursor)
    exportConstraints(cursor)
    exportOperationplans(cursor)
    exportFlowplans(cursor)
    exportLoadplans(cursor)
    exportDemand(cursor)
    exportForecast(cursor)
    exportPegging(cursor)

  else:
    # OPTION 2: Parallel export of entities in groups.
    # The groups are running in seperate threads, and all functions in a group
    # are run in sequence.
    tasks = (
      DatabaseTask(exportProblems, exportConstraints),
      DatabaseTask(exportOperationplans, exportFlowplans, exportLoadplans),
      DatabaseTask(exportForecast, exportDemand),
      DatabaseTask(exportPegging),
      )
    # Start all threads
    for i in tasks: i.start()
    # Wait for all threads to finish
    for i in tasks: i.join()

  # Analyze
  if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
    print "Analyzing database tables..."
    cursor.execute("analyze")

  # Close the database connection
  cursor.close()
