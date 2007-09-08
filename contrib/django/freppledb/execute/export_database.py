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
                'out_loadplan', 'out_demand', #xxx'out_forecast',
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
       i['ENTITY'], i['TYPE'], i['DESCRIPTION'], i['START'], i['END'],
       i['START'].date(), i['END'].date(), round(i['WEIGHT'],ROUNDING_DECIMALS)
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
       i['IDENTIFIER'], i['OPERATION'].replace("'","''"),
       round(i['QUANTITY'],ROUNDING_DECIMALS), i['START'], i['END'],
       i['START'].date(), i['END'].date(), i['DEMAND'], str(i['LOCKED']), i['OWNER'] or None
     ) )
    cnt += 1
    if cnt >= 10000:
      cursor.executemany(
        "insert into out_operationplan \
        (identifier,operation,quantity,startdatetime,enddatetime,startdate, \
         enddate,demand,locked,owner_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)
      transaction.commit()
      objects = []
      cnt = 0
  if cnt > 0:
    cursor.executemany(
      "insert into out_operationplan \
      (identifier,operation,quantity,startdatetime,enddatetime,startdate, \
      enddate,demand,locked,owner_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)
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
      (operationplan, operation, thebuffer, quantity, flowdate, \
       flowdatetime, onhand) \
      values (%s,%s,%s,%s,%s,%s,%s)",
      [(
         j['OPERATIONPLAN'], j['OPERATION'], j['BUFFER'],
         round(j['QUANTITY'],ROUNDING_DECIMALS), j['DATE'].date(), j['DATE'],
         round(j['ONHAND'],ROUNDING_DECIMALS)
       ) for j in i['FLOWPLANS']
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
         j['OPERATIONPLAN'], j['RESOURCE'],
         round(j['QUANTITY'],ROUNDING_DECIMALS),
         j['STARTDATE'].date(), j['STARTDATE'],
         j['ENDDATE'].date(), j['ENDDATE'],
       ) for j in i['LOADPLANS']
      ])
    cnt += 1
    if cnt % 50 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_loadplan")
  print 'Exported %d loadplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportDemand(cursor):
  global ROUNDING_DECIMALS
  print "Exporting demand..."
  starttime = time()
  cnt = 0
  for i in frepple.demand():
    cursor.executemany(
      "insert into out_demand \
      (demand,duedate,duedatetime,quantity,plandate,plandatetime,planquantity,operationplan) \
      values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         i['NAME'], i['DUE'].date(), i['DUE'], round(j['QUANTITY'],ROUNDING_DECIMALS),
         (j['PLANDATE'] and j['PLANDATE'].date()) or None, j['PLANDATE'],
         (j['PLANQUANTITY'] and round(j['PLANQUANTITY'],ROUNDING_DECIMALS)) or None,
         j['OPERATIONPLAN'] or None
       ) for j in i['DELIVERY']
      ])
    cnt += 1
    if cnt % 100 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_demand")
  print 'Exported %d demands in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportPegging(cursor):
  global ROUNDING_DECIMALS
  print "Exporting pegging..."
  starttime = time()
  cnt = 0
  for i in frepple.demand():
    cursor.executemany(
      "insert into out_demandpegging \
      (demand,depth,operationplan,buffer,quantity,pegdate, \
      factor,pegged) values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         i['NAME'], j['LEVEL'], j['OPERATIONPLAN'] or None, j['BUFFER'],
         round(j['QUANTITY'],ROUNDING_DECIMALS), j['DATE'],
         round(j['FACTOR'],ROUNDING_DECIMALS), str(j['PEGGED'])
       ) for j in i['PEGGING']
      ])
    cnt += 1
    if cnt % 100 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_demandpegging")
  print 'Exported %d pegging in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


def exportForecast(cursor):
  global ROUNDING_DECIMALS
  print "Exporting forecast..."
  starttime = time()
  cnt = 0
  for i in frepple.demand():
    cursor.executemany(
      "insert into out_forecast \
      (operationplan,operation_id,resource_id,quantity,loaddate, \
      loaddatetime,onhand,maximum) values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         j['OPERATIONPLAN'], j['OPERATION'], j['RESOURCE'],
         round(j['QUANTITY'],ROUNDING_DECIMALS), j['DATE'].date(), j['DATE'],
         round(j['ONHAND'],ROUNDING_DECIMALS), round(j['MAXIMUM'],ROUNDING_DECIMALS)
       ) for j in i['LOADPLANS']
      ])
    cnt += 1
    if cnt % 50 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_forecast")
  print 'Exported %d forecasts in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)


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
    #exportForecast(cursor)
    exportPegging(cursor)
  else:
    # OPTION 2: Parallel export of entities in groups.
    # The groups are running in seperate threads, and all functions in a group
    # are run in sequence.
    tasks = (
      DatabaseTask(exportProblems, exportDemand),
      DatabaseTask(exportOperationplans),
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
