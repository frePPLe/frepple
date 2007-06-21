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

from datetime import date

from freppledb.input.models import Buffer, Flow, Operation, Plan, Resource, Item

# Parameter settings
PAGINATE_BY = 50       # Number of entities displayed on a page
ON_EACH_SIDE = 3       # Number of pages show left and right of the current page
ON_ENDS = 2            # Number of pages shown at the start and the end of the page list
CACHE_SQL_QUERY = 10   # Time in minutes during which results of SQL queries are cached

def getBuckets(request, bucket=None, start=None, end=None):
  '''
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table input_dates, and are
  stored in the django memory cache for performance reasons
  '''
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
        if not start: start = Plan.objects.all()[0].current.date()
    else:
      try: start = request.user.get_profile().startdate
      except: pass
      if not start: start = Plan.objects.all()[0].current.date()
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
  dates = cache.get(bucket)

  # Read the buckets from the database if the data isn't in the cache yet
  if not dates:
    cursor = connection.cursor()
    cursor.execute('''
      select %s, min(day), max(day)
      from input_dates
      group by %s
      order by min(day)''' % (bucket,bucket))
    dates = [ {'name': i, 'start': j, 'end': k} for i,j,k in cursor.fetchall() ]
    cache.set(bucket, dates, 24 * 7 * 3600)  # Cache for 7 days

  # Filter based on the start and end date
  if start and end:
    res = []
    for i in dates:
      if i['start'] <= end and i['end'] >= start: res.append(i)
  elif end:
    res = []
    for i in dates:
      if i['start'] >= end: res.append(i)
  elif start:
    res = []
    for i in dates:
      if i['end'] >= start: res.append(i)
  else:
    return (bucket,start,end,dates)
  return (bucket,start,end,res)


def BucketedView(request, entity, querymethod, htmltemplate, csvtemplate, extra_context=None):
    global ON_EACH_SIDE
    global ON_ENDS
    global PAGINATE_BY
    (bucket,start,end,bucketlist) = getBuckets(request)

    # Look up the data in the cache
    parameters = request.GET.copy()
    parameters.__setitem__('page', 0)
    objectlist = None
    if entity is None:
      key = (request.path,bucket,start,end)
      objectlist = cache.get(key)
    if not objectlist:
      # Data not found in the cache, recompute
      objectlist = querymethod(entity, bucket, start, end)
      if entity is None:
        cache.set(key, objectlist, CACHE_SQL_QUERY * 60)

    # HTML output or CSV output?
    type = request.GET.get('type','html')
    if type == 'csv':
      # CSV output
      (bucket,start,end,bucketlist) = getBuckets(request)
      c = RequestContext(request, {
         'objectlist': objectlist,
         'bucket': bucket,
         'startdate': start,
         'enddate': end,
         'bucketlist': bucketlist,
         })
      response = HttpResponse(mimetype='text/csv')
      response['Content-Disposition'] = 'attachment; filename=%s' % csvtemplate
      response.write(loader.get_template(csvtemplate).render(c))
      return response

    page = int(request.GET.get('page', '1'))
    paginator = ObjectPaginator(objectlist, PAGINATE_BY, 1)
    try: results = paginator.get_page(page - 1)
    except InvalidPage: raise Http404
    page_htmls = []

    # If there are less than 10 pages, show them all
    if paginator.pages <= 10:
      for n in range(1,paginator.pages+1):
        parameters.__setitem__('page', n)
        if n == page:
          page_htmls.append('<span class="this-page">%d</span>' % page)
        else:
          page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n))
    else:
        # Insert "smart" pagination links, so that there are always ON_ENDS
        # links at either end of the list of pages, and there are always
        # ON_EACH_SIDE links at either end of the "current page" link.
        if page <= (1 + ON_ENDS + ON_EACH_SIDE):
            # 1 2 *3* 4 5 6 ... 99 100
            for n in range(1, page + max(ON_EACH_SIDE, ON_ENDS) + 1):
              if n == page:
                page_htmls.append('<span class="this-page">%d</span>' % page)
              else:
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n))
            page_htmls.append('...')
            for n in range(paginator.pages - ON_EACH_SIDE + 1, paginator.pages):
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n))
        elif page > (paginator.pages - ON_EACH_SIDE - ON_ENDS - 2):
            # 1 2 ... 95 96 97 *98* 99 100
            for n in range(1, ON_ENDS + 1):
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n))
            page_htmls.append('...')
            for n in range(page - max(ON_EACH_SIDE, ON_ENDS), paginator.pages):
              if n == page:
                page_htmls.append('<span class="this-page">%d</span>' % page)
              else:
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n))
        else:
            # 1 2 ... 45 46 47 *48* 49 50 51 ... 99 100
            for n in range(1, ON_ENDS + 1):
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n))
            page_htmls.append('...')
            for n in range(page - ON_EACH_SIDE, page + ON_EACH_SIDE + 1):
              if n == page:
                page_htmls.append('<span class="this-page">%s</span>' % page)
              elif n == '.':
                page_htmls.append('...')
              else:
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n))
            page_htmls.append('...')
            for n in range(paginator.pages - ON_ENDS, paginator.pages):
                parameters.__setitem__('page', n)
                page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n))
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


