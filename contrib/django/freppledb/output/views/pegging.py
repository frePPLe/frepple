#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

from freppledb.input.models import Demand
from freppledb.output.models import FlowPlan, LoadPlan, OperationPlan
from freppledb.common.report import GridReport, GridFieldText, GridFieldNumber, GridFieldDateTime, getBuckets


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
    GridFieldText('parent', editable=False, sortable=False, hidden=False),
    GridFieldText('leaf', editable=False, sortable=False, hidden=False),
    GridFieldText('expanded', editable=False, sortable=False, hidden=True),
    )

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    return Demand.objects.filter(name__exact=args[0]).values('name')

  @classmethod
  def query(reportclass, request, basequery):
    # Execute the query
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)
    cursor = connections[request.database].cursor()

    # Pick up the list of time buckets
    (bucket,start,end,bucketlist) = getBuckets(request, request.user)
    horizon = (end - start).total_seconds() / 10000

    # query 1: pick up all resources loaded
    resource = {}
    query = '''
      select operationplan_id, theresource
      from out_loadplan
      where operationplan_id in (
        select prod_operationplan as opplan_id
          from out_demandpegging
          where demand in (select dms.name from (%s) dms)
        union
        select cons_operationplan as opplan_id
          from out_demandpegging
          where demand in (select dms.name from (%s) dms)
      )
      ''' % (basesql, basesql)
    cursor.execute(query, baseparams + baseparams)
    for row in cursor.fetchall():
      if row[0] in resource:
        resource[row[0]] += (row[1], )
      else:
        resource[row[0]] = ( row[1], )

    # query 2: pick up all operationplans
    query = '''
      select min(depth), min(opplans.id), operation, opplans.quantity,
        opplans.startdate, opplans.enddate, operation.name,
        max(buffer), max(opplans.item), opplan_id, out_demand.due,
        sum(quantity_demand) / opplans.quantity
      from (
        select depth+1 as depth, peg.id+1 as id, operation, quantity, startdate, enddate,
          buffer, item, prod_operationplan as opplan_id, quantity_demand
        from out_demandpegging peg, out_operationplan prod
        where peg.demand in (select dms.name from (%s) dms)
        and peg.prod_operationplan = prod.id
        union
        select depth, peg.id, operation, quantity, startdate, enddate,
          null, null, cons_operationplan, 0
        from out_demandpegging peg, out_operationplan cons
        where peg.demand in (select dms.name from (%s) dms)
        and peg.cons_operationplan = cons.id
      ) opplans
      left join operation
      on operation = operation.name
      left join out_demand
      on opplan_id = out_demand.operationplan
      group by operation, opplans.quantity, opplans.startdate, opplans.enddate,
        operation.name, opplan_id, out_demand.due
      order by min(depth), operation.name, min(opplans.id)
      ''' % (basesql, basesql)
    cursor.execute(query, baseparams + baseparams)

    # Build the Python result
    prevoper = None
    data = None
    quantity = 0
    for row in cursor.fetchall():
      if row[2] != prevoper:
        if data:
          data['quantity'] = quantity
          yield data
        quantity = float(row[3]) * (row[11] or 1.0)
        data = {
          'depth': row[0],
          'peg_id': row[1],
          'operation': row[2],
          'quantity': row[3],
          'hidden': row[6] == None,
          'buffer': row[7],
          'item': row[8],
          'id': row[9],
          'due': row[10],
          'parent': prevoper or 'null',
          'leaf': str(row[0]) == "7" and 'true' or 'false',
          'expanded': 'true',
          'resource': row[9] in resource and resource[row[9]] or None,
          'operationplans': [{
             'operation': row[2],
             'description': row[11] or 100.0, # TODO percent used
             'quantity': float(row[3]),
             'x': round((row[4] - start).total_seconds() / horizon, 3),
             'w': round((row[5] - row[4]).total_seconds() / horizon, 3),
             'startdate': str(row[4]),
             'enddate': str(row[5]),
             'locked': 0, # TODO
             } ]
          }
        prevoper = row[2]
      else:
        quantity += float(row[3]) * (row[11] or 1.0)
        data['operationplans'].append({
             'operation': row[2],
             'description': row[11] or 100.0, # TODO percent used
             'quantity': float(row[3]),
             'x': round((row[4] - start).total_seconds() / horizon, 3),
             'w': round((row[5] - row[4]).total_seconds() / horizon, 3),
             'startdate': str(row[4]),
             'enddate': str(row[5]),
             'locked': 0, # TODO
             })
    if data:
      data['quantity'] = quantity
      yield data


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
