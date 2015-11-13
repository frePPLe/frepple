#
# Copyright (C) 2007-2013 by frePPLe bvba
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
import os
from subprocess import Popen, PIPE
from time import time
from threading import Thread

from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.conf import settings

import frepple

if 'FREPPLE_DATABASE' in os.environ:
  database = os.environ['FREPPLE_DATABASE']
else:
  database = DEFAULT_DB_ALIAS

encoding = 'UTF8'
timestamp = str(datetime.now())


def truncate(process):
  print("Emptying database plan tables...")
  starttime = time()
  process.stdin.write('truncate table out_demandpegging;\n'.encode(encoding))
  process.stdin.write('truncate table out_problem, out_resourceplan, out_constraint;\n'.encode(encoding))
  process.stdin.write('truncate table out_loadplan, out_flowplan, out_operationplan;\n'.encode(encoding))
  process.stdin.write('truncate table out_demand;\n'.encode(encoding))
  process.stdin.write("delete from purchase_order where status='proposed' or status is null;\n".encode(encoding))
  process.stdin.write("delete from distribution_order where status='proposed' or status is null;\n".encode(encoding))
  print("Emptied plan tables in %.2f seconds" % (time() - starttime))


def exportProblems(process):
  print("Exporting problems...")
  starttime = time()
  process.stdin.write('COPY out_problem (entity, name, owner, description, startdate, enddate, weight) FROM STDIN;\n'.encode(encoding))
  for i in frepple.problems():
    process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
       i.entity, i.name,
       isinstance(i.owner, frepple.operationplan) and i.owner.operation.name or i.owner.name,
       i.description, str(i.start), str(i.end),
       round(i.weight, 4)
    )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
  print('Exported problems in %.2f seconds' % (time() - starttime))


def exportConstraints(process):
  print("Exporting constraints...")
  starttime = time()
  process.stdin.write('COPY out_constraint (demand,entity,name,owner,description,startdate,enddate,weight) FROM STDIN;\n'.encode(encoding))
  for d in frepple.demands():
    for i in d.constraints:
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
         d.name, i.entity, i.name,
         isinstance(i.owner, frepple.operationplan) and i.owner.operation.name or i.owner.name,
         i.description, str(i.start), str(i.end),
         round(i.weight, 4)
       )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
  print('Exported constraints in %.2f seconds' % (time() - starttime))


def exportOperationplans(process):
  print("Exporting operationplans...")
  starttime = time()
  process.stdin.write('COPY out_operationplan (id,operation,quantity,startdate,enddate,criticality,locked,unavailable,owner) FROM STDIN;\n'.encode(encoding))
  for i in frepple.operations():
    #if isinstance(i, (frepple.operation_itemsupplier, frepple.operation_itemdistribution)):
    #  # TODO Purchase orders and distribution orders are exported separately
    #  continue
    for j in i.operationplans:
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
        j.id, i.name[0:300],
        round(j.quantity, 4), str(j.start), str(j.end),
        round(j.criticality, 4), j.locked, j.unavailable,
        j.owner and j.owner.id or "\\N"
        )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
  print('Exported operationplans in %.2f seconds' % (time() - starttime))


def exportFlowplans(process):
  print("Exporting flowplans...")
  starttime = time()
  process.stdin.write('COPY out_flowplan (operationplan_id, thebuffer, quantity, flowdate, onhand) FROM STDIN;\n'.encode(encoding))
  for i in frepple.buffers():
    for j in i.flowplans:
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\n" % (
         j.operationplan.id, j.buffer.name,
         round(j.quantity, 4),
         str(j.date), round(j.onhand, 4)
         )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
  print('Exported flowplans in %.2f seconds' % (time() - starttime))


