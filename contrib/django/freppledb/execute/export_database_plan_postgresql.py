#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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

r'''
Exports the plan information from the frePPLe C++ core engine into a
PostgreSQL database.

The code in this file is executed NOT by the Django web application, but by the
embedded Python interpreter from the frePPLe engine.
'''
from datetime import timedelta, datetime, date
from time import time
import os
from subprocess import Popen, PIPE

from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

import frepple

if 'FREPPLE_DATABASE' in os.environ:
  database = os.environ['FREPPLE_DATABASE']
else:
  database = DEFAULT_DB_ALIAS

encoding = 'UTF8'


def truncate(process):
  print("Emptying database plan tables...")
  starttime = time()
  process.stdin.write('truncate table out_demandpegging;\n')
  process.stdin.write('truncate table out_problem, out_resourceplan, out_constraint;\n')
  process.stdin.write('truncate table out_loadplan, out_flowplan, out_operationplan;\n')
  process.stdin.write('truncate table out_demand;\n')
  print("Emptied plan tables in %.2f seconds" % (time() - starttime))


def exportProblems(process):
  print("Exporting problems...")
  starttime = time()
  process.stdin.write('COPY out_problem (entity, name, owner, description, startdate, enddate, weight) FROM STDIN;\n')
  for i in frepple.problems():
    process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
       i.entity.encode(encoding), i.name.encode(encoding),
       isinstance(i.owner, frepple.operationplan) and i.owner.operation.name.encode(encoding) or i.owner.name.encode(encoding),
       i.description.encode(encoding)[0:settings.NAMESIZE + 20], str(i.start), str(i.end),
       round(i.weight, settings.DECIMAL_PLACES)
    ))
  process.stdin.write('\\.\n')
  print('Exported problems in %.2f seconds' % (time() - starttime))


def exportConstraints(process):
  print("Exporting constraints...")
  starttime = time()
  process.stdin.write('COPY out_constraint (demand,entity,name,owner,description,startdate,enddate,weight) FROM STDIN;\n')
  for d in frepple.demands():
    for i in d.constraints:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
         d.name.encode(encoding), i.entity.encode(encoding), i.name.encode(encoding),
         isinstance(i.owner, frepple.operationplan) and i.owner.operation.name.encode(encoding) or i.owner.name.encode(encoding),
         i.description.encode(encoding)[0:settings.NAMESIZE + 20], str(i.start), str(i.end),
         round(i.weight, settings.DECIMAL_PLACES)
       ))
  process.stdin.write('\\.\n')
  print('Exported constraints in %.2f seconds' % (time() - starttime))


def exportOperationplans(process):
  print("Exporting operationplans...")
  starttime = time()
  process.stdin.write('COPY out_operationplan (id,operation,quantity,startdate,enddate,criticality,locked,unavailable,owner) FROM STDIN;\n')
  for i in frepple.operations():
    for j in i.operationplans:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
        j.id, i.name[0:settings.NAMESIZE].encode(encoding),
        round(j.quantity, settings.DECIMAL_PLACES), str(j.start), str(j.end),
        round(j.criticality, settings.DECIMAL_PLACES), j.locked, j.unavailable,
        j.owner and j.owner.id or "\\N"
        ))
  process.stdin.write('\\.\n')
  print('Exported operationplans in %.2f seconds' % (time() - starttime))


def exportFlowplans(process):
  print("Exporting flowplans...")
  starttime = time()
  process.stdin.write('COPY out_flowplan (operationplan_id, thebuffer, quantity, flowdate, onhand) FROM STDIN;\n')
  for i in frepple.buffers():
    for j in i.flowplans:
      process.stdin.write("%s\t%s\t%s\t%s\t%s\n" % (
         j.operationplan.id, j.buffer.name.encode(encoding),
         round(j.quantity, settings.DECIMAL_PLACES),
         str(j.date), round(j.onhand, settings.DECIMAL_PLACES)
         ))
  process.stdin.write('\\.\n')
  print('Exported flowplans in %.2f seconds' % (time() - starttime))


def exportLoadplans(process):
  print("Exporting loadplans...")
  starttime = time()
  process.stdin.write('COPY out_loadplan (operationplan_id, theresource, quantity, startdate, enddate, setup) FROM STDIN;\n')
  for i in frepple.resources():
    for j in i.loadplans:
      if j.quantity < 0:
        process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (
          j.operationplan.id, j.resource.name.encode(encoding),
          round(-j.quantity, settings.DECIMAL_PLACES),
          str(j.startdate), str(j.enddate),
          j.setup and j.setup.encode(encoding) or "\\N"
          ))
  process.stdin.write('\\.\n')
  print('Exported loadplans in %.2f seconds' % (time() - starttime))


