#
# Copyright (C) 2007-2013 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

r'''
Exports the plan information from the frePPLe C++ core engine into a
PostgreSQL database.

The code in this file is executed NOT by the Django web application, but by the
embedded Python interpreter from the frePPLe engine.
'''
from datetime import timedelta, datetime, date
import json
import os
from psycopg2.extensions import adapt
from subprocess import Popen, PIPE
from time import time
from threading import Thread

from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.conf import settings

import frepple


class DatabasePipe(Thread):
  '''
  An auxiliary class that allows us to run a function with its own
  PostgreSQL process pipe.
  '''
  def __init__(self, owner, *f):
    self.owner = owner
    super(DatabasePipe, self).__init__()
    self.functions = f

  def run(self):
    test = 'FREPPLE_TEST' in os.environ

    # Start a PSQL process
    my_env = os.environ
    if settings.DATABASES[self.owner.database]['PASSWORD']:
      my_env['PGPASSWORD'] = settings.DATABASES[self.owner.database]['PASSWORD']
    process = Popen("psql -q -w %s%s%s%s" % (
       settings.DATABASES[self.owner.database]['USER'] and ("-U %s " % settings.DATABASES[self.owner.database]['USER']) or '',
       settings.DATABASES[self.owner.database]['HOST'] and ("-h %s " % settings.DATABASES[self.owner.database]['HOST']) or '',
       settings.DATABASES[self.owner.database]['PORT'] and ("-p %s " % settings.DATABASES[self.owner.database]['PORT']) or '',
       settings.DATABASES[self.owner.database]['TEST']['NAME'] if test else settings.DATABASES[self.owner.database]['NAME'],
     ), stdin=PIPE, stderr=PIPE, bufsize=0, shell=True, env=my_env)
    if process.returncode is None:
      # PSQL session is still running
      process.stdin.write("SET statement_timeout = 0;\n".encode(self.owner.encoding))
      process.stdin.write("SET client_encoding = 'UTF8';\n".encode(self.owner.encoding))

    # Run the functions sequentially
    try:
      for f in self.functions:
        f(self.owner, process)
    finally:
      msg = process.communicate()[1]
      if msg:
        print(msg)
      # Close the pipe and PSQL process
      if process.returncode is None:
        # PSQL session is still running.
        process.stdin.write('\\q\n'.encode(self.owner.database))
      process.stdin.close()


class export:

  def __init__(self, cluster=-1, verbosity=1, database=None):
    self.cluster = cluster
    self.verbosity = verbosity
    if database:
      self.database = database
    else:
      if 'FREPPLE_DATABASE' in os.environ:
        self.database = os.environ['FREPPLE_DATABASE']
      else:
        self.database = DEFAULT_DB_ALIAS
    self.encoding = 'UTF8'
    self.timestamp = str(datetime.now())


  def getPegging(self, opplan):
    peg = { j.demand.name: round(j.quantity, 6) for j in opplan.pegging_demand }
    # We need to double any backslash to assure that the string remains
    # valid when passing it through postgresql (which eats them away)
    return json.dumps(peg).replace("\\", "\\\\")


  def truncate(self, process):
    if self.verbosity:
      print("Emptying database plan tables...")
    starttime = time()
    if self.cluster == -1:
      # Complete export for the complete model
      process.stdin.write("truncate table out_problem, out_resourceplan, out_constraint;\n".encode(self.encoding))
      process.stdin.write("truncate table operationplanmaterial, operationplanresource;\n".encode(self.encoding)) 
