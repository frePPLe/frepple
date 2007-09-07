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

from datetime import date, datetime

from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader
from django.db import connection
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.conf import settings

from freppledb.input.models import Buffer, Operation, Resource, Item, Forecast
from freppledb.dbutils import *
from freppledb.report import Report


class BufferReport(Report):
  '''
  A report showing the inventory profile of buffers.
  '''
  template = 'buffer.html'
  title = "Inventory report"
  basequeryset = Buffer.objects.all()
  rows = (
    ('buffer', {'filter': 'name__icontains', 'order_by': 'name'}),
    ('item', {'filter': 'item__name__icontains'}),
    ('location', {'filter': 'location__name__icontains'}),
    )
  crosses = (
    ('startoh', {'title':'start inventory',}),
    ('consumed', {}),
    ('produced', {}),
    ('endoh', {'title': 'end inventory',}),
    )
  columns = (
    ('bucket', {}),
    )

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
    query = '''
      select buf.name as row1, buf.item_id as row2, buf.location_id as row3, buf.onhand as row4,
             d.bucket as col1, d.startdate as col2, d.enddate as col3,
             coalesce(sum(%s),0.0) as consumed,
             coalesce(-sum(%s),0.0) as produced
        from (%s) buf
        -- Multiply with buckets
        cross join (
             select %s as bucket, %s_start as startdate, %s_end as enddate
             from dates
             where day_start >= '%s' and day_start <= '%s'
             group by %s, %s_start, %s_end
             ) d
        -- Consumed and produced quantities
        left join out_flowplan
        on buf.name = out_flowplan.thebuffer
        and d.startdate <= out_flowplan.flowdate
        and d.enddate > out_flowplan.flowdate
        -- Grouping and sorting
        group by buf.name, buf.item_id, buf.location_id, buf.onhand, d.bucket, d.startdate, d.enddate
        order by %s, d.startdate
      ''' % (sql_max('out_flowplan.quantity','0.0'),sql_min('out_flowplan.quantity','0.0'),
        basesql,connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
        connection.ops.quote_name(bucket),bucket,bucket,sortsql)
    cursor.execute(query, baseparams)

    # Build the python result
    resultset = []
    prevbuf = None
    rowset = []
    for row in cursor.fetchall():
      if row[0] != prevbuf:
        if prevbuf: resultset.append(rowset)
        rowset = []
        prevbuf = row[0]
        endoh = float(row[3])
      startoh = endoh   # @todo the starting onhand isn't right...
      endoh += float(row[7] - row[8])
      rowset.append( {
        'buffer': row[0],
        'item': row[1],
        'location': row[2],
        'bucket': row[4],
        'startdate': row[5],
        'enddate': row[6],
        'startoh': startoh,
        'produced': row[7],
        'consumed': row[8],
        'endoh': endoh,
        } )
    if prevbuf: resultset.append(rowset)
    return resultset


