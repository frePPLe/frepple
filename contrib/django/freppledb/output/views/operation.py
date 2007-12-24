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

from input.models import Operation, Plan
from output.models import OperationPlan
from utils.db import *
from utils.report import *


class OverviewReport(TableReport):
  '''
  A report showing the planned starts of each operation.
  '''
  template = 'output/operation.html'
  title = _('Operation Report')
  basequeryset = Operation.objects.all()
  rows = (
    ('operation',{
      'filter': FilterText(field='name'),
      'order_by': 'name',
      'title': _('operation'),
      }),
    )
  crosses = (
    ('locked_start', {'title': _('locked starts'),}),
    ('total_start', {'title': _('total starts'),}),
    ('locked_end', {'title': _('locked ends'),}),
    ('total_end', {'title': _('total ends'),}),
    )
  columns = (
    ('bucket',{'title': _('bucket')}),
    )

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified

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
               where day_start >= '%s' and day_start < '%s'
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
    for row in cursor.fetchall():
      yield {
        'operation': row[0],
        'bucket': row[1],
        'startdate': python_date(row[2]),
        'enddate': python_date(row[3]),
        'locked_start': row[4],
        'total_start': row[5],
        'locked_end': row[6],
        'total_end': row[7],
        }


class DetailReport(ListReport):
  '''
  A list report to show operationplans.
  '''
  template = 'output/operationplan.html'
  title = _("Operationplan Detail Report")
  reset_crumbs = False
  basequeryset = OperationPlan.objects.extra(
    select={'fcst_or_actual':'demand in (select distinct name from forecast)'}
    )
  rows = (
    ('identifier', {
      'filter': FilterNumber(),
      'title': _('operationplan'),
      }),
    ('demand', {
      'filter': FilterText(size=15),
      'title': _('demand'),
      }),
    ('operation', {
      'filter': FilterText(size=15),
      'title': _('operation')}),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('startdate', {
      'title': _('startdate'),
      'filter': FilterDate(),
      }),
    ('enddate', {
      'title': _('enddate'),
      'filter': FilterDate(),
      }),
    ('locked', {
      'title': _('locked'),
      'filter': FilterBool(),
      }),
    ('owner', {'title': _('owner')}),
    )

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified
