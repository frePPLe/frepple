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
from django.db import connection
from django.db import transaction
from django.conf import settings

import csv
import frepple

# Exported numbers are rounded to this number of decimals after the comma.
# This number should match the model definitions in models.py
ROUNDING_DECIMALS = 4


def dumpfrepple_files():
  '''
  This function exports the data from the frepple memory into a series of flat files.
  '''
  print "Exporting problems..."
  starttime = time()
  writer = csv.writer(open("problems.csv", "wb"))
  for i in frepple.problem():
    writer.writerow((i['ENTITY'], i['TYPE'], i['DESCRIPTION'], str(i['START']), str(i['END']), str(i['START']), str(i['END']), i['WEIGHT']))
  print 'Exported problems in %.2f seconds' % (time() - starttime)

  print "Exporting operationplans..."
  starttime = time()
  writer = csv.writer(open("operations.csv", "wb"))
  for i in frepple.operationplan():
    writer.writerow( (i['IDENTIFIER'], i['OPERATION'].replace("'","''"),
      i['QUANTITY'], str(i['START']), str(i['END']), str(i['START']),
      str(i['END']), i['DEMAND'], str(i['LOCKED'])) )
  print 'Exported operationplans in %.2f seconds' % (time() - starttime)

  print "Exporting flowplans..."
  starttime = time()
  writer = csv.writer(open("buffers.csv", "wb"))
  for i in frepple.buffer():
    for j in i['FLOWPLANS']:
      writer.writerow( (j['OPERATIONPLAN'], j['OPERATION'], j['BUFFER'],
        j['QUANTITY'], str(j['DATE']), str(j['DATE']), j['ONHAND']) )
  print 'Exported flowplans in %.2f seconds' % (time() - starttime)

  print "Exporting loadplans..."
  starttime = time()
  writer = csv.writer(open("resources.csv", "wb"))
  for i in frepple.resource():
    for j in i['LOADPLANS']:
      writer.writerow( (j['OPERATIONPLAN'], j['OPERATION'], j['RESOURCE'],
        j['QUANTITY'], str(j['DATE']), str(j['DATE']), j['ONHAND'],
        j['MAXIMUM']) )
  print 'Exported loadplans in %.2f seconds' % (time() - starttime)

  print "Exporting pegging..."
  starttime = time()
  writer = csv.writer(open("demand_pegging.csv", "wb"))
  for i in frepple.demand():
    for j in i['PEGGING']:
      writer.writerow( (i['NAME'], j['LEVEL'], j['OPERATIONPLAN'] or None,
        j['BUFFER'], j['QUANTITY'], str(j['DATE']), j['FACTOR'], j['PEGGED']
       ) )
  print 'Exported pegging in %.2f seconds' % (time() - starttime)


@transaction.commit_manually
def dumpfrepple():
  '''
  This function exports the data from the frepple memory into the database.
  '''
  global ROUNDING_DECIMALS

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

  print "Emptying database plan tables..."
  starttime = time()
  if settings.DATABASE_ENGINE in ['sqlite3','postgresql_psycopg2']:
    delete = "delete from %s"
  else:
    delete = "truncate table %s"
  for table in ['out_problem','out_demandpegging','out_flowplan',
                'out_loadplan','out_operationplan',
               ]:
    cursor.execute(delete % table)
    transaction.commit()
  print "Emptied plan tables in %.2f seconds" % (time() - starttime)

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

  print "Exporting operationplans..."
  starttime = time()
  objects = []
  cnt = 0
  for i in frepple.operationplan():
    objects.append( (\
       i['IDENTIFIER'], i['OPERATION'].replace("'","''"),
       round(i['QUANTITY'],ROUNDING_DECIMALS), i['START'], i['END'],
       i['START'].date(), i['END'].date(), i['DEMAND'], str(i['LOCKED'])
     ) )
    cnt += 1
    if cnt >= 10000:
      cursor.executemany(
        "insert into out_operationplan \
        (identifier,operation_id,quantity,startdatetime,enddatetime,startdate, \
         enddate,demand,locked) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)
      transaction.commit()
      objects = []
      cnt = 0
  if cnt > 0:
    cursor.executemany(
      "insert into out_operationplan \
      (identifier,operation_id,quantity,startdatetime,enddatetime,startdate, \
      enddate,demand,locked) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)", objects)
    transaction.commit()
  cursor.execute("select count(*) from out_operationplan")
  print 'Exported %d operationplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)

  print "Exporting flowplans..."
  starttime = time()
  cnt = 0
  for i in frepple.buffer():
    cursor.executemany(
      "insert into out_flowplan \
      (operationplan_id,operation_id,thebuffer_id,quantity,flowdate,flowdatetime, \
      onhand) \
      values (%s,%s,%s,%s,%s,%s,%s)",
      [(
         j['OPERATIONPLAN'], j['OPERATION'], j['BUFFER'],
         round(j['QUANTITY'],ROUNDING_DECIMALS), j['DATE'].date(), j['DATE'],
         round(j['ONHAND'],ROUNDING_DECIMALS)
       ) for j in i['FLOWPLANS']
      ])
    cnt += 1
    if cnt % 20 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_flowplan")
  print 'Exported %d flowplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)

  print "Exporting loadplans..."
  starttime = time()
  cnt = 0
  for i in frepple.resource():
    cursor.executemany(
      "insert into out_loadplan \
      (operationplan_id,operation_id,resource_id,quantity,loaddate, \
      loaddatetime,onhand,maximum) values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         j['OPERATIONPLAN'], j['OPERATION'], j['RESOURCE'],
         round(j['QUANTITY'],ROUNDING_DECIMALS), j['DATE'].date(), j['DATE'],
         round(j['ONHAND'],ROUNDING_DECIMALS), round(j['MAXIMUM'],ROUNDING_DECIMALS)
       ) for j in i['LOADPLANS']
      ])
    cnt += 1
    if cnt % 20 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_loadplan")
  print 'Exported %d loadplans in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)

  print "Exporting pegging..."
  starttime = time()
  cnt = 0
  for i in frepple.demand():
    cursor.executemany(
      "insert into out_demandpegging \
      (demand,depth,operationplan_id,buffer_id,quantity,pegdate, \
      factor,pegged) values (%s,%s,%s,%s,%s,%s,%s,%s)",
      [(
         i['NAME'], j['LEVEL'], j['OPERATIONPLAN'] or None, j['BUFFER'],
         round(j['QUANTITY'],ROUNDING_DECIMALS), j['DATE'],
         round(j['FACTOR'],ROUNDING_DECIMALS), str(j['PEGGED'])
       ) for j in i['PEGGING']
      ])
    cnt += 1
    if cnt % 20 == 0: transaction.commit()
  transaction.commit()
  cursor.execute("select count(*) from out_demandpegging")
  print 'Exported %d pegging in %.2f seconds' % (cursor.fetchone()[0], time() - starttime)

  if settings.DATABASE_ENGINE == 'sqlite3':
    print "Analyzing database tables..."
    cursor.execute("analyze")
