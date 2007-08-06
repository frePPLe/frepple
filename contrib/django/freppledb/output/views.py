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

from django.core.paginator import ObjectPaginator, InvalidPage
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader
from django.db import connection
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.conf import settings

from datetime import date, datetime

from freppledb.input.models import Buffer, Flow, Operation, Plan, Resource, Item, Demand, Forecast
from freppledb.dbutils import *

# Parameter settings
PAGINATE_BY = 50       # Number of entities displayed on a page
ON_EACH_SIDE = 3       # Number of pages show left and right of the current page
ON_ENDS = 2            # Number of pages shown at the start and the end of the page list
CACHE_SQL_QUERY = 10   # Time in minutes during which results of SQL queries are cached

# A variable to cache bucket information in memory
datelist = {}

def getBuckets(request, bucket=None, start=None, end=None):
  '''
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table dates, and are
  stored in the django memory cache for performance reasons
  '''
  global datelist
  # Pick up the arguments
  if not bucket:
    bucket = request.GET.get('bucket')
    if not bucket:
      try: bucket = request.user.get_profile().buckets
      except: bucket = 'month'
  if not start:
    start = request.GET.get('start')
    if start:
      try:
        (y,m,d) = start.split('-')
        start = date(int(y),int(m),int(d))
      except:
        try: start = request.user.get_profile().startdate
        except: pass
        if not start: start = Plan.objects.all()[0].currentdate.date()
    else:
      try: start = request.user.get_profile().startdate
      except: pass
      if not start: start = Plan.objects.all()[0].currentdate.date()
  if not end:
    end = request.GET.get('end')
    if end:
      try:
        (y,m,d) = end.split('-')
        end = date(int(y),int(m),int(d))
      except:
        try: end = request.user.get_profile().enddate
        except: pass
        if not end: end = date(2030,1,1)
    else:
      try: end = request.user.get_profile().enddate
      except: pass
      if not end: end = date(2030,1,1)

  # Check if the argument is valid
  if bucket not in ('day','week','month','quarter','year'):
    raise Http404, "bucket name %s not valid" % bucket

  # Pick up the buckets from the cache
  if not bucket in datelist:
    # Read the buckets from the database if the data isn't in the cache yet
    cursor = connection.cursor()
    cursor.execute('''
      select %s, min(day), max(day)
      from dates
      group by %s
      order by min(day)''' % (bucket,bucket))
    # Compute the data to store in memory
    if settings.DATABASE_ENGINE == 'sqlite3':
      # Sigh... Poor data type handling in sqlite
      datelist[bucket] = [{
        'name': i,
        'start': datetime.strptime(j,'%Y-%m-%d').date(),
        'end': datetime.strptime(k,'%Y-%m-%d').date()
        } for i,j,k in cursor.fetchall()]
    else:
      datelist[bucket] = [{'name': i, 'start': j, 'end': k} for i,j,k in cursor.fetchall()]

  # Filter based on the start and end date
  if start and end:
    res = filter(lambda b: b['start'] <= end and b['end'] >= start, datelist[bucket])
  elif end:
    res = filter(lambda b: b['start'] <= end, datelist[bucket])
  elif start:
    res = filter(lambda b: b['end'] >= start, datelist[bucket])
  else:
    res = datelist[bucket]
  return (bucket,start,end,res)


