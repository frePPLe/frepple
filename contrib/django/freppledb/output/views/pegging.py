#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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
from django.utils.translation import ugettext_lazy as _

from freppledb.input.models import Demand
from freppledb.output.models import FlowPlan, LoadPlan, OperationPlan
from freppledb.common.report import GridReport, GridFieldText, GridFieldNumber, GridFieldDateTime
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
    GridFieldText('operation', title=_('operation'), formatter='operation', editable=False, sortable=False, key=True),
    GridFieldText('buffer', title=_('buffer'), formatter='buffer', editable=False, sortable=False),
    GridFieldText('item', title=_('item'), formatter='item', editable=False, sortable=False),
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
    return Demand.objects.filter(name__exact=args[0]).values('name')


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
         on (out_demandpegging.prod_operationplan = out_operationplan.id
             or out_demandpegging.cons_operationplan = out_operationplan.id)
         and out_operationplan.operation not like 'Inventory %%'
      where demand.name = %s
      group by due
       ''', (args[0]))
    (due, start, end) = cursor.fetchone()
    if not start: start = due
    if not end: end = due

    if not isinstance(start, datetime):
      # SQLite max(datetime) function doesn't return a datetime. Sigh.
      start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    if not isinstance(end, datetime):
      # SQLite max(datetime) function doesn't return a datetime. Sigh.
      end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

    # Adjust the horizon
    if due > end: end = due
    if due < start: start =due
    end += timedelta(days=1)
    start -= timedelta(days=1)
    request.report_startdate = start.replace(hour=0, minute=0, second=0, microsecond=0)
    request.report_enddate = end.replace(hour=0, minute=0, second=0, microsecond=0)
    request.report_bucket = None
    request.report_bucketlist = []


  @classmethod
  def query(reportclass, request, basequery):
    # Execute the query
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)
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

    # query 1: pick up all resources loaded
    resource = {}
    query = '''
      select operation, theresource
      from out_loadplan
      inner join out_operationplan
        on out_operationplan.id = out_loadplan.operationplan_id
      where operationplan_id in (
        select prod_operationplan as opplan_id
          from out_demandpegging
          where demand = %s
        union
        select cons_operationplan as opplan_id
          from out_demandpegging
          where demand = %s
      )
      group by operation, theresource
      '''
    cursor.execute(query, baseparams + baseparams)
    for row in cursor.fetchall():
      if row[0] in resource:
        resource[row[0]] += (row[1], )
      else:
        resource[row[0]] = ( row[1], )

    # query 2: collect all operationplans
    query = '''
      select depth, buffer, item, quantity_demand, quantity_buffer, due,
        cons_opplan.id, cons_opplan.operation, cons_opplan.startdate, cons_opplan.enddate, cons_opplan.quantity,
        prod_opplan.id, prod_opplan.operation, prod_opplan.startdate, prod_opplan.enddate, prod_opplan.quantity
      from out_demandpegging peg
      inner join demand
        on peg.demand = demand.name
      left outer join out_operationplan cons_opplan
        on peg.cons_operationplan = cons_opplan.id
      left outer join out_operationplan prod_opplan
        on peg.prod_operationplan = prod_opplan.id
      where peg.demand = %s
      order by peg.id
      '''
    cursor.execute(query, baseparams)

    # Group the results by operations
    opplans = {}
    ops = {}
    indx = 0
    due = None
    for (depth, buf, it, qty_d, qty_b, due, c_id, c_name, c_start, c_end, c_qty, p_id, p_name, p_start, p_end, p_qty) in cursor.fetchall():
      if c_id and not c_id in opplans:
        opplans[c_id] = (c_start,c_end,float(c_qty))
        if c_name in ops:
          ops[c_name][6].append(c_id)
        else:
          ops[c_name] = [indx, depth, None, True, buf, it, [c_id,] ]
      if p_id and not p_id in opplans:
        opplans[p_id] = (p_start,p_end,float(p_qty))
        if p_name in ops:
          ops[p_name][6].append(p_id)
        else:
          ops[p_name] = [indx+1, depth+1, None, True, buf, it, [p_id,] ]
      if c_name and p_name:
        ops[p_name][2] = c_name # set parent
        ops[c_name][3] = False # c_name is no longer a leaf
      indx += 1

    # Build the Python result
    for i in sorted(ops.iteritems(), key=lambda(k,v): (v[0],k)):
      yield {
          'current': str(current),
          'due': str(due),
          'depth': i[1][1],
          'operation': i[0],
          'quantity': sum([opplans[j][2] for j in i[1][6]]),
          'buffer': i[1][4],
          'item': i[1][5],
          'due': round((due - request.report_startdate).total_seconds() / horizon, 3),
          'current': round((current - request.report_startdate).total_seconds() / horizon, 3),
          'parent': i[1][2],
          'leaf': i[1][3] and 'true' or 'false',
          'expanded': 'true',
          'resource': i[0] in resource and resource[i[0]] or None,
          'operationplans': [{
             'operation': i[0],
             #'description': float(row[11]) or 100.0, # TODO percent used
             'quantity': opplans[j][2],
             'x': round((opplans[j][0] - request.report_startdate).total_seconds() / horizon, 3),
             'w': round((opplans[j][1] - opplans[j][0]).total_seconds() / horizon, 3),
             'startdate': str(opplans[j][0]),
             'enddate': str(opplans[j][1]),
             'locked': 0, # TODO
             } for j in i[1][6] ]
          }


class ReportByBuffer(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/operationpegging.html'
  title = _("Pegging report")
  filterable = False
  frozenColumns = 0
  editable = False
  default_sort = (2,'asc')
  rows = (
    GridFieldText('operation', title=_('operation'), formatter='operation', editable=False),
    GridFieldDateTime('date', title=_('date'), editable=False),
    GridFieldText('demand', title=_('demand'), formatter='demand', editable=False),
    GridFieldNumber('quantity', title=_('quantity'), editable=False),
    GridFieldText('item', title=_('end item'), formatter='item', editable=False),
    )

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    # The base query uses different fields than the main query.
    query = FlowPlan.objects.all()
    for i,j in request.GET.iteritems():
      if i.startswith('thebuffer') or i.startswith('flowdate'):
        try: query = query.filter(**{i:j})
        except: pass # silently ignore invalid filters
    return query

  @classmethod
  def query(reportclass, request, basequery):
    # Execute the query
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.where.as_sql(
      connections[request.database].ops.quote_name,
      connections[request.database])
    if not basesql: basesql = '1 = 1'

    query = '''
        select operation, date, demand, quantity, ditem
        from
        (
        select out_demandpegging.demand as demand, prod_date as date, operation, sum(quantity_buffer) as quantity, demand.item_id as ditem
        from out_flowplan
        join out_operationplan
        on out_operationplan.id = out_flowplan.operationplan_id
          and %s
          and out_flowplan.quantity > 0
        join out_demandpegging
        on out_demandpegging.prod_operationplan = out_flowplan.operationplan_id
        left join demand
        on demand.name = out_demandpegging.demand
        group by out_demandpegging.demand, prod_date, operation, out_operationplan.id, demand.item_id
        union
        select out_demandpegging.demand, cons_date as date, operation, -sum(quantity_buffer) as quantity, demand.item_id as ditem
        from out_flowplan
        join out_operationplan
        on out_operationplan.id = out_flowplan.operationplan_id
          and %s
          and out_flowplan.quantity < 0
        join out_demandpegging
        on out_demandpegging.cons_operationplan = out_flowplan.operationplan_id
        left join demand
        on demand.name = out_demandpegging.demand
        group by out_demandpegging.demand, cons_date, operation, demand.item_id
        ) a
        order by %s
      ''' % (basesql, basesql, reportclass.get_sort(request))
    cursor.execute(query, baseparams + baseparams)

    # Build the python result
    for row in cursor.fetchall():
      yield {
          'operation': row[0],
          'date': row[1],
          'demand': row[2],
          'quantity': row[3],
          'forecast': False,
          'item': row[4],
          }


class ReportByResource(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/operationpegging.html'
  title = _("Pegging report")
  filterable = False
  frozenColumns = 0
  editable = False
  default_sort = (2,'asc')
  rows = (
    GridFieldText('operation', title=_('operation'), formatter='operation', editable=False),
    GridFieldDateTime('date', title=_('date'), editable=False),
    GridFieldText('demand', title=_('demand'), formatter='demand', editable=False),
    GridFieldNumber('quantity', title=_('quantity'), editable=False),
    GridFieldText('item', title=_('end item'), formatter='item', editable=False),
    )

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    # The base query uses different fields than the main query.
    query = LoadPlan.objects.all()
    for i,j in request.GET.iteritems():
      if i.startswith('theresource') or i.startswith('startdate') or i.startswith('enddate'):
        try: query = query.filter(**{i:j})
        except: pass # silently ignore invalid filters
    return query

  @classmethod
  def query(reportclass, request, basequery):
    # Execute the query
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.where.as_sql(
      connections[request.database].ops.quote_name,
      connections[request.database])
    if not basesql: basesql = '1 = 1'

    query = '''
        select operation, out_loadplan.startdate as date, out_demandpegging.demand, sum(quantity_buffer), demand.item_id, null
        from out_loadplan
        join out_operationplan
        on out_operationplan.id = out_loadplan.operationplan_id
          and %s
        join out_demandpegging
        on out_demandpegging.prod_operationplan = out_loadplan.operationplan_id
        left join demand
        on demand.name = out_demandpegging.demand
        group by out_demandpegging.demand, out_loadplan.startdate, operation, demand.item_id
        order by %s
      ''' % (basesql, reportclass.get_sort(request))
    cursor.execute(query, baseparams)

    # Build the python result
    for row in cursor.fetchall():
      yield {
          'operation': row[0],
          'date': row[1],
          'demand': row[2],
          'quantity': row[3],
          'forecast': not row[4],
          'item': row[4] or row[5]
          }


class ReportByOperation(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/operationpegging.html'
  title = _("Pegging report")
  filterable = False
  frozenColumns = 0
  editable = False
  default_sort = (2,'asc')
  rows = (
    GridFieldText('operation', title=_('operation'), formatter='operation', editable=False),
    GridFieldDateTime('date', title=_('date'), editable=False),
    GridFieldText('demand', title=_('demand'), formatter='demand', editable=False),
    GridFieldNumber('quantity', title=_('quantity'), editable=False),
    GridFieldText('item', title=_('end item'), formatter='item', editable=False),
    )

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    # The base query uses different fields than the main query.
    query = OperationPlan.objects.all()
    for i,j in request.GET.iteritems():
      if i.startswith('operation') or i.startswith('startdate') or i.startswith('enddate'):
        try: query = query.filter(**{i:j})
        except: pass # silently ignore invalid filters
    return query

  @classmethod
  def query(reportclass, request, basequery):
    # Execute the query
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.where.as_sql(
      connections[request.database].ops.quote_name,
      connections[request.database])
    if not basesql: basesql = '1 = 1'

    query = '''
        select operation, date, demand, quantity, ditem
        from
        (
        select out_operationplan.operation as operation, out_operationplan.startdate as date, out_demandpegging.demand as demand, sum(quantity_buffer) as quantity, demand.item_id as ditem
        from out_operationplan
        join out_demandpegging
        on out_demandpegging.prod_operationplan = out_operationplan.id
          and %s
        left join demand
        on demand.name = out_demandpegging.demand
        group by out_demandpegging.demand, out_operationplan.startdate, out_operationplan.operation, demand.item_id
        union
        select out_operationplan.operation, out_operationplan.startdate as date, out_demand.demand, sum(out_operationplan.quantity), demand.item_id as ditem
        from out_operationplan
        join out_demand
        on out_demand.operationplan = out_operationplan.id
          and %s
        left join demand
        on demand.name = out_demand.demand
        group by out_demand.demand, out_operationplan.startdate, out_operationplan.operation, demand.item_id
        ) a
        order by %s
      ''' % (basesql, basesql, reportclass.get_sort(request))
    cursor.execute(query, baseparams + baseparams)

    # Build the python result
    for row in cursor.fetchall():
      yield {
          'operation': row[0],
          'date': row[1],
          'demand': row[2],
          'quantity': row[3],
          'item': row[4]
          }
