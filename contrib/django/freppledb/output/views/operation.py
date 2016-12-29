#
# Copyright (C) 2007-2013 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.db import connections
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.encoding import force_text

from freppledb.input.models import Operation
from freppledb.common.report import GridReport, GridPivot, GridFieldText, GridFieldNumber, GridFieldDateTime, GridFieldBool, GridFieldInteger


class OverviewReport(GridPivot):
  '''
  A report showing the planned starts of each operation.
  '''
  template = 'output/operation.html'
  title = _('Operation report')
  basequeryset = Operation.objects.all()
  model = Operation
  permissions = (("view_operation_report", "Can view operation report"),)
  help_url = 'user-guide/user-interface/plan-analysis/operation-report.html'
  rows = (
    GridFieldText('operation', title=_('operation'), key=True, editable=False, field_name='name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('location', title=_('location'), editable=False, field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    )
  crosses = (
    ('proposed_start', {'title': _('proposed starts')}),
    ('total_start', {'title': _('total starts')}),
    ('proposed_end', {'title': _('proposed ends')}),
    ('total_end', {'title': _('total ends')}),
    )

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plan'
      return {
        'title': capfirst(force_text(Operation._meta.verbose_name) + " " + args[0]),
        'post_title': ': ' + capfirst(force_text(_('plan'))),
        }
    else:
      return {}

  @staticmethod
  def query(request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)
    # Run the query
    cursor = connections[request.database].cursor()
    query = '''
        select x.row1, x.row2, x.col1, x.col2, x.col3,
          min(x.proposed_start), min(x.total_start),
          coalesce(sum(case when o2.status in ('proposed') then o2.quantity else 0 end),0),
          coalesce(sum(o2.quantity),0)
        from (
          select oper.name as row1,  oper.location_id as row2,
               d.bucket as col1, d.startdate as col2, d.enddate as col3,
               coalesce(sum(case when o1.status in ('proposed') then o1.quantity else 0 end),0) as proposed_start,
               coalesce(sum(o1.quantity),0) as total_start
          from (%s) oper
          -- Multiply with buckets
          cross join (
             select name as bucket, startdate, enddate
             from common_bucketdetail
             where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
             ) d
          -- Planned and frozen quantity, based on start date
          left join operationplan o1
          on oper.name = o1.operation_id
          and d.startdate <= o1.startdate
          and d.enddate > o1.startdate
          and o1.type = 'MO'
          and o1.status in ('approved','confirmed','proposed')
          -- Grouping
          group by oper.name, oper.location_id, d.bucket, d.startdate, d.enddate
        ) x
        -- Planned and frozen quantity, based on end date
        left join operationplan o2
        on x.row1 = o2.operation_id
        and x.col2 <= o2.enddate
        and x.col3 > o2.enddate
        and o2.type = 'MO'
        and o2.status in ('approved','confirmed','proposed')
        -- Grouping and ordering
        group by x.row1, x.row2, x.col1, x.col2, x.col3
        order by %s, x.col2
      ''' % (basesql, request.report_bucket,
             request.report_startdate, request.report_enddate, sortsql)
    cursor.execute(query, baseparams)

    # Convert the SQl results to python
    for row in cursor.fetchall():
      yield {
        'operation': row[0],
        'location': row[1],
        'bucket': row[2],
        'startdate': row[3].date(),
        'enddate': row[4].date(),
        'proposed_start': row[5],
        'total_start': row[6],
        'proposed_end': row[7],
        'total_end': row[8],
        }