def BucketedView(request, entity, querymethod, htmltemplate, csvtemplate, extra_context=None, countmethod=None):
  global ON_EACH_SIDE
  global ON_ENDS
  global PAGINATE_BY

  # Pick up the list of time buckets
  (bucket,start,end,bucketlist) = getBuckets(request)

  # HTML output or CSV output?
  type = request.GET.get('type','html')
  if type == 'csv':
    # CSV output
    c = RequestContext(request, {
       'objectlist': querymethod(entity, bucket, start, end),
       'bucket': bucket,
       'startdate': start,
       'enddate': end,
       'bucketlist': bucketlist,
       })
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % csvtemplate
    response.write(loader.get_template(csvtemplate).render(c))
    return response

  # Create a copy of the request url parameters
  parameters = request.GET.copy()
  parameters.__setitem__('p', 0)

  # Calculate the content of the page
  page = int(request.GET.get('p', '0'))
  if countmethod:
    paginator = ObjectPaginator(countmethod, PAGINATE_BY)
    try: results = querymethod(entity, bucket, start, end, offset=paginator.first_on_page(page)-1, limit=PAGINATE_BY)
    except InvalidPage: raise Http404
  else:
    paginator = ObjectPaginator(querymethod(entity, bucket, start, end), PAGINATE_BY)
    try: results = paginator.get_page(page)
    except InvalidPage: raise Http404

  # If there are less than 10 pages, show them all
  page_htmls = []
  if paginator.pages <= 10:
    for n in range(0,paginator.pages):
      parameters.__setitem__('p', n)
      if n == page:
        page_htmls.append('<span class="this-page">%d</span>' % (page+1))
      else:
        page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
  else:
      # Insert "smart" pagination links, so that there are always ON_ENDS
      # links at either end of the list of pages, and there are always
      # ON_EACH_SIDE links at either end of the "current page" link.
      if page <= (ON_ENDS + ON_EACH_SIDE):
          # 1 2 *3* 4 5 6 ... 99 100
          for n in range(0, page + max(ON_EACH_SIDE, ON_ENDS)+1):
            if n == page:
              page_htmls.append('<span class="this-page">%d</span>' % (page+1))
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_EACH_SIDE, paginator.pages-1):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
      elif page >= (paginator.pages - ON_EACH_SIDE - ON_ENDS - 2):
          # 1 2 ... 95 96 97 *98* 99 100
          for n in range(0, ON_ENDS):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(page - max(ON_EACH_SIDE, ON_ENDS), paginator.pages - 1):
            if n == page:
              page_htmls.append('<span class="this-page">%d</span>' % (page+1))
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n+1))
      else:
          # 1 2 ... 45 46 47 *48* 49 50 51 ... 99 100
          for n in range(0, ON_ENDS):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(page - ON_EACH_SIDE, page + ON_EACH_SIDE + 1):
            if n == page:
              page_htmls.append('<span class="this-page">%s</span>' % (page+1))
            elif n == '.':
              page_htmls.append('...')
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_ENDS - 1, paginator.pages - 1):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n+1))
  context = {
       'objectlist': results,
       'bucket': bucket,
       'startdate': start,
       'enddate': end,
       'bucketlist': bucketlist,
       'paginator': paginator,
       'is_paginated': paginator.pages > 1,
       'has_next': paginator.has_next_page(page - 1),
       'has_previous': paginator.has_previous_page(page - 1),
       'current_page': page,
       'next_page': page + 1,
       'previous_page': page - 1,
       'pages': paginator.pages,
       'hits' : paginator.hits,
       'page_htmls': page_htmls,
     }
  if extra_context: context.update(extra_context)
  return render_to_response(htmltemplate,  context, context_instance=RequestContext(request))


