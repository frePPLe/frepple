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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.db import connection
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.contrib.admin.views.decorators import staff_member_required

from input.models import Buffer
from output.models import FlowPlan
from common.db import *
from common.report import *


class OverviewReport(TableReport):
  '''
  A report showing the inventory profile of buffers.
  '''
  template = 'output/buffer.html'
  title = _('Inventory Report')
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
  def resultlist1(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    return basequery.values('name','item','location')

  @staticmethod
  def resultlist2(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    cursor = connection.cursor()

    # Execute a query  to get the onhand value at the start of our horizon
    startohdict = {}
    query = '''
      select out_flowplan.thebuffer, out_flowplan.onhand
      from out_flowplan,
        (select thebuffer, max(id) as id
         from out_flowplan
         where thebuffer in (select buf.name from (%s) buf)
         and flowdate < '%s'
         group by thebuffer
        ) maxid
      where maxid.thebuffer = out_flowplan.thebuffer
      and maxid.id = out_flowplan.id
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
             select %s as bucket, %s_start as startdate, %s_end as enddate
             from dates
             where day_start >= '%s' and day_start < '%s'
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
  basequeryset = FlowPlan.objects.extra(
    select={'operation':'out_operationplan.operation'},
    where=['out_operationplan.id = out_flowplan.operationplan'],
    tables=['out_operationplan'])
  model = FlowPlan
  frozenColumns = 0
  editable = False
  rows = (
    ('thebuffer', {
      'filter': FilterText(),
      'title': _('buffer')
      }),
    # @todo filter on the operation field...
    # ('operation', {'filter': 'operation__icontains', 'title': _('operation')}),
    ('operation', {
      'title': _('operation'),
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
      'filter': FilterNumber(),
      'title': _('operationplan'),
      }),
    )


@staff_member_required
def GraphData(request, entity):
  basequery = Buffer.objects.filter(pk__exact=entity)
  (bucket,start,end,bucketlist) = getBuckets(request)
  consumed = []
  produced = []
  endoh = []
  for x in OverviewReport.resultlist2(basequery, bucket, start, end):
    consumed.append(x['consumed'])
    produced.append(x['produced'])
    endoh.append(x['endoh'])
  context = { 
    'buckets': bucketlist, 
    'consumed': consumed, 
    'produced': produced, 
    'endoh': endoh, 
    'axis_nth': len(bucketlist) / 20 + 1,
    }
  return HttpResponse(
    loader.render_to_string("output/buffer.xml", context, context_instance=RequestContext(request)),
    )
    