def exportLoadplans(process):
  print("Exporting loadplans...")
  starttime = time()
  process.stdin.write('COPY out_loadplan (operationplan_id, theresource, quantity, startdate, enddate, setup) FROM STDIN;\n'.encode(encoding))
  for i in frepple.resources():
    for j in i.loadplans:
      if j.quantity < 0:
        process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\n" % (
          j.operationplan.id, j.resource.name,
          round(-j.quantity, 4),
          str(j.startdate), str(j.enddate),
          j.setup and j.setup or "\\N"
          )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
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
  process.stdin.write('COPY out_resourceplan (theresource,startdate,available,unavailable,setup,load,free) FROM STDIN;\n'.encode(encoding))
  for i in frepple.resources():
    for j in i.plan(buckets):
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
       i.name, str(j['start']),
       round(j['available'], 4),
       round(j['unavailable'], 4),
       round(j['setup'], 4),
       round(j['load'], 4),
       round(j['free'], 4)
       )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
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
        d.name, d.item.name, d.customer and d.customer.name or "\\N", str(d.due),
        round(cur, 4), str(i.end),
        round(i.quantity, 4), i.id
        )
    # Extra record if planned short
    if cumplanned < d.quantity:
      yield (
        d.name, d.item.name, d.customer and d.customer.name or "\\N", str(d.due),
        round(d.quantity - cumplanned, 4), "\\N",
        "\\N", "\\N"
        )

  print("Exporting demand plans...")
  starttime = time()
  process.stdin.write('COPY out_demand (demand,item,customer,due,quantity,plandate,planquantity,operationplan) FROM STDIN;\n'.encode(encoding))
  for i in frepple.demands():
    if i.quantity == 0:
      continue
    for j in deliveries(i):
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % j).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
  print('Exported demand plans in %.2f seconds' % (time() - starttime))


def exportPegging(process):
  print("Exporting pegging...")
  starttime = time()
  process.stdin.write('COPY out_demandpegging (demand,level,operationplan,quantity) FROM STDIN;\n'.encode(encoding))
  for i in frepple.demands():
    # Find non-hidden demand owner
    n = i
    while n.hidden and n.owner:
      n = n.owner
    n = n and n.name or 'unspecified'
    # Export pegging
    for j in i.pegging:
      process.stdin.write(("%s\t%s\t%s\t%s\n" % (
        n, str(j.level),
        j.operationplan.id, round(j.quantity, 4)
        )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))
  print('Exported pegging in %.2f seconds' % (time() - starttime))


def exportPurchaseOrders(process):

  def getPOs(flag):
    for i in frepple.operations():
      if not isinstance(i, frepple.operation_itemsupplier):
        continue
      for j in i.operationplans:
        if (flag and j.status == 'proposed') or (not flag and j.status != 'proposed'):
          yield j

  print("Exporting purchase orders...")
  starttime = time()

  # Export new proposed orders
  process.stdin.write('COPY purchase_order (id,reference,item_id,location_id,supplier_id,quantity,startdate,enddate,criticality,source,status,lastmodified) FROM STDIN;\n'.encode(encoding))
  for p in getPOs(True):
    process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tproposed\t%s\n" % (
      p.id, p.reference or "\\N",
      p.operation.buffer.item.name[0:300],
      p.operation.buffer.location.name[0:300],
      p.operation.itemsupplier.supplier.name[0:300],
      round(p.quantity, 4), str(p.start), str(p.end),
      round(p.criticality, 4),
      p.source or "\\N",
      timestamp
      )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))

  # Export existing orders
  with transaction.atomic(using=database, savepoint=False):
    cursor = connections[database].cursor()
    cursor.executemany(
      "update purchase_order set criticality=%s where id=%s",
      [ (round(j.criticality, 4), j.id) for j in getPOs(False) ]
      )

  print('Exported purchase orders in %.2f seconds' % (time() - starttime))


def exportDistributionOrders(process):

  def getDOs(flag):
    for i in frepple.operations():
      if not isinstance(i, frepple.operation_itemdistribution):
        continue
      for j in i.operationplans:
        if (flag and j.status == 'proposed') or (not flag and j.status != 'proposed'):
          yield j

  print("Exporting distribution orders...")
  starttime = time()

  # Export new proposed orders
  process.stdin.write('COPY distribution_order (id,reference,item_id,origin_id,destination_id,quantity,startdate,enddate,criticality,source,status,consume_material,lastmodified) FROM STDIN;\n'.encode(encoding))
  for p in getDOs(True):
    process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tproposed\ttrue\t%s\n" % (
      p.id, p.reference or "\\N",
      p.operation.destination.item.name[0:300],
      p.operation.origin.location.name[0:300],
      p.operation.destination.location.name[0:300],
      round(p.quantity, 4), str(p.start), str(p.end),
      round(p.criticality, 4),
      p.source or "\\N",
      timestamp
      )).encode(encoding))
  process.stdin.write('\\.\n'.encode(encoding))

  # Update existing orders
  with transaction.atomic(using=database, savepoint=False):
    cursor = connections[database].cursor()
    cursor.executemany(
      "update distribution_order set criticality=%s where id=%s",
      [ (round(j.criticality, 4), j.id) for j in getDOs(False) ]
      )

  print('Exported distribution orders in %.2f seconds' % (time() - starttime))