class DemandReport(Report):
  '''
  A report showing the independent demand for each item.
  '''
  template = 'demand.html'
  title = 'Demand report'
  basequeryset = Item.objects.extra(where=('name in (select item_id from demand)',))
  rows = (
    ('item',{'filter': 'name__icontains', 'order_by': 'name'}),
    )
  crosses = (
    ('demand',{}),
    ('supply',{}),
    ('backlog',{}),
    )
  columns = (
    ('bucket',{}),
    )

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
    query = '''
        select x.name as row1,
               x.bucket as col1, x.startdate as col2, x.enddate as col3,
               coalesce(sum(demand.quantity),0),
               min(x.planned)
        from (
          select items.name as name,
                 d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
                 coalesce(sum(pln.quantity),0) as planned
          from (%s) items
          -- Multiply with buckets
          cross join (
               select %s as bucket, %s_start as startdate, %s_end as enddate
               from dates
               where day_start >= '%s' and day_start <= '%s'
               group by %s, %s_start, %s_end
               ) d
          -- Planned quantity
          left join (
            select item_id as item_id, out_demand.plandate as plandate, out_demand.planquantity as quantity
            from out_demand
            inner join demand
            on out_demand.demand = demand.name
            ) pln
          on items.name = pln.item_id
          and d.startdate <= pln.plandate
          and d.enddate > pln.plandate
          -- Grouping
          group by items.name, d.bucket, d.startdate, d.enddate
        ) x
        -- Requested quantity
        left join demand
        on x.name = demand.item_id
        and x.startdate <= demand.due
        and x.enddate > demand.due
        -- Ordering and grouping
        group by x.name, x.bucket, x.startdate, x.enddate
        order by %s, x.startdate
       ''' % (basesql,connection.ops.quote_name(bucket),bucket,bucket,
       startdate,enddate,connection.ops.quote_name(bucket),bucket,bucket,sortsql)
    cursor.execute(query,baseparams)

    # Build the python result
    resultset = []
    previtem = None
    rowset = []
    for row in cursor.fetchall():
      if row[0] != previtem:
        if previtem: resultset.append(rowset)
        rowset = []
        previtem = row[0]
        backlog = 0         # @todo Setting the backlog to 0 is not correct: it may be non-zero from the plan before the start date
      backlog += row[4] - row[5]
      rowset.append( {
        'item': row[0],
        'bucket': row[1],
        'startdate': row[2],
        'enddate': row[3],
        'demand': row[4],
        'supply': row[5],
        'backlog': backlog,
        } )
    if previtem: resultset.append(rowset)
    return resultset


class ForecastReport(Report):
  '''
  A report allowing easy editing of forecast numbers.
  '''
  template = 'forecast.html'
  title = 'Forecast report'
  basequeryset = Forecast.objects.all()
  rows = (
    ('forecast',{'filter': 'name__icontains', 'order_by': 'name'}),
    ('item',{'filter': 'item__name__icontains'}),
    ('customer',{'filter': 'customer__name__icontains'}),
    )
  crosses = (
    ('total',{}),
    )
  columns = (
    ('bucket',{}),
    )

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
    query = '''
        select fcst.name as row1, fcst.item_id as row2, fcst.customer_id as row3,
               d.bucket as col1, d.startdate as col2, d.enddate as col3,
               coalesce(sum(forecastdemand.quantity * %s / %s),0) as qty
        from (%s) fcst
        -- Multiply with buckets
        cross join (
             select %s as bucket, %s_start as startdate, %s_end as enddate
             from dates
             where day_start >= '%s' and day_start <= '%s'
             group by %s, %s_start, %s_end
             ) d
        -- Total forecasted quantity
        left join forecastdemand
        on fcst.name = forecastdemand.forecast_id
        and forecastdemand.enddate >= d.startdate
        and forecastdemand.startdate <= d.enddate
        -- Ordering and grouping
        group by fcst.name, fcst.item_id, fcst.customer_id,
          d.bucket, d.startdate, d.enddate
        order by %s, d.startdate
        ''' % (sql_overlap('forecastdemand.startdate','forecastdemand.enddate','d.startdate','d.enddate'),
         sql_datediff('forecastdemand.enddate','forecastdemand.startdate'),
         basesql,connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
         connection.ops.quote_name(bucket),bucket,bucket,sortsql)
    cursor.execute(query, baseparams)

    # Build the python result
    resultset = []
    prevfcst = None
    rowset = []
    for row in cursor.fetchall():
      if row[0] != prevfcst:
        if prevfcst: resultset.append(rowset)
        rowset = []
        prevfcst = row[0]
      rowset.append( {
        'forecast': row[0],
        'item': row[1],
        'customer': row[2],
        'bucket': row[3],
        'startdate': row[4],
        'enddate': row[5],
        'total': row[6],
        } )
    if prevfcst: resultset.append(rowset)
    return resultset