def exportResourceplans(process):
  print("Exporting resourceplans...")
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
      if j.startdate < startdate:
        startdate = j.startdate
      if j.enddate > enddate:
        enddate = j.enddate
  if startdate == datetime.max:
    startdate = frepple.settings.current
  if enddate == datetime.min:
    enddate = frepple.settings.current
  startdate = (startdate - timedelta(days=30)).date()
  enddate = (enddate + timedelta(days=30)).date()
  if enddate > date(2030, 12, 30):  # This is the max frePPLe can represent.
    enddate = date(2030, 12, 30)

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
       i.name.encode(encoding), str(j['start']),
       round(j['available'], settings.DECIMAL_PLACES),
       round(j['unavailable'], settings.DECIMAL_PLACES),
       round(j['setup'], settings.DECIMAL_PLACES),
       round(j['load'], settings.DECIMAL_PLACES),
       round(j['free'], settings.DECIMAL_PLACES)
       ))
  process.stdin.write('\\.\n')
  print('Exported resourceplans in %.2f seconds' % (time() - starttime))


def exportDemand(process):

  def deliveries(d):
    cumplanned = 0
    # Loop over all delivery operationplans
    for i in d.operationplans:
      cumplanned += i.quantity
      cur = i.quantity
      if cumplanned > d.quantity:
        cur -= cumplanned - d.quantity
        if cur < 0:
          cur = 0
      yield (
        d.name.encode(encoding), d.item.name.encode(encoding), d.customer and d.customer.name.encode(encoding) or "\\N", str(d.due),
        round(cur, settings.DECIMAL_PLACES), str(i.end),
        round(i.quantity, settings.DECIMAL_PLACES), i.id
        )
    # Extra record if planned short
    if cumplanned < d.quantity:
      yield (
        d.name.encode(encoding), d.item.name.encode(encoding), d.customer and d.customer.name.encode(encoding) or "\\N", str(d.due),
        round(d.quantity - cumplanned, settings.DECIMAL_PLACES), "\\N",
        "\\N", "\\N"
        )

  print("Exporting demand plans...")
  starttime = time()
  process.stdin.write('COPY out_demand (demand,item,customer,due,quantity,plandate,planquantity,operationplan) FROM STDIN;\n')
  for i in frepple.demands():
    if i.quantity == 0:
      continue
    for j in deliveries(i):
      process.stdin.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % j)
  process.stdin.write('\\.\n')
  print('Exported demand plans in %.2f seconds' % (time() - starttime))


def exportPegging(process):
  print("Exporting pegging...")
  starttime = time()
  process.stdin.write('COPY out_demandpegging (demand,level,operationplan,quantity) FROM STDIN;\n')
  for i in frepple.demands():
    # Find non-hidden demand owner
    n = i
    while n.hidden and n.owner:
      n = n.owner
    n = n and n.name or 'unspecified'
    # Export pegging
    for j in i.pegging:
      process.stdin.write("%s\t%s\t%s\t%s\n" % (
        n.encode(encoding), str(j.level),
        j.operationplan.id, round(j.quantity, settings.DECIMAL_PLACES)
        ))
  process.stdin.write('\\.\n')
  print('Exported pegging in %.2f seconds' % (time() - starttime))


def exportfrepple():
  '''
  This function exports the data from the frePPLe memory into the database.
  '''
  test = 'FREPPLE_TEST' in os.environ

  # Start a PSQL process
  # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
  os.environ['PGPASSWORD'] = settings.DATABASES[database]['PASSWORD']
  process = Popen("psql -q -w -U%s %s%s%s" % (
      settings.DATABASES[database]['USER'],
     settings.DATABASES[database]['HOST'] and ("-h %s " % settings.DATABASES[database]['HOST']) or '',
     settings.DATABASES[database]['PORT'] and ("-p %s " % settings.DATABASES[database]['PORT']) or '',
     test and settings.DATABASES[database]['TEST_NAME'] or settings.DATABASES[database]['NAME'],
   ), stdin=PIPE, stderr=PIPE, bufsize=0, shell=True, universal_newlines=True)
  if process.returncode is None:
    # PSQL session is still running
    process.stdin.write("SET statement_timeout = 0;\n")
    process.stdin.write("SET client_encoding = 'UTF8';\n")

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
  finally:
    # Print any error messages
    print(process.communicate()[1])
    # Close the pipe and PSQL process
    if process.returncode is None:
      # PSQL session is still running.
      process.stdin.write('\\q\n')
    process.stdin.close()

  cursor = connections[database].cursor()
  cursor.execute('''
    select 'out_problem', count(*) from out_problem
    union select 'out_constraint', count(*) from out_constraint
    union select 'out_operationplan', count(*) from out_operationplan
    union select 'out_flowplan', count(*) from out_flowplan
    union select 'out_loadplan', count(*) from out_loadplan
    union select 'out_resourceplan', count(*) from out_resourceplan
    union select 'out_demandpegging', count(*) from out_demandpegging
    union select 'out_demand', count(*) from out_demand
    order by 1
    ''')
  for table, recs in cursor.fetchall():
    print("Table %s: %d records" % (table, recs))
