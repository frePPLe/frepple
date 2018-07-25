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

from datetime import datetime, timedelta

from django.db import connections
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from freppledb.input.models import Demand
from freppledb.common.report import GridReport, GridFieldText, GridFieldNumber
from freppledb.common.models import Parameter


class ReportByDemand(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/pegging.html'
  title = _("Demand plan")
  filterable = False
  frozenColumns = 0
  editable = False
  default_sort = None
  hasTimeBuckets = True
  multiselect = False
  heightmargin = 87
  help_url = 'user-guide/user-interface/plan-analysis/demand-gantt-report.html'
  rows = (
    GridFieldText('depth', title=_('depth'), editable=False, sortable=False),
    GridFieldText('operation', title=_('operation'), editable=False, sortable=False, key=True, formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('type', title=_('type'), editable=False, sortable=False, width=100),
    #GridFieldText('buffer', title=_('buffer'), formatter='buffer', editable=False, sortable=False),
    #GridFieldText('item', title=_('item'), formatter='item', editable=False, sortable=False),
    GridFieldText('resource', title=_('resource'), editable=False, sortable=False, extra='formatter:reslistfmt'),
    GridFieldNumber('quantity', title=_('quantity'), editable=False, sortable=False),
    GridFieldText('operationplans', width=1000, extra='formatter:ganttcell', editable=False, sortable=False),
    GridFieldText('parent', editable=False, sortable=False, hidden=True),
    GridFieldText('leaf', editable=False, sortable=False, hidden=True),
    GridFieldText('expanded', editable=False, sortable=False, hidden=True),
    GridFieldText('current', editable=False, sortable=False, hidden=True),
    GridFieldText('due', editable=False, sortable=False, hidden=True),
    GridFieldText('showdrilldown', editable=False, sortable=False, hidden=True),
    )


  @ classmethod
  def basequeryset(reportclass, request, *args, **kwargs):
    return Demand.objects.filter(name__exact=args[0]).values('name')


  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      return {
        'active_tab': 'plan',
        'title': force_text(Demand._meta.verbose_name) + " " + args[0],
        'post_title': _('plan')
        }
    else:
      return {}


  @classmethod
  def getBuckets(reportclass, request, *args, **kwargs):
    # Get the earliest and latest operationplan, and the demand due date
    cursor = connections[request.database].cursor()
    cursor.execute('''
      with dmd as (
        select
          due,
          cast(jsonb_array_elements(plan->'pegging')->>'opplan' as integer) opplan
        from demand
        where name = %s
        )
      select min(dmd.due), min(startdate), max(enddate)
      from dmd
      inner join operationplan
      on dmd.opplan = operationplan.id
      and type <> 'STCK'
      ''', (args[0]))
    x = cursor.fetchone()
    (due, start, end) = x
    if not due:
      # This demand is unplanned
      request.report_startdate = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
      request.report_enddate = request.report_startdate + timedelta(days=1)
      request.report_bucket = None
      request.report_bucketlist = []
      return
    if not start:
      start = due
    if not end:
      end = due

    # Adjust the horizon
    if due > end:
      end = due
    if due < start:
      start = due
    end += timedelta(days=1)
    start -= timedelta(days=1)
    request.report_startdate = start.replace(hour=0, minute=0, second=0, microsecond=0)
    request.report_enddate = end.replace(hour=0, minute=0, second=0, microsecond=0)
    request.report_bucket = None
    request.report_bucketlist = []


  @classmethod
  def query(reportclass, request, basequery):
    # Execute the query
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)
    cursor = connections[request.database].cursor()

    # Get current date and horizon
    horizon = (request.report_enddate - request.report_startdate).total_seconds() / 10000
    try:
      current = datetime.strptime(
        Parameter.objects.using(request.database).get(name="currentdate").value,
        "%Y-%m-%d %H:%M:%S"
        )
    except:
      current = datetime.now()
      current = current.replace(microsecond=0)

    # Collect demand due date, all operationplans and loaded resources
    query = '''
      with pegging as (
        select
          min(rownum) as rownum, min(due) as due, opplan, min(lvl) as lvl, sum(quantity) as quantity
        from (select
          row_number() over () as rownum, opplan, due, lvl, quantity
        from (select
          due,
          cast(jsonb_array_elements(plan->'pegging')->>'opplan' as integer) as opplan,
          cast(jsonb_array_elements(plan->'pegging')->>'level' as integer) as lvl,
          cast(jsonb_array_elements(plan->'pegging')->>'quantity' as numeric) as quantity
          from demand
          where name = %s
          ) d1
          )d2
        group by opplan
        )
      select
        pegging.due, operationplan.name, pegging.lvl, ops.pegged,
        pegging.rownum, operationplan.startdate, operationplan.enddate, operationplan.quantity,
        operationplan.status, operationplanresource.resource_id, operationplan.type,
        case when operationplan.operation_id is not null then 1 else 0 end as show
      from pegging
      inner join operationplan
        on operationplan.id = pegging.opplan
      inner join (
        select name,
          min(rownum) as rownum,
          sum(pegging.quantity) as pegged
        from pegging
        inner join operationplan
          on pegging.opplan = operationplan.id
        group by operationplan.name
        ) ops
      on operationplan.name = ops.name
      left outer join operationplanresource
        on pegging.opplan = operationplanresource.operationplan_id
      order by ops.rownum, pegging.rownum
      '''
    cursor.execute(query, baseparams)

    # Build the Python result
    prevrec = None
    parents = {}
    for rec in cursor.fetchall():
      if not prevrec or rec[1] != prevrec['operation']:
        # Return prev operation
        if prevrec:
          if prevrec['depth'] < rec[2]:
            prevrec['leaf'] = 'false'
          yield prevrec
        # New operation
        prevrec = {
          'current': str(current),
          'operation': rec[1],
          'type': rec[10],
          'showdrilldown': rec[11],
          'depth': rec[2],
          'quantity': str(rec[3]),
          'due': round((rec[0] - request.report_startdate).total_seconds() / horizon, 3),
          'current': round((current - request.report_startdate).total_seconds() / horizon, 3),
          'parent': parents.get(rec[2] - 1, None) if rec[2] and rec[2] >= 1 else None,
          'leaf': 'true',
          'expanded': 'true',
          'resource': rec[9] and [rec[9], ] or [],
          'operationplans': [{
             'operation': rec[1],
             'quantity': str(rec[7]),
             'x': round((rec[5] - request.report_startdate).total_seconds() / horizon, 3),
             'w': round((rec[6] - rec[5]).total_seconds() / horizon, 3),
             'startdate': str(rec[5]),
             'enddate': str(rec[6]),
             'status': rec[8],
             'id': rec[4]
             }]
          }
        parents[rec[2]] = rec[1]
      elif rec[4] != prevrec['operationplans'][-1]['id']:
        # Extra operationplan for the operation
        prevrec['operationplans'].append({
          'operation': rec[1],
          'quantity': str(rec[7]),
          'x': round((rec[5] - request.report_startdate).total_seconds() / horizon, 3),
          'w': round((rec[6] - rec[5]).total_seconds() / horizon, 3),
          'startdate': str(rec[5]),
          'enddate': str(rec[6]),
          'locked': rec[8],
          'id': rec[4]
          })
      elif rec[9] and not rec[9] in prevrec['resource']:
        # Extra resource loaded by the operationplan
        prevrec['resource'].append(rec[9])
    if prevrec:
      yield prevrec
