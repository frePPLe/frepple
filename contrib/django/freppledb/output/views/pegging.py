#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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

from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.utils.translation import ugettext_lazy as _

from freppledb.input.models import Parameter, Demand
from freppledb.output.models import FlowPlan, LoadPlan, OperationPlan
from freppledb.common.report import GridReport, TextGridField, NumberGridField, DateTimeGridField, BoolGridField, getBuckets


class ReportByDemand(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/pegging.html'
  title = _("Demand plan")
  reset_crumbs = False
  basequeryset = Demand.objects.all().values('name')
  frozenColumns = 0
  editable = False
  timebuckets = True
  javascript_imports = [
    "/media/js/core.js",
    "/media/js/calendar.js",
    "/media/js/admin/DateTimeShortcuts.js",
    ]
  rows = (
    TextGridField('depth', title=_('depth'), editable=False),
    TextGridField('operation', title=_('operation'), formatter='operation', editable=False),
    TextGridField('buffer', title=_('buffer'), formatter='buffer', editable=False),
    TextGridField('item', title=_('item'), formatter='item', editable=False),
    TextGridField('resource', title=_('resource'), formatter='resource', editable=False),
    DateTimeGridField('startdate', title=_('start date'), editable=False),
    DateTimeGridField('enddate', title=_('end date'), editable=False),
    NumberGridField('quantity', title=_('quantity'), editable=False),
    NumberGridField('percent_used', title=_('percent_used'), editable=False),
    )

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)
    cursor = connections[request.database].cursor()

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
        sum(quantity_demand) * 100 / opplans.quantity
      from (
        select depth, peg.id+1 as id, operation, quantity, startdate, enddate,
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
      order by min(opplans.id)
      ''' % (basesql, basesql)
    cursor.execute(query, baseparams + baseparams)

    # Build the python result
    for row in cursor.fetchall():
      yield {
          'depth': row[0],
          'peg_id': row[1],
          'operation': row[2],
          'quantity': row[3],
          'startdate': row[4],
          'enddate': row[5],
          'hidden': row[6] == None,
          'buffer': row[7],
          'item': row[8],
          'id': row[9],
          'due': row[10],
          'percent_used': row[11] or 100.0,
          'resource': row[9] in resource and resource[row[9]] or None,
          }


@staff_member_required
def GraphData(request, entity):
  basequery = Demand.objects.filter(name__exact=entity).values('name')
  try:
    current = datetime.strptime(Parameter.objects.using(request.database).get(name="currentdate").value, "%Y-%m-%d %H:%M:%S")
  except:
    current = datetime.now()
  (bucket,start,end,bucketlist) = getBuckets(request)
  result = [ i for i in ReportByDemand.resultlist1(request,basequery,bucket,start,end) ]
  min = None
  max = None

  # extra query: pick up the linked operation plans
  cursor = connections[request.database].cursor()
  query = '''
    select cons_operationplan, prod_operationplan
    from out_demandpegging
    where demand = '%s'
    group by cons_operationplan, prod_operationplan
    ''' % entity
  cursor.execute(query)
  links = [ {'to':row[1], 'from':row[0]} for row in cursor.fetchall() ]

  # Rebuild result list
  for i in result:
    if i['enddate'] < i['startdate'] + timedelta(1):
      i['enddate'] = i['startdate']
    else:
      i['enddate'] = i['enddate'] - timedelta(1)
    if i['startdate'] <= datetime(1971,1,1): i['startdate'] = current
    if i['enddate'] <= datetime(1971,1,1): i['enddate'] = current
    if min == None or i['startdate'] < min: min = i['startdate']
    if max == None or i['enddate'] > max: max = i['enddate']
    if min == None or i['due'] and i['due'] < min: min = i['due']
    if max == None or i['due'] and i['due'] > max: max = i['due']

  # Add a line to mark the current date
  if min <= current and max >= current:
    todayline = current
  else:
    todayline = None

  # Get the time buckets
  (bucket,start,end,bucketlist) = getBuckets(request, start=min, end=max)
  buckets = []
  for i in bucketlist:
    if i['enddate'] >= min and i['startdate'] <= max:
      if i['enddate'] - timedelta(1) >= i['startdate']:
        buckets.append( {'start': i['startdate'], 'end': i['enddate'] - timedelta(1), 'name': i['name']} )
      else:
        buckets.append( {'start': i['startdate'], 'end': i['startdate'], 'name': i['name']} )

  # Snap to dates
  min = min.date()
  max = max.date() + timedelta(1)

  context = {
    'buckets': buckets,
    'reportbucket': bucket,
    'reportstart': start,
    'reportend': end,
    'objectlist1': result,
    'links': links,
    'todayline': todayline,
    }
  return HttpResponse(
    loader.render_to_string("output/pegging.xml", context, context_instance=RequestContext(request)),
    mimetype='application/xml; charset=%s' % settings.DEFAULT_CHARSET
    )


class ReportByBuffer(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/operationpegging.html'
  title = _("Pegging report")
  reset_crumbs = False
  basequeryset = FlowPlan.objects.all()
  frozenColumns = 0
  editable = False
  timebuckets = False
  default_sort = '3a'
  rows = (
    TextGridField('operation', title=_('operation'), formatter='operation', editable=False),
    DateTimeGridField('date', title=_('date'), editable=False),
    TextGridField('demand', title=_('demand'), formatter='demand', editable=False),
    NumberGridField('quantity', title=_('quantity'), editable=False),
    TextGridField('item', title=_('end item'), formatter='item', editable=False),
    )

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.where.as_sql(
      connections[request.database].ops.quote_name,
      connections[request.database])
    if not basesql: basesql = '1 = 1'

    query = '''
        select operation, date, demand, quantity, ditem, fitem
        from
        (
        select out_demandpegging.demand as demand, prod_date as date, operation, sum(quantity_buffer) as quantity, demand.item_id as ditem, forecast.item_id as fitem
        from out_flowplan
        join out_operationplan
        on out_operationplan.id = out_flowplan.operationplan_id
          and %s
          and out_flowplan.quantity > 0
        join out_demandpegging
        on out_demandpegging.prod_operationplan = out_flowplan.operationplan_id
        left join demand
        on demand.name = out_demandpegging.demand
        left join forecast
        on forecast.name = out_demandpegging.demand
        group by out_demandpegging.demand, prod_date, operation, out_operationplan.id, demand.item_id, forecast.item_id
        union
        select out_demandpegging.demand, cons_date as date, operation, -sum(quantity_buffer) as quantity, demand.item_id as ditem, forecast.item_id as fitem
        from out_flowplan
        join out_operationplan
        on out_operationplan.id = out_flowplan.operationplan_id
          and %s
          and out_flowplan.quantity < 0
        join out_demandpegging
        on out_demandpegging.cons_operationplan = out_flowplan.operationplan_id
        left join demand
        on demand.name = out_demandpegging.demand
        left join forecast
        on forecast.name = out_demandpegging.demand
        group by out_demandpegging.demand, cons_date, operation, demand.item_id, forecast.item_id
        ) a
        order by %s
      ''' % (basesql, basesql, sortsql)
    cursor.execute(query, baseparams + baseparams)

    # Build the python result
    for row in cursor.fetchall():
      yield {
          'operation': row[0],
          'date': row[1],
          'demand': row[2],
          'quantity': row[3],
          'forecast': not row[4],
          'item': row[4] or row[5],
          }


class ReportByResource(GridReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/operationpegging.html'
  title = _("Pegging report")
  reset_crumbs = False
  basequeryset = LoadPlan.objects.all()
  frozenColumns = 0
  editable = False
  timebuckets = False
  default_sort = '3a'
  rows = (
    TextGridField('operation', title=_('operation'), formatter='operation', editable=False),
    DateTimeGridField('date', title=_('date'), editable=False),
    TextGridField('demand', title=_('demand'), formatter='demand', editable=False),
    NumberGridField('quantity', title=_('quantity'), editable=False),
    TextGridField('item', title=_('end item'), formatter='item', editable=False),
    )

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.where.as_sql(
      connections[request.database].ops.quote_name,
      connections[request.database])
    if not basesql: basesql = '1 = 1'

    query = '''
        select operation, out_loadplan.startdate as date, out_demandpegging.demand, sum(quantity_buffer), demand.item_id, forecast.item_id
        from out_loadplan
        join out_operationplan
        on out_operationplan.id = out_loadplan.operationplan_id
          and %s
        join out_demandpegging
        on out_demandpegging.prod_operationplan = out_loadplan.operationplan_id
        left join demand
        on demand.name = out_demandpegging.demand
        left join forecast
        on forecast.name = out_demandpegging.demand
        group by out_demandpegging.demand, out_loadplan.startdate, operation, demand.item_id, forecast.item_id
        order by %s
      ''' % (basesql, sortsql)
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
  reset_crumbs = False
  basequeryset = OperationPlan.objects.all()
  frozenColumns = 0
  editable = False
  timebuckets = False
  default_sort = '3a'
  rows = (
    TextGridField('operation', title=_('operation'), formatter='operation', editable=False),
    DateTimeGridField('date', title=_('date'), editable=False),
    TextGridField('demand', title=_('demand'), formatter='demand', editable=False),
    NumberGridField('quantity', title=_('quantity'), editable=False),
    TextGridField('item', title=_('end item'), formatter='item', editable=False),
    )

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.where.as_sql(
      connections[request.database].ops.quote_name,
      connections[request.database])
    if not basesql: basesql = '1 = 1'

    query = '''
        select operation, date, demand, quantity, ditem, fitem
        from
        (
        select out_operationplan.operation as operation, out_operationplan.startdate as date, out_demandpegging.demand as demand, sum(quantity_buffer) as quantity, demand.item_id as ditem, forecast.item_id as fitem
        from out_operationplan
        join out_demandpegging
        on out_demandpegging.prod_operationplan = out_operationplan.id
          and %s
        left join demand
        on demand.name = out_demandpegging.demand
        left join forecast
        on forecast.name = out_demandpegging.demand
        group by out_demandpegging.demand, out_operationplan.startdate, out_operationplan.operation, demand.item_id, forecast.item_id
        union
        select out_operationplan.operation, out_operationplan.startdate as date, out_demand.demand, sum(out_operationplan.quantity), demand.item_id as ditem, forecast.item_id as fitem
        from out_operationplan
        join out_demand
        on out_demand.operationplan = out_operationplan.id
          and %s
        left join demand
        on demand.name = out_demand.demand
        left join forecast
        on forecast.name = out_demand.demand
        group by out_demand.demand, out_operationplan.startdate, out_operationplan.operation, demand.item_id, forecast.item_id
        ) a
        order by %s
      ''' % (basesql, basesql, sortsql)
    cursor.execute(query, baseparams + baseparams)

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