def bufferquery(buffer, bucket, startdate, enddate, offset=0, limit=None):
  if buffer: filterstring = 'where name = %s'
  else: filterstring = ''
  if limit:
    if offset == 0: limitstring = 'limit %d' % int(limit)
    else: limitstring = 'limit %d offset %d' % (int(limit),int(offset))
  else: limitstring = ''
  cursor = connection.cursor()
  query = '''
    select combi.thebuffer_id,
           combi.item_id,
           combi.location_id,
           combi.onhand,
           combi.bucket,
           coalesce(data.produced,0.0),
           coalesce(data.consumed,0.0)
      from
       (select name as thebuffer_id, location_id, item_id, onhand, d.bucket as bucket, d.start as start
        from
          (select name, location_id, item_id, onhand from buffer %s order by name %s) as buffer
        cross join (select %s as bucket , min(day) as start from dates where day >= '%s'
          and day < '%s' group by bucket) d
       ) as combi
      left join
       (select thebuffer_id, %s as bucket,
          sum(%s) as produced,
          -sum(%s) as consumed
          from out_flowplan,
               dates,
               (select name from buffer %s order by name %s) as buffer
          where out_flowplan.flowdate = dates.day
          and out_flowplan.flowdate >= '%s'
          and out_flowplan.flowdate < '%s'
          and thebuffer_id = buffer.name
          group by thebuffer_id, bucket
        ) data
      on combi.thebuffer_id = data.thebuffer_id
      and combi.bucket = data.bucket
      order by combi.thebuffer_id, combi.start
    ''' % (filterstring,limitstring,bucket,startdate,enddate,bucket,
           sql_max('quantity','0.0'),sql_min('quantity','0.0'),filterstring, limitstring,
           startdate,enddate)
  if buffer: cursor.execute(query, (buffer,buffer))
  else: cursor.execute(query)
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
    endoh += float(row[5] - row[6])
    rowset.append( {
      'buffer': row[0],
      'item': row[1],
      'location': row[2],
      'bucket': row[4],
      'startoh': startoh,
      'produced': row[5],
      'consumed': row[6],
      'endoh': endoh,
      } )
  if prevbuf: resultset.append(rowset)
  return resultset


@staff_member_required
def bufferreport(request, buffer=None):
  if buffer:
    return BucketedView(request, buffer, bufferquery,
      'buffer.html', 'buffer.csv',
      {'title': 'Inventory report for %s' % buffer, 'reset_crumbs': False}
      )
  else:
    return BucketedView(request, buffer, bufferquery,
      'buffer.html', 'buffer.csv',
      {'title': 'Inventory report', 'reset_crumbs': True},
      countmethod=Buffer.objects
      )


def demandquery(item, bucket, startdate, enddate, offset=0, limit=None):
  if item: filterstring = 'where item_id = %s'
  else: filterstring = ''
  if limit:
    if offset == 0: limitstring = 'limit %d' % int(limit)
    else: limitstring = 'limit %d offset %d' % (int(limit),int(offset))
  else: limitstring = ''
  cursor = connection.cursor()
  query = '''
      select combi.item_id,
             combi.bucket,
             coalesce(data.demand,0),
             coalesce(data2.planned,0)
      from
       (select item_id, d.bucket as bucket, d.start as start
        from (select distinct item_id from demand %s order by item_id %s) as items
        cross join (select %s as bucket, min(day) as start from dates where day >= '%s'
          and day < '%s' group by bucket) d
       ) as combi
      -- Planned quantity
      left join
       (select items.item_id as item_id, %s as bucket, sum(out_operationplan.quantity) as planned
        from out_operationplan, dates as d, demand as inp,
          (select distinct item_id from demand %s order by item_id %s) as items
        where out_operationplan.enddate = d.day
        and out_operationplan.demand_id = inp.name
        and inp.item_id = items.item_id
        and out_operationplan.enddate >= '%s'
        and out_operationplan.enddate < '%s'
        group by items.item_id, bucket) data2
      on combi.item_id = data2.item_id
      and combi.bucket = data2.bucket
      -- Requested quantity
      left join
       (select items.item_id as item_id, %s as bucket, sum(inp.quantity) as demand
            from dates as d, demand as inp,
              (select distinct item_id from demand %s order by item_id %s) as items
            where date(inp.due) = d.day
            and inp.due >= '%s'
            and inp.due < '%s'
            and inp.item_id = items.item_id
            group by items.item_id, bucket) data
      on combi.item_id = data.item_id
      and combi.bucket = data.bucket
      -- Sort the result
      order by combi.item_id, combi.start
     ''' % (filterstring, limitstring,bucket,startdate,enddate,
            bucket,filterstring,limitstring,startdate,enddate,
            bucket,filterstring,limitstring,startdate,enddate)
  if item: cursor.execute(query, (item,item,item))
  else: cursor.execute(query)
  resultset = []
  previtem = None
  rowset = []
  for row in cursor.fetchall():
    if row[0] != previtem:
      if previtem: resultset.append(rowset)
      rowset = []
      previtem = row[0]
      backlog = 0         # @todo Setting the backlog to 0 is not correct: it may be non-zero from the plan before the start date
    backlog += row[2] - row[3]
    rowset.append( {
      'item': row[0],
      'bucket': row[1],
      'requested': row[2],
      'supplied': row[3],
      'backlog': backlog,
      } )
  if previtem: resultset.append(rowset)
  return resultset