def bufferquery(buffer, bucket, startdate, enddate):
      if buffer is None:
        filterstring1 = ''
        filterstring2 = ''
      else:
        filterstring1 = "where name ='%s'" % buffer
        filterstring2 = "and thebuffer_id ='%s'" % buffer
      cursor = connection.cursor()
      cursor.execute('''
        select combi.thebuffer_id, combi.onhand, combi.%s, coalesce(data.produced,0), coalesce(data.consumed,0)
          from
           (select name as thebuffer_id, onhand, d.%s, d.start from input_buffer
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
            %s
           ) as combi
          left join
           (select thebuffer_id, %s,
              sum(case when quantity>0 then quantity else 0 end) as produced,
              -sum(case when quantity<0 then quantity else 0 end) as consumed
              from output_flowplan, input_dates
              where output_flowplan.date = input_dates.day
              and output_flowplan.date >= '%s'
              and output_flowplan.date < '%s'
              %s
              group by thebuffer_id, %s
            ) data
          on combi.thebuffer_id = data.thebuffer_id
          and combi.%s = data.%s
          order by combi.thebuffer_id, combi.start '''
          % (bucket,bucket,bucket,startdate,enddate,bucket,filterstring1,bucket,startdate,enddate,filterstring2,bucket,bucket,bucket))
      resultset = []
      prevbuf = None
      rowset = []
      for row in cursor.fetchall():
        if row[0] != prevbuf:
          if prevbuf: resultset.append(rowset)
          rowset = []
          prevbuf = row[0]
          endoh = row[1]
        startoh = endoh
        endoh += row[3] - row[4]
        rowset.append( {
          'buffer': row[0],
          'bucket': row[2],
          'startoh': startoh,
          'produced': row[3],
          'consumed': row[4],
          'endoh': endoh,
          } )
      if prevbuf: resultset.append(rowset)
      return resultset

@staff_member_required
def bufferreport(request, buffer=None):
   if buffer:
     extra = {'title': 'Inventory report for %s' % buffer, 'reset_crumbs': False}
   else:
     extra = {'title': 'Inventory report', 'reset_crumbs': True}
   return BucketedView(request, buffer, bufferquery, 'buffer.html', 'buffer.csv', extra)


def demandquery(item, bucket, startdate, enddate):
      if item is None:
        filterstring1 = ''
        filterstring2 = ''
      else:
        filterstring1 = "where item_id ='%s'" % item
        filterstring2 = "and inp.item_id ='%s'" % item
      cursor = connection.cursor()
      cursor.execute('''
          select combi.item_id, combi.%s, coalesce(data.demand,0), coalesce(data.planned,0)
          from
           (select distinct item_id, d.%s, d.start from input_demand
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
            %s
           ) as combi
          left join
           (select inp.item_id, d.%s, sum(inp.quantity) as demand,
                  coalesce((select sum(output_operationplan.quantity)
                   from output_operationplan, input_dates, input_demand
                   where output_operationplan.enddate = input_dates.day
                   and input_dates.%s = d.%s
                   and output_operationplan.demand_id is not null
                   and output_operationplan.demand_id = input_demand.name
                   and input_demand.item_id = inp.item_id), 0) as planned
                from input_dates as d, input_demand as inp
                where inp.due = d.day
                and inp.due >= '%s'
                and inp.due < '%s'
                %s
                group by inp.item_id, d.%s) data
          on combi.item_id = data.item_id
          and combi.%s = data.%s
          order by combi.item_id, combi.start
         ''' % (bucket,bucket,bucket,startdate,enddate,bucket,filterstring1,bucket,bucket,bucket,startdate,enddate,filterstring2,bucket,bucket,bucket))
      resultset = []
      previtem = None
      rowset = []
      for row in cursor.fetchall():
        if row[0] != previtem:
          if previtem: resultset.append(rowset)
          rowset = []
          previtem = row[0]
          backlog = 0
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
     extra = {'title': 'Demand report for %s' % item, 'reset_crumbs': False}
   else:
     extra = {'title': 'Demand report', 'reset_crumbs': True}
   return BucketedView(request, item, demandquery, 'demand.html', 'demand.csv', extra)


