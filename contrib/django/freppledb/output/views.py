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
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.db import connection
from django.core.cache import cache
from django.http import Http404, HttpResponse

from datetime import date

from freppledb.input.models import Buffer, Flow, Operation, Plan

PAGINATE_BY = 20
ON_EACH_SIDE = 3
ON_ENDS = 2


def getBuckets(request, bucket=None, start=None, end=None):
  '''
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table input_dates, and are
  stored in the django memory cache for performance reasons
  '''
  # Pick up the arguments
  if not bucket: bucket = request.GET.get('bucket', 'month')
  if not start:
    start = request.GET.get('start')
    if start:
      try:
        (y,m,d) = start.split('-')
        start = date(int(y),int(m),int(d))
      except:
        start = Plan.objects.all()[0].current.date()
    else:
      start = Plan.objects.all()[0].current.date()
  if not end:
    end = request.GET.get('end')
    if end:
      try:
        (y,m,d) = end.split('-')
        end = date(int(y),int(m),int(d))
      except:
        end = date(2030,1,1)
    else:
      end = date(2030,1,1)

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
      if i['start'] < end and i['end'] > start: res.append(i)
  elif end:
    res = []
    for i in dates:
      if i['start'] > end: res.append(i)
  elif start:
    res = []
    for i in dates:
      if i['end'] > start: res.append(i)
  else:
    return (bucket,start,end,dates)
  return (bucket,start,end,res)


def BucketedView(request, querymethod, htmltemplate, csvtemplate):
    global ON_EACH_SIDE
    global ON_ENDS
    global PAGINATE_BY
    (bucket,start,end,bucketlist) = getBuckets(request)

    # Look up the data in the cache
    parameters = request.GET.copy()
    parameters.__setitem__('page', 0)
    key = "%s?%s" % (request.path, parameters.urlencode())
    objectlist = cache.get(key)
    if not objectlist:
      # Data not found in the cache, recompute
      objectlist = querymethod(bucket,start,end)
      cache.set(key, objectlist, 10 * 60)   # cache for 10 minutes

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
    return render_to_response(htmltemplate,
       {
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
       },
       context_instance=RequestContext(request))


def bufferquery(bucket, startdate, enddate):
      cursor = connection.cursor()
      cursor.execute('''
        select combi.thebuffer_id, combi.onhand, combi.%s, coalesce(data.produced,0), coalesce(data.consumed,0)
          from
           (select name as thebuffer_id, onhand, d.%s, d.start from input_buffer
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
           ) as combi
          left join
           (select thebuffer_id, %s,
              sum(case when quantity>0 then quantity else 0 end) as produced,
              sum(case when quantity<0 then quantity else 0 end) as consumed
              from output_flowplan, input_dates
              where output_flowplan.date = input_dates.day
              and output_flowplan.date >= '%s'
              and output_flowplan.date < '%s'
              group by thebuffer_id, %s
            ) data
          on combi.thebuffer_id = data.thebuffer_id
          and combi.%s = data.%s
          order by combi.thebuffer_id, combi.start '''
          % (bucket,bucket,bucket,startdate,enddate,bucket,bucket,startdate,enddate,bucket,bucket,bucket))
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
        endoh += row[3] + row[4]
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

#@login_required
def bufferreport(request):
    return BucketedView(request, bufferquery, 'buffer.html', 'buffer.csv')


def demandquery(bucket, startdate, enddate):
      cursor = connection.cursor()
      cursor.execute('''
          select combi.item_id, combi.%s, coalesce(data.demand,0), coalesce(data.planned,0)
          from
           (select distinct item_id, d.%s, d.start from input_demand
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
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
                group by inp.item_id, d.%s) data
          on combi.item_id = data.item_id
          and combi.%s = data.%s
          order by combi.item_id, combi.start
         ''' % (bucket,bucket,bucket,startdate,enddate,bucket,bucket,bucket,bucket,startdate,enddate,bucket,bucket,bucket))
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


#@login_required
def demandreport(request):
    return BucketedView(request, demandquery, 'demand.html', 'demand.csv')


def resourcequery(bucket, startdate, enddate):
      cursor = connection.cursor()
      cursor.execute('''
        select combi.resource_id, combi.%s, coalesce(data.load,0), coalesce(data.available,0)
          from
           (select name as resource_id, d.%s, d.start from input_resource
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
           ) as combi
          left join
           (select resource_id, %s,
              sum(quantity * extract(epoch from (%s_end - output_loadplan.datetime)))/86400 as load,
              min(maximum * (%s_end - %s_start)) as available
              from output_loadplan, input_dates
              where output_loadplan.date = input_dates.day
              and output_loadplan.date >= '%s'
              and output_loadplan.date < '%s'           
              group by resource_id, %s
            ) data 
          on combi.resource_id = data.resource_id
          and combi.%s = data.%s
          order by combi.resource_id, combi.start ''' 
          % (bucket,bucket,bucket,startdate,enddate,bucket,bucket,bucket,bucket,bucket,startdate,enddate,bucket,bucket,bucket))
      resultset = []
      prevres = None
      rowset = []
      for row in cursor.fetchall():
        if row[0] != prevres:
          if prevres: resultset.append(rowset)
          rowset = []
          prevres = row[0]
        if row[3] != 0: util = row[2] / float(row[3])
        else: util = 0
        rowset.append( {
          'resource': row[0],
          'bucket': row[1],
          'load': row[2],
          'available': row[3],
          'utilization': util,
          } )
      if prevres: resultset.append(rowset)
      return resultset


#@login_required
def resourcereport(request):
    return BucketedView(request, resourcequery, 'resource.html', 'resource.csv')


def operationquery(bucket, startdate, enddate):
      cursor = connection.cursor()
      cursor.execute('''
        select combi.operation_id, combi.%s, coalesce(data.quantity,0)
          from
           (select name as operation_id, d.%s, d.start from input_operation
            inner join (select %s, min(day) as start from input_dates where day >= '%s'
              and day < '%s' group by %s) d on 1=1
           ) as combi
          left join
           (select operation_id, %s,
              sum(quantity) as quantity
              from output_operationplan, input_dates
              where output_operationplan.startdate = input_dates.day
              and startdate >= '%s'
              and enddate < '%s'
              group by operation_id, %s
            ) data
          on combi.operation_id = data.operation_id
          and combi.%s = data.%s
          order by combi.operation_id, combi.start '''
          % (bucket,bucket,bucket,startdate,enddate,bucket,bucket,startdate,enddate,bucket,bucket,bucket))
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

#@login_required
def operationreport(request):
   return BucketedView(request, operationquery, 'operation.html', 'operation.csv')


class pathreport:
  @staticmethod
  def getPath(buffer):
    # Find the buffer
    try: rootbuffer = Buffer.objects.get(name=buffer)
    except: raise Http404, "buffer %s doesn't exist" % buffer

    # Initialize
    resultset = []
    level = 0
    bufs = [ (rootbuffer, None, 1) ]

    # Recurse deeper in the supply chain
    while len(bufs) > 0:
       level += 1
       newbufs = []
       for i, fl, q in bufs:
          # Find new buffers
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
       bufs = newbufs

    # Return results
    return resultset

  #@login_required
  @staticmethod
  def view(request):
    b = request.GET.get('buffer', 'Buf 00000 L00')  # todo hardcoded default
    c = RequestContext(request,{
       'supplypath': pathreport.getPath(b),
       'buffer': b,
       })
    # Uncomment the next line to see the SQL statements executed for the report
    #for i in connection.queries: print i
    return render_to_response('path.html', c)
