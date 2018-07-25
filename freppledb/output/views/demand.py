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

import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from freppledb.boot import getAttributeFields
from freppledb.common.report import GridPivot, GridFieldText
from freppledb.input.models import Demand, Item, PurchaseOrder, DistributionOrder, ManufacturingOrder


class OverviewReport(GridPivot):
  '''
  A report showing the independent demand for each item.
  '''
  template = 'output/demand.html'
  title = _('Demand report')
  post_title = _('plan')
  basequeryset = Item.objects.all()
  model = Item
  permissions = (("view_demand_report", "Can view demand report"),)
  rows = (
    GridFieldText('item', title=_('item'), key=True, editable=False, field_name='name', formatter='detail', extra='"role":"input/item"'),
    )
  crosses = (
    ('demand', {'title': _('demand')}),
    ('supply', {'title': _('supply')}),
    ('backlog', {'title': _('backlog')}),
    )
  help_url = 'user-guide/user-interface/plan-analysis/demand-report.html'

  @classmethod
  def initialize(reportclass, request):
    if reportclass._attributes_added != 2:
      reportclass._attributes_added = 2
      reportclass.attr_sql = ''
      # Adding custom item attributes
      for f in getAttributeFields(Item, initially_hidden=True):
        reportclass.attr_sql += 'item.%s, ' % f.name.split('__')[-1]

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plan'
      return {
        'title': force_text(Item._meta.verbose_name) + " " + args[0],
        }
    else:
      return {}

  @classmethod
  def query(reportclass, request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)
    cursor = connections[request.database].cursor()

    # Assure the item hierarchy is up to date
    Item.rebuildHierarchy(database=basequery.db)

    # Execute a query to get the backlog at the start of the horizon
    startbacklogdict = {}
    query = '''
      select items.name, coalesce(req.qty, 0) - coalesce(pln.qty, 0)
      from (%s) items
      left outer join (
        select parent.name, sum(quantity) qty
        from demand
        inner join item on demand.item_id = item.name
        inner join item parent on item.lft between parent.lft and parent.rght
        where status in ('open', 'quote')
        and due < %%s
        group by parent.name
        ) req
      on req.name = items.name
      left outer join (
        select parent.name, sum(operationplan.quantity) qty
        from operationplan
        inner join demand on operationplan.demand_id = demand.name
          and operationplan.owner_id is null
          and operationplan.enddate < %%s
        inner join item on demand.item_id = item.name
        inner join item parent on item.lft between parent.lft and parent.rght
        group by parent.name
        ) pln
      on pln.name = items.name
      ''' % basesql
    cursor.execute(query, baseparams + (request.report_startdate, request.report_startdate))
    for row in cursor.fetchall():
      if row[0]:
        startbacklogdict[row[0]] = float(row[1])

    # Execute the query
    query = '''
        select y.name, %s
               y.bucket, y.startdate, y.enddate,
               min(y.orders),
               min(y.planned)
        from (
          select x.name as name, x.lft as lft, x.rght as rght,
               x.bucket as bucket, x.startdate as startdate, x.enddate as enddate,
               coalesce(sum(demand.quantity),0) as orders,
               min(x.planned) as planned
          from (
          select items.name as name, items.lft as lft, items.rght as rght,
                 d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
                 coalesce(sum(operationplan.quantity),0) as planned
          from (%s) items
          -- Multiply with buckets
          cross join (
             select name as bucket, startdate, enddate
             from common_bucketdetail
             where bucket_id = %%s and enddate > %%s and startdate < %%s
             ) d
          -- Include hierarchical children
          inner join item
          on item.lft between items.lft and items.rght
          -- Planned quantity
          left outer join operationplan
          on operationplan.type = 'DLVR'
          and operationplan.item_id = item.name
          and d.startdate <= operationplan.enddate
          and d.enddate > operationplan.enddate
          and operationplan.enddate >= %%s
          and operationplan.enddate < %%s
          -- Grouping
          group by items.name, items.lft, items.rght, d.bucket, d.startdate, d.enddate
        ) x
        -- Requested quantity
        inner join item
        on item.lft between x.lft and x.rght
        left join demand
        on item.name = demand.item_id
        and x.startdate <= demand.due
        and x.enddate > demand.due
        and demand.due >= %%s
        and demand.due < %%s
        and demand.status in ('open', 'quote')
        -- Grouping
        group by x.name, x.lft, x.rght, x.bucket, x.startdate, x.enddate
        ) y
        -- Ordering and grouping
        group by %s y.name, y.lft, y.rght, y.bucket, y.startdate, y.enddate
        order by %s, y.startdate
       ''' % (reportclass.attr_sql, basesql, reportclass.attr_sql, sortsql)
    cursor.execute(query, baseparams + (
      request.report_bucket, request.report_startdate,
      request.report_enddate, request.report_startdate,
      request.report_enddate, request.report_startdate,
      request.report_enddate
      ))

    # Build the python result
    previtem = None
    for row in cursor.fetchall():
      numfields = len(row)
      if row[0] != previtem:
        backlog = startbacklogdict.get(row[0], 0)
        previtem = row[0]
      backlog += float(row[numfields - 2]) - float(row[numfields - 1])
      res = {
        'item': row[0],
        'bucket': row[numfields - 5],
        'startdate': row[numfields - 4].date(),
        'enddate': row[numfields - 3].date(),
        'demand': round(row[numfields - 2], 1),
        'supply': round(row[numfields - 1], 1),
        'backlog': round(backlog, 1),
        }
      idx = 1
      for f in getAttributeFields(Item):
        res[f.field_name] = row[idx]
        idx += 1
      yield res


