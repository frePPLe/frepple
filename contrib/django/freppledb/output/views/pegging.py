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

from django.contrib.admin.utils import unquote
from django.db import connections
from django.http import Http404
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
  heightmargin = 82
  rows = (
    GridFieldText('depth', title=_('depth'), editable=False, sortable=False),
    GridFieldText('operation', title=_('operation'), editable=False, sortable=False, key=True, formatter='detail', extra="role:'input/operation'"),
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
    )


  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    return Demand.objects.filter(name__exact=unquote(args[0])).values('name')


  @classmethod
  def getBuckets(reportclass, request, *args, **kwargs):
    # Get the earliest and latest operationplan, and the demand due date
    cursor = connections[request.database].cursor()
    cursor.execute('''
      select demand.due, min(startdate), max(enddate)
      from demand
        left outer join out_demandpegging
          on out_demandpegging.demand = demand.name
        left outer join out_operationplan
          on out_demandpegging.operationplan = out_operationplan.id
      where demand.name = %s
        and out_operationplan.operation not like 'Inventory %%'
      group by due
      ''', (args[0]))
    x = cursor.fetchone()
    if not x:
      raise Http404("Demand not found")
    (due, start, end) = x
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
      select
        demand.due, ops.operation, ops.level, ops.pegged,
        op2.id, op2.startdate, op2.enddate, op2.quantity,
        op2.locked, out_loadplan.theresource
      from (
        select
          out_operationplan.operation as operation,
          min(out_demandpegging.level) as level,
          min(out_demandpegging.id) as id,
          sum(out_demandpegging.quantity) as pegged
        from out_demandpegging
        inner join out_operationplan
          on out_operationplan.id = out_demandpegging.operationplan
        where demand = %s
        group by out_operationplan.operation
        ) ops
      inner join out_demandpegging peg2
        on peg2.demand = %s
      inner join out_operationplan op2
        on op2.id = peg2.operationplan
        and op2.operation = ops.operation
      inner join demand
        on name = %s
      left outer join out_loadplan
        on op2.id = out_loadplan.operationplan_id
      order by ops.id, op2.id
      '''
    cursor.execute(query, baseparams + baseparams + baseparams)

    # Build the Python result
    # due, oper, level, pegged, op_id, op_start, op_end, op_qty, op_res
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
          'depth': rec[2],
          'quantity': str(rec[3]),
          'due': round((rec[0] - request.report_startdate).total_seconds() / horizon, 3),
          'current': round((current - request.report_startdate).total_seconds() / horizon, 3),
          'parent': rec[2] and parents[rec[2] - 1] or None,
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
             'locked': rec[8],
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