class ResourceReport(Report):
  '''
  A report showing the loading of each resource.
  '''
  template = 'resource.html'
  title = 'Resource report'
  basequeryset = Resource.objects.all()
  rows = (
    ('resource',{'filter': 'name__icontains', 'order_by': 'name'}),
    ('location',{'filter': 'location__name__icontains'}),
    )
  crosses = (
    ('available',{}),
    ('load',{}),
    ('utilization',{'title':'utilization %',}),
    )
  columns = (
    ('bucket',{}),
    )

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
    query = '''
       select x.name as row1, x.location_id as row2,
             x.bucket as col1, x.startdate as col2, x.enddate as col3,
             min(x.available),
             coalesce(sum(loaddata.usagefactor * %s), 0) as loading
       from (
         select res.name as name, res.location_id as location_id,
               d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
               coalesce(sum(bucket.value * %s),0) as available
         from (%s) res
         -- Multiply with buckets
         cross join (
              select %s as bucket, %s_start as startdate, %s_end as enddate
              from dates
              where day_start >= '%s' and day_start <= '%s'
              group by %s, %s_start, %s_end
              ) d
         -- Available capacity
         left join bucket
         on res.maximum_id = bucket.calendar_id
         and d.startdate <= bucket.enddate
         and d.enddate >= bucket.startdate
         -- Grouping
         group by res.name, res.location_id, d.bucket, d.startdate, d.enddate
       ) x
       -- Load data
       left join (
         select %s as resource_id, startdatetime, enddatetime, quantity as usagefactor
         from out_loadplan
         ) loaddata
       on x.name = loaddata.resource_id
       and x.startdate <= loaddata.enddatetime
       and x.enddate >= loaddata.startdatetime
       -- Grouping and ordering
       group by x.name, x.location_id, x.bucket, x.startdate, x.enddate
       order by %s, x.startdate
       ''' % ( sql_overlap('loaddata.startdatetime','loaddata.enddatetime','x.startdate','x.enddate'),
         sql_overlap('bucket.startdate','bucket.enddate','d.startdate','d.enddate'),
         basesql,connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
         connection.ops.quote_name(bucket),bucket,bucket,connection.ops.quote_name('resource'),sortsql)
    cursor.execute(query, baseparams)

    # Build the python result
    resultset = []
    prevres = None
    rowset = []
    for row in cursor.fetchall():
      if row[0] != prevres:
        count = 0
        if prevres: resultset.append(rowset)
        rowset = []
        prevres = row[0]
      if row[5] != 0: util = row[6] / row[5] * 100
      else: util = 0
      count += 1
      rowset.append( {
        'resource': row[0],
        'location': row[1],
        'bucket': row[2],
        'startdate': row[3],
        'enddate': row[4],
        'available': row[5],
        'load': row[6],
        'utilization': util,
        } )
    if prevres: resultset.append(rowset)
    return resultset


class OperationReport(Report):
  '''
  A report showing the planned starts of each operation.
  '''
  template = 'operation.html'
  title = 'Operation report'
  basequeryset = Operation.objects.all()
  rows = (
    ('operation',{'filter': 'name__icontains', 'order_by': 'name'}),
    )
  crosses = (
    ('frozen_start', {'title':'frozen starts',}),
    ('total_start', {'title':'total starts',}),
    ('frozen_end', {'title':'frozen ends',}),
    ('total_end', {'title':'total ends',}),
    )
  columns = (
    ('bucket',{}),
    )

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Run the query
    cursor = connection.cursor()
    query = '''
        select x.row1, x.col1, x.col2, x.col3,
          min(x.frozen_start), min(x.total_start),
          coalesce(sum(case o2.locked when %s then o2.quantity else 0 end),0),
          coalesce(sum(o2.quantity),0)
        from (
          select oper.name as row1,
               d.bucket as col1, d.startdate as col2, d.enddate as col3,
               coalesce(sum(case o1.locked when %s then o1.quantity else 0 end),0) as frozen_start,
               coalesce(sum(o1.quantity),0) as total_start
          from (%s) oper
          -- Multiply with buckets
          cross join (
               select %s as bucket, %s_start as startdate, %s_end as enddate
               from dates
               where day_start >= '%s' and day_start <= '%s'
               group by %s, %s_start, %s_end
               ) d
          -- Planned and frozen quantity, based on start date
          left join out_operationplan o1
          on oper.name = o1.operation
          and d.startdate <= o1.startdate
          and d.enddate > o1.startdate
          -- Grouping
          group by oper.name, d.bucket, d.startdate, d.enddate
        ) x
        -- Planned and frozen quantity, based on end date
        left join out_operationplan o2
        on x.row1 = o2.operation
        and x.col2 <= o2.enddate
        and x.col3 > o2.enddate
        -- Grouping and ordering
        group by x.row1, x.col1, x.col2, x.col3
        order by %s, x.col2
      ''' % (sql_true(),sql_true(),basesql,
      connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
      connection.ops.quote_name(bucket),bucket,bucket,sortsql)
    cursor.execute(query, baseparams)

    # Convert the SQl results to python
    resultset = []
    prevoper = None
    rowset = []
    for row in cursor.fetchall():
      if row[0] != prevoper:
        if prevoper: resultset.append(rowset)
        rowset = []
        prevoper = row[0]
      rowset.append( {
        'operation': row[0],
        'bucket': row[1],
        'startdate': row[2],
        'enddate': row[3],
        'frozen_start': row[4],
        'total_start': row[5],
        'frozen_end': row[6],
        'total_end': row[7],
        } )
    if prevoper: resultset.append(rowset)
    return resultset