@staff_member_required
def OperationPlans(request):
  # Check permissions
  if request.method != "GET" or not request.is_ajax():
    return HttpResponseBadRequest('Only ajax get requests allowed')
  if not request.user.has_perm("view_demand_report"):
    return HttpResponseForbidden('<h1>%s</h1>' % _('Permission denied'))

  # Collect list of selected sales orders
  so_list = request.GET.getlist('demand')

  # Collect operationplans associated with the sales order(s)
  id_list = []
  for dm in Demand.objects.all().using(request.database).filter(pk__in=so_list).only('plan'):
    for op in dm.plan['pegging']:
      id_list.append(op['opplan'])

  # Collect details on the operationplans
  result = []
  for o in PurchaseOrder.objects.all().using(request.database).filter(id__in=id_list, status='proposed'):
    result.append({
      'id': o.id,
      'type': "PO",
      'item': o.item.name,
      'location': o.location.name,
      'origin': o.supplier.name,
      'startdate': str(o.startdate.date()),
      'enddate': str(o.enddate.date()),
      'quantity': float(o.quantity),
      'value': float(o.quantity * o.item.cost),
      'criticality': float(o.criticality)
    })
  for o in DistributionOrder.objects.all().using(request.database).filter(id__in=id_list, status='proposed'):
    result.append({
      'id': o.id,
      'type': "DO",
      'item': o.item.name,
      'location': o.location.name,
      'origin': o.origin.name,
      'startdate': str(o.startdate),
      'enddate': str(o.enddate),
      'quantity': float(o.quantity),
      'value': float(o.quantity * o.item.cost),
      'criticality': float(o.criticality)
    })
  for o in ManufacturingOrder.objects.all().using(request.database).filter(id__in=id_list, status='proposed'):
    result.append({
      'id': o.id,
      'type': "MO",
      'item': '',
      'location': o.operation.location.name,
      'origin': o.operation.name,
      'startdate': str(o.startdate.date()),
      'enddate': str(o.enddate.date()),
      'quantity': float(o.quantity),
      'value': '',
      'criticality': float(o.criticality)
    })

  return HttpResponse(
    content=json.dumps(result),
    content_type='application/json; charset=%s' % settings.DEFAULT_CHARSET
    )
