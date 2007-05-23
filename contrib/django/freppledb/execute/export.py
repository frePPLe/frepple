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

from os import times
from django.db import connection
from django.db import transaction
import csv
import frepple


def dumpfrepple_files():
  '''
  This function exports the data from the frepple memory into a series of flat files.
  '''
  print "Exporting problems..."
  starttime = times()[4]
  writer = csv.writer(open("problems.csv", "wb"))
  for i in frepple.problem():
    writer.writerow((i['ENTITY'], i['TYPE'], i['DESCRIPTION'], str(i['START']), str(i['END']), str(i['START']), str(i['END'])))
  print 'Exported problems in %.2f seconds' % (times()[4] - starttime)

  print "Exporting operationplans..."
  starttime = times()[4]
  writer = csv.writer(open("operations.csv", "wb"))
  for i in frepple.operationplan():
    writer.writerow( (i['IDENTIFIER'], i['OPERATION'].replace("'","''"), i['QUANTITY'], str(i['START']), str(i['END']), str(i['START']), str(i['END']), i['DEMAND'], str(i['LOCKED'])) )
  print 'Exported operationplans in %.2f seconds' % (times()[4] - starttime)

  print "Exporting flowplans..."
  starttime = times()[4]
  writer = csv.writer(open("buffers.csv", "wb"))
  for i in frepple.buffer():
    for j in i['FLOWPLANS']:
      writer.writerow( (j['OPERATIONPLAN'], j['OPERATION'], j['BUFFER'], j['QUANTITY'], str(j['DATE']), str(j['DATE']), j['ONHAND']) )
  print 'Exported flowplans in %.2f seconds' % (times()[4] - starttime)

  print "Exporting loadplans..."
  starttime = times()[4]
  writer = csv.writer(open("resources.csv", "wb"))
  for i in frepple.resource():
    for j in i['LOADPLANS']:
      writer.writerow( (j['OPERATIONPLAN'], j['OPERATION'], j['RESOURCE'], j['QUANTITY'], str(j['DATE']), str(j['DATE']), j['ONHAND'], j['MAXIMUM']) )
  print 'Exported loadplans in %.2f seconds' % (times()[4] - starttime)


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