class pathreport:
  @staticmethod
  def getPath(type, entity):
    if type == 'buffer':
      # Find the buffer
      try: root = [Buffer.objects.get(name=entity)]
      except DoesNotExist: raise Http404, "buffer %s doesn't exist" % entity
    elif type == 'operation':
      # Find the operation
      try: root = [Operation.objects.get(name=entity)]
      except DoesNotExist: raise Http404, "operation %s doesn't exist" % entity
    elif type == 'item':
      # Find the item
      try: root = [Item.objects.get(name=entity).operation]
      except DoesNotExist: raise Http404, "item %s doesn't exist" % entity
    elif type == 'resource':
      # Find the resource
      try: root = Resource.objects.get(name=entity)
      except DoesNotExist: raise Http404, "resource %s doesn't exist" % entity
      root = [i.operation for i in root.loads.all()]
    else:
      raise Http404, "invalid entity type %s" % type

    # Initialize
    resultset = []

    for r in root:
        level = 0
        bufs = [ (r, None, 1) ]

        # Recurse deeper in the supply chain
        while len(bufs) > 0:
           level += 1
           newbufs = []
           for i, fl, q in bufs:

              # Recurse upstream for a buffer
              if isinstance(i,Buffer):
                f = None
                if i.producing != None:
                  x = i.producing.flows.all()
                  for j in x:
                     if j.thebuffer == i: f = j
                  for j in x:
                     if j.quantity < 0:
                       # Found a new buffer
                       if f is None:
                         newbufs.append( (j.thebuffer, j, - q * j.quantity) )
                       else:
                         newbufs.append( (j.thebuffer, j, - q * j.quantity / f.quantity) )
                # Append to the list of buffers
                resultset.append( {
                  'buffer': i,
                  'producingflow': f,
                  'operation': i.producing,
                  'level': level,
                  'consumingflow': fl,
                  'cumquantity': q,
                  } )

              # Recurse upstream for an operation
              elif isinstance(i,Operation):
                # Flows on the main operation
                for j in i.flows.all():
                   if j.quantity < 0:
                     # Found a new buffer
                     newbufs.append( (j.thebuffer, j, - q * j.quantity) )
                # Flows on suboperations
                for k in i.suboperations.all():
                   for j in k.suboperation.flows.all():
                     if j.quantity < 0:
                       # Found a new buffer
                       newbufs.append( (j.thebuffer, j, - q * j.quantity) )
                # Append to the list of buffers
                resultset.append( {
                  'buffer': None,
                  'producingflow': None,
                  'operation': i,
                  'level': level,
                  'consumingflow': fl,
                  'cumquantity': q,
                  } )
           bufs = newbufs

    # Return results
    return resultset

  @staticmethod
  @staff_member_required
  def view(request, type, entity):
    c = RequestContext(request,{
       'title': "Supply path of %s %s" % (type, entity),
       'supplypath': pathreport.getPath(type, entity),
       'type': type,
       'entity': entity,
       })
    # Uncomment the next line to see the SQL statements executed for the report
    # With the complex logic there can be quite a lot!
    #for i in connection.queries: print i['time'], i['sql']
    return render_to_response('path.html', c)
