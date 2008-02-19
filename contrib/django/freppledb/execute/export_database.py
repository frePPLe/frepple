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
Exports frePPLe information into a database.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

The code iterates over all objects in the C++ core engine, and creates
database records with the information. Django's database wrappers are used
to keep the code portable between different databases.
'''


from time import time
from threading import Thread

from django.db import connection
from django.db import transaction
from django.conf import settings

import frepple

# Exported numbers are rounded to this number of decimals after the comma.
# This number should match the model definitions in models.py
ROUNDING_DECIMALS = 4


def truncate(cursor):
  print "Emptying database plan tables..."
  starttime = time()
  if settings.DATABASE_ENGINE in ['sqlite3','postgresql_psycopg2']:
    delete = "delete from %s"
  else:
    delete = "truncate table %s"
  for table in ['out_problem', 'out_demandpegging', 'out_flowplan',
                'out_loadplan', 'out_demand', 'out_forecast',
                'out_operationplan',
               ]:
    cursor.execute(delete % table)
    transaction.commit()
  print "Emptied plan tables in %.2f seconds" % (time() - starttime)


def exportProblems(cursor):
  global ROUNDING_DECIMALS
  print "Exporting problems..."
  starttime = time()
  cursor.executemany(
    "insert into out_problem \
    (entity,name,description,startdatetime,enddatetime,startdate,enddate,weight) \
    values(%s,%s,%s,%s,%s,%s,%s,%s)",
    [(
       i['entity'], i['type'], i['description'][0:79], str(i['start']), str(i['end']),
       str(i['start'].date()), str(i['end'].date()), round(i['weight'],ROUNDING_DECIMALS)
     ) for i in frepple.problem()
    ])
  transaction.commit()
  cursor.execute("select count(*) from out_problem")
  print 'Exported %d problems in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportOperationplans(cursor):
  global ROUNDING_DECIMALS
  print "Exporting operationplans..."
  starttime = time()
  objects = []
  cnt = 0
  for i in frepple.operationplan():
    objects.append( (\
       i['identifier'], i['operation'].replace("'","''"),
       round(i['quantity'],ROUNDING_DECIMALS), str(i['start']), str(i['end']),
       str(i['start'].date()), str(i['end'].date()), i['demand'], str(i['locked']), i['owner'] or None
     ) )
    cnt += 1
    if cnt >= 20000:
      cursor.executemany(
        "insert into out_operationplan \
        (identifier,operation,quantity,startdatetime,enddatetime,startdate, \
         enddate,demand,locked,owner) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)
      transaction.commit()
      objects = []
      cnt = 0
  if cnt > 0:
    cursor.executemany(
      "insert into out_operationplan \
      (identifier,operation,quantity,startdatetime,enddatetime,startdate, \
      enddate,demand,locked,owner) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)
    transaction.commit()
  cursor.execute("select count(*) from out_operationplan")
  print 'Exported %d operationplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportFlowplans(cursor):
  global ROUNDING_DECIMALS
  print "Exporting flowplans..."
  starttime = time()
  cnt = 0
  for i in frepple.buffer():
    cursor.executemany(
      "insert into out_flowplan \
      (operationplan, thebuffer, quantity, flowdate, flowdatetime, onhand) \
      values (%s,%s,%s,%s,%s,%s)",
      [(
         j['operationplan'], j['buffer'],
         round(j['quantity'],ROUNDING_DECIMALS), str(j['date'].date()),
         str(j['date']), round(j['onhand'],ROUNDING_DECIMALS)
       ) for j in i['flowplans']
      ])
    cnt += 1
    if cnt % 300 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_flowplan")
  print 'Exported %d flowplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportLoadplans(cursor):
  global ROUNDING_DECIMALS
  print "Exporting loadplans..."
  starttime = time()
  cnt = 0
  sql = 'insert into out_loadplan \
      (operationplan, %s, quantity, startdate, \
      startdatetime, enddate, enddatetime) values \
      (%%s,%%s,%%s,%%s,%%s,%%s,%%s)' % connection.ops.quote_name('resource')
  for i in frepple.resource():
    cursor.executemany(
      sql,
      [(
         j['operationplan'], j['resource'],
         round(j['quantity'],ROUNDING_DECIMALS),
         str(j['startdate'].date()), str(j['startdate']),
         str(j['enddate'].date()), str(j['enddate']),
       ) for j in i['loadplans']
      ])
    cnt += 1
    if cnt % 100 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_loadplan")
  print 'Exported %d loadplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportDemand(cursor):
  global ROUNDING_DECIMALS
  print "Exporting demand plans..."
  starttime = time()
  cnt = 0
  for i in frepple.demand():
    cursor.executemany(
      "insert into out_demand \
      (demand,item,duedate,duedatetime,quantity,plandate,plandatetime,planquantity,operationplan) \
      values (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         i['name'], i['item'], str(i['due'].date()), str(i['due']), round(j['quantity'],ROUNDING_DECIMALS),
         (j['plandate'] and str(j['plandate'].date())) or None, (j['plandate'] and str(j['plandate'])) or None,
         (j['planquantity'] and round(j['planquantity'],ROUNDING_DECIMALS)) or None,
         j['operationplan'] or None
       ) for j in i['delivery']
      ])
    cnt += 1
    if cnt % 500 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_demand")
  print 'Exported %d demand plans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportPegging(cursor):
  global ROUNDING_DECIMALS
  print "Exporting pegging..."
  starttime = time()
  cnt = 0
  for i in frepple.demand():
    cursor.executemany(
      "insert into out_demandpegging \
      (demand,depth,cons_operationplan,cons_date,prod_operationplan,prod_date, \
       buffer,quantity_demand,quantity_buffer,pegged) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         i['name'], str(j['level']),
         j['cons_operationplan'] or 0, str(j['cons_date']),
         j['prod_operationplan'] or 0, str(j['prod_date']),
         j['buffer'], round(j['quantity_demand'],ROUNDING_DECIMALS),
         round(j['quantity_buffer'],ROUNDING_DECIMALS), str(j['pegged'])
       ) for j in i['pegging']
      ])
    cnt += 1
    if cnt % 500 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_demandpegging")
  print 'Exported %d pegging in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportForecast(cursor):
  # Detect whether the forecast module is available
  try: import freppleforecast
  except: return

  global ROUNDING_DECIMALS
  print "Exporting forecast plans..."
  starttime = time()
  cnt = 0
  for i in freppleforecast.forecast():
    cursor.executemany(
      "insert into out_forecast \
      (forecast,startdate,enddate,total,net,consumed) \
      values (%s,%s,%s,%s,%s,%s)",
      [(
         i['name'], str(j['start_date'].date()), str(j['end_date'].date()),
         round(j['totalqty'],ROUNDING_DECIMALS),
         round(j['netqty'],ROUNDING_DECIMALS),
         round(j['consumedqty'],ROUNDING_DECIMALS)
       ) for j in i['buckets'] if j['totalqty'] > 0
      ])
    cnt += 1
    if cnt % 100 == 0: transaction.commit()

  transaction.commit()
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

  @transaction.commit_manually
  def run(self):
    # Create a database connection
    cursor = connection.cursor()
    if settings.DATABASE_ENGINE == 'sqlite3':
      cursor.execute('PRAGMA temp_store = MEMORY;')
      cursor.execute('PRAGMA synchronous = OFF')
      cursor.execute('PRAGMA cache_size = 8000')
    elif settings.DATABASE_ENGINE == 'oracle':
      cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")
    # Run the functions sequentially
    for f in self.functions:
      try: f(cursor)
      except Exception, e: print e


@transaction.commit_manually
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
  cursor = connection.cursor()
  if settings.DATABASE_ENGINE == 'sqlite3':
    cursor.execute('PRAGMA temp_store = MEMORY;')
    cursor.execute('PRAGMA synchronous = OFF')
    cursor.execute('PRAGMA cache_size = 8000')
  elif settings.DATABASE_ENGINE == 'oracle':
    cursor.execute("ALTER SESSION SET COMMIT_WRITE='BATCH,NOWAIT'")

  # Erase previous output
  truncate(cursor)

  if settings.DATABASE_ENGINE == 'sqlite3':
    # OPTION 1: Sequential export of each entity
    # For sqlite this is required since a writer blocks the database file.
    # For other databases the parallel export normally gives a better
    # performance, but you could still choose a sequential export.
    exportProblems(cursor)
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
      DatabaseTask(exportProblems, exportDemand),
      DatabaseTask(exportOperationplans, exportForecast),
      DatabaseTask(exportFlowplans),
      DatabaseTask(exportLoadplans),
      DatabaseTask(exportPegging),
      )
    # Start all threads
    for i in tasks: i.start()
    # Wait for all threads to finish
    for i in tasks: i.join()

  # Analyze
  if settings.DATABASE_ENGINE == 'sqlite3':
    print "Analyzing database tables..."
    cursor.execute("analyze")