@staff_member_required
def demandreport(request, item=None):
  if item:
    return BucketedView(request, item, demandquery,
      'demand.html', 'demand.csv',
      {'title': 'Demand report for %s' % item, 'reset_crumbs': False}
      )
  else:
    return BucketedView(request, item, demandquery,
      'demand.html', 'demand.csv',
      {'title': 'Demand report', 'reset_crumbs': True},
      countmethod=Demand.objects.values('item').distinct()
      )


def forecastquery(fcst, bucket, startdate, enddate, offset=0, limit=None):
  if fcst: filterstring = 'where name = %s'
  else: filterstring = ''
  if limit:
    if offset == 0: limitstring = 'limit %d' % int(limit)
    else: limitstring = 'limit %d offset %d' % (int(limit),int(offset))
  else: limitstring = ''
  cursor = connection.cursor()
  query = '''
      select fcst.name, fcst.item_id, fcst.customer_id,
             d.bucket, d.startdate, d.enddate,
             coalesce(sum(forecastdemand.quantity * %s / %s),0) as qty
      from (select * from forecast %s order by name %s) as fcst
      -- Multiply with buckets
      cross join (
           select %s as bucket, %s_start as startdate, %s_end as enddate
           from dates
           where day >= '%s' and day < '%s'
           group by bucket, startdate, enddate
           ) d
      -- Total forecasted quantity
      left join forecastdemand
      on fcst.name = forecastdemand.forecast_id
      and forecastdemand.enddate >= d.startdate
      and forecastdemand.startdate <= d.enddate
      -- Ordering and grouping
      group by fcst.name, fcst.item_id, fcst.customer_id,
             d.bucket, d.startdate, d.enddate
      order by fcst.name, d.startdate
      ''' % (sql_overlap('forecastdemand.startdate','forecastdemand.enddate','d.startdate','d.enddate'),
       sql_datediff('forecastdemand.enddate','forecastdemand.startdate'),filterstring,limitstring,
       bucket,bucket,bucket,startdate,enddate)
  if fcst: cursor.execute(query, (fcst,fcst))
  else: cursor.execute(query)
  resultset = []
  prevfcst = None
  rowset = []
  for row in cursor.fetchall():
    if row[0] != prevfcst:
      if prevfcst: resultset.append(rowset)
      rowset = []
      prevfcst = row[0]
    rowset.append( {
      'name': row[0],
      'item': row[1],
      'customer': row[2],
      'bucket': row[3],
      'startdate': row[4],
      'enddate': row[5],
      'forecast': row[6],
      } )
  if prevfcst: resultset.append(rowset)
  return resultset


@staff_member_required
def forecastreport(request, fcst=None):
  if fcst:
    return BucketedView(request, fcst, forecastquery,
      'forecast.html', 'forecast.csv',
      {'title': 'Forecast report for %s' % fcst, 'reset_crumbs': False}
      )
  else:
    return BucketedView(request, fcst, forecastquery,
      'forecast.html', 'forecast.csv',
      {'title': 'Forecast report', 'reset_crumbs': True},
      countmethod=Forecast.objects.values('item').distinct()
      )