# Above line is a temporary solution until we have a correct version of this block of code 
#       process.stdin.write('''
#         delete from operationplanmaterial
#         using operationplan
#         where operationplanmaterial.operationplan_id = operationplan.id
#         and ((operationplan.status='proposed' or operationplan.status is null) or operationplan.type = 'STCK');\n
#         '''.encode(self.encoding))
#       process.stdin.write('''
#         delete from operationplanresource
#         using operationplan
#         where operationplanresource.operationplan_id = operationplan.id
#         and ((operationplan.status='proposed' or operationplan.status is null) or operationplan.type = 'STCK');\n
#         '''.encode(self.encoding))
      process.stdin.write('''
        delete from operationplan
        where (status='proposed' or status is null) or type = 'STCK';\n
        '''.encode(self.encoding))
    else:
      # Partial export for a single cluster
      process.stdin.write('create temporary table cluster_keys (name character varying(300), constraint cluster_key_pkey primary key (name));\n'.encode(self.encoding))
      for i in frepple.items():
        if i.cluster == self.cluster:
          process.stdin.write(("insert into cluster_keys (name) values (%s);\n" % adapt(i.name).getquoted().decode(self.encoding)).encode(self.encoding))
      process.stdin.write("delete from out_constraint where demand in (select demand.name from demand inner join cluster_keys on cluster_keys.name = demand.item_id);\n".encode(self.encoding))
      process.stdin.write('''
        delete from operationplanmaterial
        where buffer in (select buffer.name from buffer inner join cluster_keys on cluster_keys.name = buffer.item_id);\n
        '''.encode(self.encoding))
      process.stdin.write('''
        delete from out_problem
        where entity = 'demand' and owner in (
          select demand.name from demand inner join cluster_keys on cluster_keys.name = demand.item_id
          );\n
        '''.encode(self.encoding))
      process.stdin.write('''
        delete from out_problem
        where entity = 'material'
        and owner in (select buffer.name from buffer inner join cluster_keys on cluster_keys.name = buffer.item_id);\n
        '''.encode(self.encoding))
      process.stdin.write('''
        delete from operationplan
        using cluster_keys
        where (status='proposed' or status is null or type='STCK')
        and item_id = cluster_keys.name;\n
        '''.encode(self.encoding))
      process.stdin.write("truncate table cluster_keys;\n".encode(self.encoding))
      for i in frepple.resources():
        if i.cluster == self.cluster:
          process.stdin.write(("insert into cluster_keys (name) values (%s);\n" % adapt(i.name).getquoted().decode(self.encoding)).encode(self.encoding))
      process.stdin.write("delete from out_problem where entity = 'demand' and owner in (select demand.name from demand inner join cluster_keys on cluster_keys.name = demand.item_id);\n".encode(self.encoding))
      process.stdin.write('delete from operationplanresource using cluster_keys where resource = cluster_keys.name;\n'.encode(self.encoding))
      process.stdin.write('delete from out_resourceplan using cluster_keys where resource = cluster_keys.name;\n'.encode(self.encoding))
      process.stdin.write("delete from out_problem using cluster_keys where entity = 'capacity' and owner = cluster_keys.name;\n".encode(self.encoding))
      process.stdin.write('truncate table cluster_keys;\n'.encode(self.encoding))
      for i in frepple.operations():
        if i.cluster == self.cluster:
          process.stdin.write(("insert into cluster_keys (name) values (%s);\n" % adapt(i.name).getquoted().decode(self.encoding)).encode(self.encoding))
      process.stdin.write("delete from out_problem using cluster_keys where entity = 'operation' and owner = cluster_keys.name;\n".encode(self.encoding))
      process.stdin.write("delete from operationplan using cluster_keys where (status='proposed' or status is null) and operationplan.operation_id = cluster_keys.name;\n".encode(self.encoding)) # TODO not correct in new data model
      process.stdin.write("drop table cluster_keys;\n".encode(self.encoding))
    if self.verbosity:
      print("Emptied plan tables in %.2f seconds" % (time() - starttime))


  def exportProblems(self, process):
    if self.verbosity:
      print("Exporting problems...")
    starttime = time()
    process.stdin.write('COPY out_problem (entity, name, owner, description, startdate, enddate, weight) FROM STDIN;\n'.encode(self.encoding))
    for i in frepple.problems():
      if isinstance(i.owner, frepple.operationplan):
        owner = i.owner.operation
      else:
        owner = i.owner
      if self.cluster != -1 and owner.cluster != self.cluster:
        continue
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
         i.entity, i.name, owner.name,
         i.description, str(i.start), str(i.end),
         round(i.weight, 6)
      )).encode(self.encoding))
    process.stdin.write('\\.\n'.encode(self.encoding))
    if self.verbosity:
      print('Exported problems in %.2f seconds' % (time() - starttime))


  def exportConstraints(self, process):
    if self.verbosity:
      print("Exporting constraints...")
    starttime = time()
    process.stdin.write('COPY out_constraint (demand,entity,name,owner,description,startdate,enddate,weight) FROM STDIN;\n'.encode(self.encoding))
    for d in frepple.demands():
      if self.cluster != -1 and self.cluster != d.cluster:
        continue
      for i in d.constraints:
        process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
           d.name, i.entity, i.name,
           isinstance(i.owner, frepple.operationplan) and i.owner.operation.name or i.owner.name,
           i.description, str(i.start), str(i.end),
           round(i.weight, 6)
         )).encode(self.encoding))
    process.stdin.write('\\.\n'.encode(self.encoding))
    if self.verbosity:
      print('Exported constraints in %.2f seconds' % (time() - starttime))


  def exportOperationplans(self, process):

    def getOperationPlans():
      for i in frepple.operations():        
        if self.cluster != -1 and self.cluster != i.cluster:
          continue
        for j in i.operationplans:     
          if isinstance(i, frepple.operation_inventory):
            # Export inventory  
            yield (
              i.name, 'STCK', j.status, j.reference or '\\N', round(j.quantity, 6),
              str(j.start), str(j.end), round(j.criticality, 6), j.delay,
              self.getPegging(j), j.source or '\\N', self.timestamp,
              '\\N', j.owner.id if j.owner and not j.owner.operation.hidden else '\\N',
              j.operation.buffer.item.name, j.operation.buffer.location.name, '\\N', '\\N', '\\N',
              j.demand.name if j.demand else j.owner.demand.name if j.owner and j.owner.demand else '\\N',
              j.demand.due if j.demand else j.owner.demand.due if j.owner and j.owner.demand else '\\N',
              j.id
              )
          elif isinstance(i, frepple.operation_itemdistribution):
            # Export DO
            yield (
              i.name, 'DO', j.status, j.reference or '\\N', round(j.quantity, 6),
              str(j.start), str(j.end), round(j.criticality, 6), j.delay,
              self.getPegging(j), j.source or '\\N', self.timestamp,
              '\\N', j.owner.id if j.owner and not j.owner.operation.hidden else '\\N',
              j.operation.destination.item.name, j.operation.destination.location.name,
              j.operation.origin.location.name,
              '\\N', '\\N',
              j.demand.name if j.demand else j.owner.demand.name if j.owner and j.owner.demand else '\\N',
              j.demand.due if j.demand else j.owner.demand.due if j.owner and j.owner.demand else '\\N',
              j.id
              )
          elif isinstance(i, frepple.operation_itemsupplier):
            # Export PO
            yield (
              i.name, 'PO', j.status, j.reference or '\\N', round(j.quantity, 6),
              str(j.start), str(j.end), round(j.criticality, 6), j.delay,
              self.getPegging(j), j.source or '\\N', self.timestamp,
              '\\N', j.owner.id if j.owner and not j.owner.operation.hidden else '\\N',
              j.operation.buffer.item.name, '\\N', '\\N',
              j.operation.buffer.location.name, j.operation.itemsupplier.supplier.name,
              j.demand.name if j.demand else j.owner.demand.name if j.owner and j.owner.demand else '\\N',
              j.demand.due if j.demand else j.owner.demand.due if j.owner and j.owner.demand else '\\N',
              j.id
              )
          elif not i.hidden:
            # Export MO
            yield (
              i.name, 'MO', j.status, j.reference or '\\N', round(j.quantity, 6),
              str(j.start), str(j.end), round(j.criticality, 6), j.delay,
              self.getPegging(j), j.source or '\\N', self.timestamp,
              i.name, j.owner.id if j.owner and not j.owner.operation.hidden else '\\N',
              '\\N', '\\N', '\\N', '\\N', '\\N',
              j.demand.name if j.demand else j.owner.demand.name if j.owner and j.owner.demand else '\\N',
              j.demand.due if j.demand else j.owner.demand.due if j.owner and j.owner.demand else '\\N',
              j.id
              )
          elif j.demand or (j.owner and j.owner.demand):
            # Export shipments (with automatically created delivery operations)
            yield (
              i.name, 'DLVR', j.status, j.reference or '\\N', round(j.quantity, 6),
              str(j.start), str(j.end), round(j.criticality, 6), j.delay,
              self.getPegging(j), j.source or '\\N', self.timestamp,
              '\\N', j.owner.id if j.owner and not j.owner.operation.hidden else '\\N',
              j.operation.buffer.item.name, '\\N', '\\N', j.operation.buffer.location.name, '\\N',
              j.demand.name if j.demand else j.owner.demand.name if j.owner and j.owner.demand else '\\N',
              j.demand.due if j.demand else j.owner.demand.due if j.owner and j.owner.demand else '\\N',
              j.id
              )

    if self.verbosity:
      print("Exporting operationplans...")
    starttime = time()

    # Export operationplans to a temporary table
    process.stdin.write('''
      create temporary table tmp_operationplan (
        name character varying(1000),
        type character varying(5) NOT NULL,
        status character varying(20),
        reference character varying(300),
        quantity numeric(15,4) NOT NULL,
        startdate timestamp with time zone,
        enddate timestamp with time zone,
        criticality numeric(15,4),
        delay numeric,
        plan json,
        source character varying(300),
        lastmodified timestamp with time zone NOT NULL,
        operation_id character varying(300),
        owner_id integer,
        item_id character varying(300),
        destination_id character varying(300),
        origin_id character varying(300),        
        location_id character varying(300),
        supplier_id character varying(300),  
        demand_id character varying(300),
        due timestamp with time zone,
        id integer NOT NULL
      ); 
      '''.encode(self.encoding))
    process.stdin.write('''COPY tmp_operationplan
      (name,type,status,reference,quantity,startdate,enddate,
      criticality,delay,plan,source,lastmodified,
      operation_id,owner_id,
      item_id,destination_id,origin_id,
      location_id,supplier_id,
      demand_id,due,id) FROM STDIN;\n'''.encode(self.encoding))
    for p in getOperationPlans():
      process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % p).encode(self.encoding))
    process.stdin.write('\\.\n'.encode(self.encoding))

    # Merge temp table into the actual table
    process.stdin.write('''
      update operationplan 
        set name=tmp.name, type=tmp.type, status=tmp.status, reference=tmp.reference, 
        quantity=tmp.quantity, startdate=tmp.startdate, enddate=tmp.enddate,
        criticality=tmp.criticality, delay=tmp.delay * interval '1 second', 
        plan=tmp.plan, source=tmp.source,
        lastmodified=tmp.lastmodified, operation_id=tmp.operation_id, owner_id=tmp.owner_id,
        item_id=tmp.item_id, destination_id=tmp.destination_id, origin_id=tmp.origin_id,
        location_id=tmp.location_id, supplier_id=tmp.supplier_id, demand_id=tmp.demand_id,
        due=tmp.due
      from tmp_operationplan as tmp
      where operationplan.id = tmp.id;
      '''.encode(self.encoding))
    process.stdin.write('''
      insert into operationplan
        (name,type,status,reference,quantity,startdate,enddate,
        criticality,delay,plan,source,lastmodified,
        operation_id,owner_id,
        item_id,destination_id,origin_id,
        location_id,supplier_id,
        demand_id,due,id)
      select name,type,status,reference,quantity,startdate,enddate,
        criticality,delay * interval '1 second',plan,source,lastmodified,
        operation_id,owner_id,
        item_id,destination_id,origin_id,
        location_id,supplier_id,
        demand_id,due,id
      from tmp_operationplan
      where not exists (
        select 1 
        from operationplan 
        where operationplan.id = tmp_operationplan.id
        );
      '''.encode(self.encoding))
    
    if self.verbosity:
      print('Exported operationplans in %.2f seconds' % (time() - starttime))


  def exportOperationPlanMaterials(self, process):
    if self.verbosity:
      print("Exporting operationplan materials...")
    starttime = time()
    process.stdin.write(
      ('COPY operationplanmaterial '
      '(operationplan_id, buffer, quantity, flowdate, onhand) '
      'FROM STDIN;\n').encode(self.encoding)
      )
    for i in frepple.buffers():
      if self.cluster != -1 and self.cluster != i.cluster:
        continue
      for j in i.flowplans:
        process.stdin.write(("%s\t%s\t%s\t%s\t%s\n" % (
           j.operationplan.id, j.buffer.name,
           round(j.quantity, 6),
           str(j.date), round(j.onhand, 6)
           )).encode(self.encoding))
    process.stdin.write('\\.\n'.encode(self.encoding))
    if self.verbosity:
      print('Exported operationplan materials in %.2f seconds' % (time() - starttime))


  def exportOperationPlanResources(self, process):
    if self.verbosity:
      print("Exporting operationplan resources...")
    starttime = time()
    process.stdin.write(
      ('COPY operationplanresource '
      '(operationplan_id, resource, quantity, startdate, enddate, setup) '
      'FROM STDIN;\n').encode(self.encoding)
      )
    for i in frepple.resources():
      if self.cluster != -1 and self.cluster != i.cluster:
        continue
      for j in i.loadplans:
        if j.quantity < 0:
          process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\n" % (
            j.operationplan.id, j.resource.name,
            round(-j.quantity, 6),
            str(j.startdate), str(j.enddate),
            j.setup and j.setup or "\\N"
            )).encode(self.encoding))
    process.stdin.write('\\.\n'.encode(self.encoding))
    if self.verbosity:
      print('Exported operationplan resources in %.2f seconds' % (time() - starttime))


  def exportResourceplans(self, process):
    if self.verbosity:
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
      if self.cluster != -1 and self.cluster != i.cluster:
        continue
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
    process.stdin.write('COPY out_resourceplan (resource,startdate,available,unavailable,setup,load,free) FROM STDIN;\n'.encode(self.encoding))
    for i in frepple.resources():
      for j in i.plan(buckets):
        process.stdin.write(("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
         i.name, str(j['start']),
         round(j['available'], 6),
         round(j['unavailable'], 6),
         round(j['setup'], 6),
         round(j['load'], 6),
         round(j['free'], 6)
         )).encode(self.encoding))
    process.stdin.write('\\.\n'.encode(self.encoding))
    if self.verbosity:
      print('Exported resourceplans in %.2f seconds' % (time() - starttime))


  def exportPegging(self, process):

    def getDemandPlan():
      for i in frepple.demands():
        if self.cluster != -1 and self.cluster != i.cluster:
          continue
        if i.hidden or not isinstance(i, frepple.demand_default):
          continue
        peg = []
        for j in i.pegging:
          peg.append({
            'level': j.level,
            'opplan': j.operationplan.id,
            'quantity': j.quantity
            })
        yield (json.dumps({'pegging': peg}), i.name)

    print("Exporting demand pegging...")
    starttime = time()
    with transaction.atomic(using=self.database, savepoint=False):
      cursor = connections[self.database].cursor()
      cursor.executemany(
        "update demand set plan=%s where name=%s",
        [ i for i in getDemandPlan() ]
        )
    print('Exported demand pegging in %.2f seconds' % (time() - starttime))




  def run(self):
    '''
    This function exports the data from the frePPLe memory into the database.
    The export runs in parallel over 2 connections to PostgreSQL.
    '''
    # Truncate
    task = DatabasePipe(self, export.truncate)
    task.start()
    task.join()

    # Export process
    tasks = (
      DatabasePipe(
        self,
        export.exportResourceplans, export.exportProblems, export.exportConstraints
        ),
      DatabasePipe(
        self,
        export.exportOperationplans, export.exportOperationPlanMaterials,
        export.exportOperationPlanResources, export.exportPegging
        )
      )
    # Start all threads
    for i in tasks:
      i.start()
    # Wait for all threads to finish
    for i in tasks:
      i.join()

    # Report on the output
    if self.verbosity:
      cursor = connections[self.database].cursor()
      cursor.execute('''
        select 'out_problem', count(*) from out_problem
        union select 'out_constraint', count(*) from out_constraint
        union select 'operationplanmaterial', count(*) from operationplanmaterial
        union select 'operationplanresource', count(*) from operationplanresource
        union select 'out_resourceplan', count(*) from out_resourceplan
        union select 'operationplan', count(*) from operationplan
        order by 1
        ''')
      for table, recs in cursor.fetchall():
        print("Table %s: %d records" % (table, recs))


  def run_sequential(self):
    '''
    This function exports the data from the frePPLe memory into the database.
    The export runs sequentially over s single connection to PostgreSQL.
    '''
    test = 'FREPPLE_TEST' in os.environ

    # Start a PSQL process
    my_env = os.environ
    if settings.DATABASES[self.database]['PASSWORD']:
      my_env['PGPASSWORD'] = settings.DATABASES[self.database]['PASSWORD']
    #process = Popen("psql -q -w %s%s%s%s" % (
    process = Popen("psql -w %s%s%s%s" % (
       settings.DATABASES[self.database]['USER'] and ("-U %s " % settings.DATABASES[self.database]['USER']) or '',
       settings.DATABASES[self.database]['HOST'] and ("-h %s " % settings.DATABASES[self.database]['HOST']) or '',
       settings.DATABASES[self.database]['PORT'] and ("-p %s " % settings.DATABASES[self.database]['PORT']) or '',
       test and settings.DATABASES[self.database]['TEST']['NAME'] or settings.DATABASES[self.database]['NAME'],
     ), stdin=PIPE, stderr=PIPE, bufsize=0, shell=True, env=my_env)
    if process.returncode is None:
      # PSQL session is still running
      process.stdin.write("SET statement_timeout = 0;\n".encode(self.encoding))
      process.stdin.write("SET client_encoding = 'UTF8';\n".encode(self.encoding))

    # Send all output to the PSQL process through a pipe
    try:
      self.truncate(process)
      self.exportProblems(process)
      self.exportConstraints(process)
      self.exportOperationplans(process)
      self.exportOperationPlanMaterials(process)
      self.exportOperationPlanResources(process)
      self.exportResourceplans(process)
      self.exportPegging(process)
    finally:
      # Print any error messages
      msg = process.communicate()[1]
      if msg:
        print(msg)
      # Close the pipe and PSQL process
      if process.returncode is None:
        # PSQL session is still running.
        process.stdin.write('\\q\n'.encode(self.encoding))
      process.stdin.close()

    if self.verbosity:
      cursor = connections[self.database].cursor()
      cursor.execute('''
        select 'out_problem', count(*) from out_problem
        union select 'out_constraint', count(*) from out_constraint
        union select 'operationplan', count(*) from operationplan
        union select 'operationplanmaterial', count(*) from operationplanmaterial
        union select 'operationplanresource', count(*) from operationplanresource
        union select 'out_resourceplan', count(*) from out_resourceplan
        order by 1
        ''')
      for table, recs in cursor.fetchall():
        print("Table %s: %d records" % (table, recs or 0))