def resourcequery(resource, bucket, startdate, enddate):
  if resource is None:
    filterstring1 = ''
    filterstring2 = ''
  else:
    filterstring1 = "where dd.resource_id ='%s'" % resource
    filterstring2 = "and input_load.resource_id ='%s'" % resource
  cursor = connection.cursor()
  cursor.execute('''
     select ddd.resource_id, ddd.bucket, min(ddd.available),
       coalesce(sum(loaddata.usage
                    * extract(epoch from (case loaddata.enddatetime>ddd.enddate when true then ddd.enddate else loaddata.enddatetime end)
                                       - (case loaddata.startdatetime>ddd.startdate when true then loaddata.startdatetime else ddd.startdate end))
                      ) / 86400 ,0) as load
     from (
       select dd.resource_id, dd.bucket, dd.startdate, dd.enddate,
         coalesce(sum(input_bucket.value
                      * extract(epoch from (case input_bucket.enddate>dd.enddate when true then dd.enddate else input_bucket.enddate end)
                                         - (case input_bucket.startdate>dd.startdate when true then input_bucket.startdate else dd.startdate end))
                 ) / 86400,0) as available
       from (
         select name as resource_id, maximum_id, d.bucket, d.startdate, d.enddate
         from input_resource
         inner join (
           -- todo the next line doesnt work for daily buckets
           select %s as bucket, %s_start as startdate, %s_end as enddate
           from input_dates
           where day >= '%s' and day < '%s'
           group by %s, startdate, enddate
           ) d on 1=1
         ) dd
       left join input_bucket
       on input_bucket.calendar_id = dd.maximum_id
          and dd.startdate <= input_bucket.enddate
          and dd.enddate >= input_bucket.startdate
       %s
		   group by dd.resource_id, dd.bucket, dd.startdate, dd.enddate
	     ) ddd
     left join (
       select input_load.resource_id, startdatetime, enddatetime, input_load.usagefactor as usage
       from output_operationplan, input_load
       where output_operationplan.operation_id = input_load.operation_id
          and output_operationplan.enddate >= '%s'
          and output_operationplan.startdate < '%s'
          %s
       ) loaddata
     on loaddata.resource_id = ddd.resource_id
       and ddd.startdate <= loaddata.enddatetime
       and ddd.enddate >= loaddata.startdatetime
     group by ddd.resource_id, ddd.bucket, ddd.startdate, ddd.enddate
     order by ddd.resource_id, ddd.startdate
     ''' % (bucket,bucket,bucket,startdate,enddate,bucket,filterstring1,startdate,enddate,filterstring2))
  resultset = []
  prevres = None
  rowset = []
  for row in cursor.fetchall():
    if row[0] != prevres:
      if prevres: resultset.append(rowset)
      rowset = []
      prevres = row[0]
    if row[2] != 0: util = row[3] / float(row[2])
    else: util = 0
    rowset.append( {
      'resource': row[0],
      'bucket': row[1],
      'load': row[3],
      'available': row[2],
      'utilization': util,
      } )
  if prevres: resultset.append(rowset)
  return resultset


@staff_member_required
def resourcereport(request, resource=None):
   if resource:
     extra = {'title': 'Resource report for %s' % resource, 'reset_crumbs': False}
   else:
     extra = {'title': 'Resource report', 'reset_crumbs': True}
   return BucketedView(request, resource, resourcequery, 'resource.html', 'resource.csv', extra)


def operationquery(operation, bucket, startdate, enddate):
      if operation is None:
        filterstring1 = ''
        filterstring2 = ''
      else:
        filterstring1 = "where name ='%s'" % operation
        filterstring2 = "and operation_id ='%s'" % operation
      cursor = connection.cursor()
      cursor.execute('''
        select combi.operation_id, combi.%s, coalesce(data.quantity,0)
          from
           (select name as operation_id, d.%s, d.start from input_operation
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
            %s
           ) as combi
          left join
           (select operation_id, %s,
              sum(quantity) as quantity
              from output_operationplan, input_dates
              where output_operationplan.startdate = input_dates.day
              and startdate >= '%s'
              and enddate < '%s'
              %s
              group by operation_id, %s
            ) data
          on combi.operation_id = data.operation_id
          and combi.%s = data.%s
          order by combi.operation_id, combi.start '''
          % (bucket,bucket,bucket,startdate,enddate,bucket,filterstring1,bucket,startdate,enddate,filterstring2,bucket,bucket,bucket))
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
          'quantity': row[2],
          } )
      if prevoper: resultset.append(rowset)
      return resultset

@staff_member_required
def operationreport(request, operation=None):
   if operation:
     extra = {'title': 'Operation report for %s' % operation, 'reset_crumbs': False}
   else:
     extra = {'title': 'Operation report', 'reset_crumbs': True}
   return BucketedView(request, operation, operationquery, 'operation.html', 'operation.csv', extra)


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
