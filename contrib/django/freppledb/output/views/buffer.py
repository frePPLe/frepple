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

from django.db import connection
from django.utils.translation import ugettext_lazy as _

from input.models import Buffer, Plan
from output.models import FlowPlan
from utils.db import *
from utils.report import *


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

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified

  @staticmethod
  def resultlist1(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    return basequery.values('name','item','location')

  @staticmethod
  def resultlist2(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    # Execute a query  to get the onhand value at the start of our horizon
    startohdict = {}
    cursor = connection.cursor()
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
    where=['out_operationplan.identifier = out_flowplan.operationplan'],
    tables=['out_operationplan'])
  model = FlowPlan
  frozenColumns = 0
  editable = False
  rows = (
    ('thebuffer', {
      'filter': FilterText(),
      'title': _('buffer')
      }),
    # @todo Eagerly awaiting the Django queryset refactoring to be able to filter on the operation field.
    # ('operation', {'filter': 'operation__icontains', 'title': _('operation')}),
    ('operation', {
      'title': _('operation'),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('flowdatetime', {
      'title': _('date'),
      'filter': FilterDate(field='flowdate'),
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

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified
