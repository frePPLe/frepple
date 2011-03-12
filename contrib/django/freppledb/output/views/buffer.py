#
# Copyright (C) 2007-2010 by Johan De Taeye, frePPLe bvba
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
from django.http import HttpResponse
from django.template import RequestContext, loader

from freppledb.input.models import Buffer
from freppledb.output.models import FlowPlan
from freppledb.common.db import sql_max, sql_min, python_date
from freppledb.common.report import TableReport, ListReport, FilterText, FilterNumber, FilterDate, getBuckets


class OverviewReport(TableReport):
  '''
  A report showing the inventory profile of buffers.
  '''
  template = 'output/buffer.html'
  title = _('Inventory report')
  basequeryset = Buffer.objects.all()
  model = Buffer
  rows = (
    ('buffer', {
      'filter': FilterText(field='name'),
      'order_by': 'name',
      'title': _('buffer')
      }),
    ('item', {
      'filter': FilterText(field='item__name'),
      'title': _('item')
      }),
    ('location', {
      'filter': FilterText(field='location__name'),
      'title': _('location')
      }),
    )
  crosses = (
    ('startoh', {'title': _('start inventory'),}),
    ('produced', {'title': _('produced'),}),
    ('consumed', {'title': _('consumed'),}),
    ('endoh', {'title': _('end inventory'),}),
    )
  columns = (
    ('bucket', {'title': _('bucket')}),
    )

  javascript_imports = ['/static/FusionCharts.js',]
  
  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):    
    return basequery.values('name','item','location')

  @staticmethod
  def resultlist2(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)
        
    # Assure the item hierarchy is up to date
    Buffer.rebuildHierarchy(database=basequery.db)
    
    # Execute a query  to get the onhand value at the start of our horizon
    startohdict = {}
    query = '''
      select buffers.name, sum(oh.onhand)
      from (%s) buffers 
      inner join buffer
      on buffer.lft between buffers.lft and buffers.rght 
      inner join (
      select out_flowplan.thebuffer as thebuffer, out_flowplan.onhand as onhand
      from out_flowplan,
        (select thebuffer, max(id) as id
         from out_flowplan
         where flowdate < '%s'
         group by thebuffer
        ) maxid
      where maxid.thebuffer = out_flowplan.thebuffer
      and maxid.id = out_flowplan.id
      ) oh
      on oh.thebuffer = buffer.name
      group by buffers.name
      ''' % (basesql, startdate)
    cursor.execute(query, baseparams)
    for row in cursor.fetchall(): startohdict[row[0]] = float(row[1])

    # Execute the actual query
    query = '''
      select buf.name as row1, buf.item_id as row2, buf.location_id as row3,
             d.bucket as col1, d.startdate as col2, d.enddate as col3,
             coalesce(sum(%s),0.0) as consumed,
             coalesce(-sum(%s),0.0) as produced
        from (%s) buf
        -- Multiply with buckets
        cross join (
             select name as bucket, startdate, enddate
             from bucketdetail
             where bucket_id = '%s' and startdate >= '%s' and startdate < '%s'
             ) d
        -- Include child buffers
        inner join buffer
        on buffer.lft between buf.lft and buf.rght
        -- Consumed and produced quantities
        left join out_flowplan
        on buffer.name = out_flowplan.thebuffer
        and d.startdate <= out_flowplan.flowdate
        and d.enddate > out_flowplan.flowdate
        -- Grouping and sorting
        group by buf.name, buf.item_id, buf.location_id, buf.onhand, d.bucket, d.startdate, d.enddate
        order by %s, d.startdate
      ''' % (sql_max('out_flowplan.quantity','0.0'),sql_min('out_flowplan.quantity','0.0'),
        basesql,bucket,startdate,enddate,sortsql)
    cursor.execute(query, baseparams)

    # Build the python result
    prevbuf = None
    for row in cursor.fetchall():
      if row[0] != prevbuf:
        prevbuf = row[0]
        try: startoh = startohdict[prevbuf]
        except: startoh = 0
        endoh = startoh + float(row[6] - row[7])
      else:
        startoh = endoh
        endoh += float(row[6] - row[7])
      yield {
        'buffer': row[0],
        'item': row[1],
        'location': row[2],
        'bucket': row[3],
        'startdate': python_date(row[4]),
        'enddate': python_date(row[5]),
        'startoh': startoh,
        'produced': row[6],
        'consumed': row[7],
        'endoh': endoh,
        }


class DetailReport(ListReport):
  '''
  A list report to show flowplans.
  '''
  template = 'output/flowplan.html'
  title = _("Inventory detail report")
  reset_crumbs = False
  basequeryset = FlowPlan.objects.select_related() \
    .extra(select={'operation_in': "select name from operation where out_operationplan.operation = operation.name",})
  model = FlowPlan
  frozenColumns = 0
  editable = False
  
  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'thebuffer', 'operationplan__operation', 'quantity', 'flowdate', 
      'onhand', 'operationplan', 'operation_in'
      )
  
  rows = (
    ('thebuffer', {
      'filter': FilterText(),
      'title': _('buffer')
      }),
    ('operationplan__operation', {
      'title': _('operation'),
      'filter': FilterText(),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('flowdate', {
      'title': _('date'),
      'filter': FilterDate(),
      }),
    ('onhand', {
      'title': _('onhand'),
      'filter': FilterNumber(),
      }),
    ('operationplan', {
      'filter': FilterNumber(operator='exact', ),
      'title': _('operationplan'),
      }),
    )


@staff_member_required
def GraphData(request, entity):
  basequery = Buffer.objects.filter(pk__exact=entity)
  (bucket,start,end,bucketlist) = getBuckets(request)
  consumed = []
  produced = []
  startoh = []
  for x in OverviewReport.resultlist2(request, basequery, bucket, start, end):
    consumed.append(x['consumed'])
    produced.append(x['produced'])
    startoh.append(x['startoh'])
  context = { 
    'buckets': bucketlist, 
    'consumed': consumed, 
    'produced': produced, 
    'startoh': startoh, 
    'axis_nth': len(bucketlist) / 20 + 1,
    }
  return HttpResponse(
    loader.render_to_string("output/buffer.xml", context, context_instance=RequestContext(request)),
    )
    