def resourcequery(resource, bucket, startdate, enddate, offset=0, limit=None):
  if resource: filterstring = 'where name = %s'
  else: filterstring = ''
  if limit:
    if offset == 0: limitstring = 'limit %d' % int(limit)
    else: limitstring = 'limit %d offset %d' % (int(limit),int(offset))
  else: limitstring = ''
  cursor = connection.cursor()
  query = '''
     select x.name, x.location_id,
           x.bucket, x.startdate, x.enddate,
           min(x.available),
           coalesce(sum(loaddata.usagefactor * %s), 0) as loading
     from (
       select res.name as name, res.location_id as location_id,
             d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
             coalesce(sum(bucket.value * %s),0) as available
       from (select name, location_id, maximum_id from resource %s order by name %s) as res
       -- Multiply with buckets
       cross join (
            select %s as bucket, %s_start as startdate, %s_end as enddate
            from dates
            where day >= '%s' and day < '%s'
            group by bucket, startdate, enddate
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
       select resourceload.resource_id as resource_id, startdatetime, enddatetime, resourceload.usagefactor as usagefactor
       from out_operationplan, resourceload
       where out_operationplan.operation_id = resourceload.operation_id
       ) loaddata
     on x.name = loaddata.resource_id
     and x.startdate <= loaddata.enddatetime
     and x.enddate >= loaddata.startdatetime
     -- Grouping and ordering
     group by x.name, x.location_id, x.bucket, x.startdate, x.enddate
     order by x.name, x.startdate
     ''' % ( sql_overlap('loaddata.startdatetime','loaddata.enddatetime','x.startdate','x.enddate'),
       sql_overlap('bucket.startdate','bucket.enddate','d.startdate','d.enddate'),
       filterstring,limitstring,bucket,bucket,bucket,startdate,enddate)
  if resource: cursor.execute(query, (resource,resource))
  else: cursor.execute(query)
  resultset = []
  prevres = None
  rowset = []
  for row in cursor.fetchall():
    if row[0] != prevres:
      count = 0
      if prevres: resultset.append(rowset)
      rowset = []
      prevres = row[0]
    if row[5] != 0: util = row[6] / row[5]
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


@staff_member_required
def resourcereport(request, resource=None):
   if resource:
     return BucketedView(request, resource, resourcequery,
      'resource.html', 'resource.csv',
      {'title': 'Resource report for %s' % resource, 'reset_crumbs': False}
      )
   else:
     return BucketedView(request, resource, resourcequery,
      'resource.html', 'resource.csv',
      {'title': 'Resource report', 'reset_crumbs': True},
      countmethod=Resource.objects
      )


def operationquery(operation, bucket, startdate, enddate, offset=0, limit=None):
  if operation: filterstring = 'where name = %s'
  else: filterstring = ''
  if limit:
    if offset == 0: limitstring = 'limit %d' % int(limit)
    else: limitstring = 'limit %d offset %d' % (int(limit),int(offset))
  else: limitstring = ''
  cursor = connection.cursor()
  query = '''
    select oper.name,
           d.bucket, d.startdate, d.enddate,
           coalesce(sum(case out_operationplan.locked when %s then out_operationplan.quantity else 0 end),0),
           coalesce(sum(out_operationplan.quantity),0)
      from (select name from operation %s order by name %s) as oper
      -- Multiply with buckets
      cross join (
           select %s as bucket, %s_start as startdate, %s_end as enddate
           from dates
           where day >= '%s' and day < '%s'
           group by bucket, startdate, enddate
           ) d
      -- Planned and frozen quantity
      left join out_operationplan
      on oper.name = out_operationplan.operation_id
      and d.startdate <= out_operationplan.startdate
      and d.enddate > out_operationplan.startdate
      -- Grouping and ordering
      group by oper.name, d.bucket, d.startdate, d.enddate
      order by oper.name, d.startdate
    ''' % (sql_true(),filterstring,limitstring,bucket,bucket,bucket,startdate,enddate)
  if operation: cursor.execute(query, (operation,operation))
  else: cursor.execute(query)
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
      'frozen': row[4],
      'total': row[5],
      } )
  if prevoper: resultset.append(rowset)
  return resultset


@staff_member_required
def operationreport(request, operation=None):
  if operation:
    return BucketedView(request, operation, operationquery,
      'operation.html', 'operation.csv',
      {'title': 'Operation report for %s' % operation, 'reset_crumbs': False}
      )
  else:
    return BucketedView(request, operation, operationquery,
      'operation.html', 'operation.csv',
      {'title': 'Operation report', 'reset_crumbs': True},
      countmethod=Operation.objects)


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
    #for i in connection.queries: print i
    return render_to_response('path.html', c)
