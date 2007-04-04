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
from django.template import RequestContext
from django.db import connection
from django.core.cache import cache
from django.http import Http404

from freppledb.input.models import Buffer, Flow, Operation
   
def getBuckets(name):
  ''' 
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table input_dates, and are
  stored in the django memory cache for performance reasons
  '''
  global bucketization
  # Check if the argument is valid
  if name not in ('day','week','month','quarter','year'): 
    raise Http404, "bucket name %s not valid" % name
    
  # Pick up the buckets from the cache, and return if found
  dates = cache.get(name)
  if dates: return dates
  
  # Read the buckets from the database if the data aren't in the cach yet
  cursor = connection.cursor()
  cursor.execute('''
    select %s, min(day), max(day)
    from input_dates
    group by %s
    order by min(day)''' % (name,name))
  dates = [ {'name': i, 'start': j, 'end': k} for i,j,k in cursor.fetchall() ]
  cache.set(name, dates, 24 * 7 * 3600)  # Cache for 7 days
  return dates   


class bufferreport:
  def __init__(self, bucket='month'):
    cursor = connection.cursor()
    cursor.execute('''
      select combi.thebuffer_id, combi.onhand, combi.%s, coalesce(data.produced,0), coalesce(data.consumed,0)
        from 
         (select distinct name as thebuffer_id, onhand, d.%s, d.start from input_buffer
          inner join (select %s, min(day) as start from input_dates group by %s) d on 1=1
         ) as combi
        left join
         (select thebuffer_id, %s,
            sum(case when quantity>0 then quantity else 0 end) as produced,
            sum(case when quantity<0 then quantity else 0 end) as consumed
            from output_flowplan, input_dates
            where output_flowplan.date = input_dates.day
            group by thebuffer_id, %s
          ) data 
        on combi.thebuffer_id = data.thebuffer_id
        and combi.%s = data.%s
        order by combi.thebuffer_id, combi.start ''' % (bucket,bucket,bucket,bucket,bucket,bucket,bucket,bucket))
    self.resultset = cursor.fetchall()
    self.count = 0
    self.curbuf = ''
    self.len = len(self.resultset)

  def __iter__(self):
    return self
    
  def next(self):
    if self.count >= self.len: raise StopIteration()
    res = self.resultset[self.count]
    if res[0] != self.curbuf:
       self.onhand = res[1]
       self.curbuf = res[0]
    oh = self.onhand
    self.onhand += res[3] + res[4]
    self.count += 1
    return {
      'buffer': res[0],
      'bucket': res[2],
      'startoh': oh,
      'produced': res[3],
      'consumed': res[4], 
      'endoh': self.onhand,
      }
    
  #@login_required
  @staticmethod
  def view(request):
    b = request.GET.get('bucket', 'month')
    c = RequestContext(request, { 
       'bufferplan': bufferreport(b), 
       'bucket': b,
       'bucketlist': getBuckets(b),
       })      
    return render_to_response('buffer.html', c)
  
  
class demandreport:
  def __init__(self, bucket='month'):
    cursor = connection.cursor()
    cursor.execute('''
        select combi.item_id, combi.%s, coalesce(data.demand,0), coalesce(data.planned,0)
        from 
         (select distinct item_id, d.%s, d.start from input_demand
          inner join (select %s, min(day) as start from input_dates group by %s) d on 1=1
         ) as combi
        left join
         (select inp.item_id, d.%s, sum(inp.quantity) as demand, 
                coalesce((select sum(output_operationplan.quantity) 
                 from output_operationplan, input_dates, input_demand
                 where output_operationplan.enddate = input_dates.day
                 and input_dates.%s = d.%s
                 and output_operationplan.demand_id = input_demand.name
                 and input_demand.item_id = inp.item_id), 0) as planned
              from input_dates as d, input_demand as inp
              where inp.due = d.day
              group by inp.item_id, d.%s) data 
        on combi.item_id = data.item_id
        and combi.%s = data.%s
        order by combi.item_id, combi.start       
       ''' % (bucket,bucket,bucket,bucket,bucket,bucket,bucket,bucket,bucket,bucket))
    self.resultset = cursor.fetchall()
    self.count = 0
    self.curitem = ''
    self.len = len(self.resultset)

  def __iter__(self):
    return self
    
  def next(self):
    if self.count >= self.len: raise StopIteration()
    res = self.resultset[self.count]
    self.count += 1
    if res[0] != self.curitem:
       self.backlog = 0
       self.curitem = res[0]
    self.backlog += res[2] - res[3]
    return {
      'item': res[0],
      'bucket': res[1],
      'requested': res[2],
      'supplied': res[3], 
      'backlog': self.backlog,
      }
    
  #@login_required
  @staticmethod
  def view(request):
    b = request.GET.get('bucket', 'week')
    c = RequestContext(request,{ 
       'demandplan': demandreport(b), 
       'bucket': b,
       'bucketlist': getBuckets(b),
       })      
    return render_to_response('demand.html', c)  


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
                                                                                                                                                                                                   