class DatabasePipe(Thread):
  '''
  An auxiliary class that allows us to run a function with its own
  PostgreSQL process pipe.
  '''
  def __init__(self, *f):
    super(DatabasePipe, self).__init__()
    self.functions = f

  def run(self):
    test = 'FREPPLE_TEST' in os.environ

    # Start a PSQL process
    my_env = os.environ
    my_env['PGPASSWORD'] = settings.DATABASES[database]['PASSWORD']
    process = Popen("psql -q -w -U%s %s%s%s" % (
        settings.DATABASES[database]['USER'],
       settings.DATABASES[database]['HOST'] and ("-h %s " % settings.DATABASES[database]['HOST']) or '',
       settings.DATABASES[database]['PORT'] and ("-p %s " % settings.DATABASES[database]['PORT']) or '',
       settings.DATABASES[database]['TEST']['NAME'] if test else settings.DATABASES[database]['NAME'],
     ), stdin=PIPE, stderr=PIPE, bufsize=0, shell=True, env=my_env)
    if process.returncode is None:
      # PSQL session is still running
      process.stdin.write("SET statement_timeout = 0;\n".encode(encoding))
      process.stdin.write("SET client_encoding = 'UTF8';\n".encode(encoding))

    # Run the functions sequentially
    try:
      for f in self.functions:
        f(process)
    finally:
      print(process.communicate()[1])
      # Close the pipe and PSQL process
      if process.returncode is None:
        # PSQL session is still running.
        process.stdin.write('\\q\n'.encode(encoding))
      process.stdin.close()


def exportfrepple():
  '''
  This function exports the data from the frePPLe memory into the database.
  The export runs in parallel over 4 connections to PostgreSQL.
  '''
  global timestamp
  timestamp = str(datetime.now())

  # Truncate
  task = DatabasePipe(truncate)
  task.start()
  task.join()

  # Export process
  tasks = (
    DatabasePipe(exportResourceplans, exportDemand, exportProblems, exportConstraints),
    DatabasePipe(exportPurchaseOrders, exportDistributionOrders, exportOperationplans, exportFlowplans, exportLoadplans, exportPegging)
    )
  # Start all threads
  for i in tasks:
    i.start()
  # Wait for all threads to finish
  for i in tasks:
    i.join()

  # Report on the output
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
    union select 'purchase_order', count(*) from purchase_order
    union select 'distribution_order', count(*) from distribution_order
    order by 1
    ''')
  for table, recs in cursor.fetchall():
    print("Table %s: %d records" % (table, recs))


def exportfrepple_sequential():
  '''
  This function exports the data from the frePPLe memory into the database.
  The export runs sequentially over s single connection to PostgreSQL.
  '''
  test = 'FREPPLE_TEST' in os.environ

  # Start a PSQL process
  my_env = os.environ
  my_env['PGPASSWORD'] = settings.DATABASES[database]['PASSWORD']
  process = Popen("psql -q -w -U%s %s%s%s" % (
      settings.DATABASES[database]['USER'],
     settings.DATABASES[database]['HOST'] and ("-h %s " % settings.DATABASES[database]['HOST']) or '',
     settings.DATABASES[database]['PORT'] and ("-p %s " % settings.DATABASES[database]['PORT']) or '',
     test and settings.DATABASES[database]['TEST']['NAME'] or settings.DATABASES[database]['NAME'],
   ), stdin=PIPE, stderr=PIPE, bufsize=0, shell=True, env=my_env)
  if process.returncode is None:
    # PSQL session is still running
    process.stdin.write("SET statement_timeout = 0;\n".encode(encoding))
    process.stdin.write("SET client_encoding = 'UTF8';\n".encode(encoding))

  # Send all output to the PSQL process through a pipe
  try:
    truncate(process)
    exportProblems(process)
    exportConstraints(process)
    exportOperationplans(process)
    exportPurchaseOrders(process)
    exportDistributionOrders(process)
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
      process.stdin.write('\\q\n'.encode(encoding))
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
    union select 'purchase_order', count(*) from purchase_order
    union select 'distribution_order', count(*) from distribution_order
    order by 1
    ''')
  for table, recs in cursor.fetchall():
    print("Table %s: %d records" % (table, recs or 0))
