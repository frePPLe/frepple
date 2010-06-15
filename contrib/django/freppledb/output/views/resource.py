#
# Copyright (C) 2007-2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$


from django.db import connections
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required

from freppledb.input.models import Resource
from freppledb.output.models import LoadPlan
from freppledb.common.db import *
from freppledb.common.report import *

  
class OverviewReport(TableReport):
  '''
  A report showing the loading of each resource.
  '''
  template = 'output/resource.html'
  title = _('Resource report')
  basequeryset = Resource.objects.all()
  model = Resource
  rows = (
    ('resource',{
      'filter': FilterText(field='name'),
      'order_by': 'name',
      'title': _('resource'),
      }),
    ('location',{
      'filter': FilterText(field='location__name'),
      'title': _('location'),
      }),
    )
  crosses = (
    ('available',{'title': _('available'), 'editable': lambda req: req.user.has_perm('input.change_resource'),}),
    ('unavailable',{'title': _('unavailable')}),
    ('setup',{'title': _('setup')}),
    ('load',{'title': _('load')}),
    ('utilization',{'title': _('utilization %'),}),
    )
  columns = (
    ('bucket',{'title': _('bucket')}),
    )

  javascript_imports = ['/static/FusionCharts.js',]

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values('name','location')

  @staticmethod
  def resultlist2(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)        
        
    # Execute the query
    cursor = connections[request.database].cursor()
    query = '''
       select x.name as row1, x.location_id as row2,
             x.bucket as col1, x.startdate as col2, x.enddate as col3,
             min(x.real_available), 
             min(x.total_available) - min(x.real_available) as unavailable,
             coalesce(sum(loaddata.quantity * %s), 0) as loading,
             0 as setup
       from (
         select res.name as name, res.location_id as location_id,
               d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
               coalesce(sum(bucket.value * %s),0) as total_available,
               coalesce(sum(bucket.value * %s * coalesce(bucket2.value,1)),0) as real_available
         from (%s) res
         -- Multiply with buckets
         cross join (
              select %s as bucket, %s_start as startdate, %s_end as enddate
              from dates
              where day_start >= '%s' and day_start < '%s'
              group by %s, %s_start, %s_end
              ) d
         -- Available capacity
         left join bucket
         on res.maximum_id = bucket.calendar_id
         and d.startdate <= bucket.enddate
         and d.enddate >= bucket.startdate
         -- Unavailable capacity
         left join location on res.location_id = location.name
         left join calendar on location.available_id = calendar.name
         left join bucket bucket2 on calendar.name = bucket2.calendar_id
         and d.startdate <= bucket2.enddate
         and d.enddate >= bucket2.startdate
         -- Grouping
         group by res.name, res.location_id, d.bucket, d.startdate, d.enddate
       ) x
       -- Load data
       left join (
         select theresource as resource_id, 
           out_loadplan.startdate as start1, out_loadplan.enddate as end1, 
           bucket.startdate as start2, bucket.enddate as end2,
           out_loadplan.quantity as quantity
         from out_loadplan
         inner join (%s) res2
         on out_loadplan.theresource = res2.name
         and out_loadplan.startdate > '%s' and out_loadplan.enddate < '%s'
         -- Unavailable capacity
         inner join out_operationplan on out_loadplan.operationplan = out_operationplan.id
         inner join operation on out_operationplan.operation = operation.name
         left join location on operation.location_id = location.name
         left join calendar on location.available_id = calendar.name
         left join bucket bucket on calendar.name = bucket.calendar_id
         and out_loadplan.startdate <= bucket.enddate
         and out_loadplan.enddate >= bucket.startdate
         and bucket.value > 0
         ) loaddata
       on x.name = loaddata.resource_id
       and x.startdate <= loaddata.end1
       and x.enddate >= loaddata.start1
       -- Grouping and ordering
       group by x.name, x.location_id, x.bucket, x.startdate, x.enddate
       order by %s, x.startdate
       ''' % ( sql_overlap3('loaddata.start1','loaddata.end1','x.startdate','x.enddate','loaddata.start2','loaddata.end2'),
         sql_overlap3('bucket.startdate','bucket.enddate','d.startdate','d.enddate','bucket2.startdate','bucket2.enddate'),
         sql_overlap3('bucket.startdate','bucket.enddate','d.startdate','d.enddate','bucket2.startdate','bucket2.enddate'),
         basesql,connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
         connection.ops.quote_name(bucket),bucket,bucket,basesql,
         startdate,enddate,sortsql)
    cursor.execute(query, baseparams + baseparams)
    
    # Build the python result
    for row in cursor.fetchall():
      if row[5] != 0: util = row[7] * 100 / row[5]
      else: util = 0
      yield {
        'resource': row[0],
        'location': row[1],
        'bucket': row[2],
        'startdate': python_date(row[3]),
        'enddate': python_date(row[4]),
        'available': row[5],
        'unavailable': row[6],
        'load': row[7],
        'setup': row[8],
        'utilization': util,
        }


class DetailReport(ListReport):
  '''
  A list report to show loadplans.
  '''
  template = 'output/loadplan.html'
  title = _("Resource detail report")
  reset_crumbs = False
  basequeryset = LoadPlan.objects.extra(
    select={'operation':'out_operationplan.operation'},
    where=['out_operationplan.id = out_loadplan.operationplan'],
    tables=['out_operationplan'])
  model = LoadPlan
  frozenColumns = 0
  editable = False
  rows = (
    ('theresource', {
      'filter': FilterText(),
      'title': _('resource')
      }),
    # @todo filter on the operation field...
    ('operation', {
      'title': _('operation'),
      }),
    ('startdate', {
      'title': _('startdate'),
      'filter': FilterDate(),
      }),
    ('enddate', {
      'title': _('enddate'),
      'filter': FilterDate(),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('setup', {
      'title': _('setup'),
      'filter': FilterText(),
      }),
    ('operationplan', {
      'filter': FilterNumber(operator='exact',),
      'title': _('operationplan')
      }),
    )


@staff_member_required
def GraphData(request, entity):
  basequery = Resource.objects.filter(pk__exact=entity)
  (bucket,start,end,bucketlist) = getBuckets(request)
  load = []
  free = []
  overload = []
  unavailable = []
  setup = []
  for x in OverviewReport.resultlist2(request, basequery, bucket, start, end):
    if x['available'] > x['load']:
      free.append(x['available'] - x['load'])
      overload.append(0)
      load.append(x['load'])
    else:
      load.append(x['available'])
      free.append(0)
      overload.append(x['load'] - x['available'])
    unavailable.append(x['unavailable'])
    setup.append(x['setup'])
  context = { 
    'buckets': bucketlist, 
    'load': load, 
    'setup': setup, 
    'free': free, 
    'overload': overload, 
    'unavailable': unavailable, 
    'axis_nth': len(bucketlist) / 20 + 1,
    }
  return HttpResponse(
    loader.render_to_string("output/resource.xml", context, context_instance=RequestContext(request)),
    )
