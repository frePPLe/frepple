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
from django.utils.translation import string_concat
from django.utils.encoding import force_text

from freppledb.input.models import Operation, DistributionOrder, PurchaseOrder
from freppledb.common.report import getHorizon, GridFieldNumber, GridFieldInteger
from freppledb.common.report import GridPivot, GridFieldText, GridFieldDuration
from freppledb.common.report import GridFieldCurrency, GridFieldDateTime, GridFieldLastModified


class OverviewReport(GridPivot):
  '''
  A report summarizing all manufacturing orders.
  '''
  template = 'output/operation.html'
  title = _('Manufacturing order summary')
  model = Operation
  permissions = (("view_operation_report", "Can view operation report"),)
  help_url = 'user-guide/user-interface/plan-analysis/manufacturing-order-summary.html'

  rows = (
    GridFieldText(
      'operation', title=_('operation'), key=True, editable=False, field_name='name',
      formatter='detail', extra='"role":"input/operation"'
      ),
    GridFieldText(
      'location', title=_('location'), editable=False, field_name='location__name',
      formatter='detail', extra='"role":"input/location"'
      ),
    # Optional fields on the operation
    GridFieldText(
      'item', title=_('item'), editable=False, field_name="item__name",
      formatter='detail', extra='"role":"input/item"', initially_hidden=True
      ),
    GridFieldText(
      'description', title=_('description'), editable=False, initially_hidden=True
      ),
    GridFieldText(
      'category', title=_('category'), editable=False, initially_hidden=True
      ),
    GridFieldText(
      'subcategory', title=_('subcategory'), editable=False, initially_hidden=True
      ),
    GridFieldText(
      'type', title=_('type'), initially_hidden=True, editable=False
      ),
    GridFieldDuration(
      'duration', title=_('duration'), initially_hidden=True, editable=False
      ),
    GridFieldDuration(
      'duration_per', title=_('duration per unit'), initially_hidden=True, editable=False
      ),
    GridFieldDuration(
      'fence', title=_('release fence'), initially_hidden=True, editable=False
      ),
    GridFieldDuration(
      'posttime', title=_('post-op time'), initially_hidden=True, editable=False
      ),
    GridFieldNumber(
      'sizeminimum', title=_('size minimum'), initially_hidden=True, editable=False
      ),
    GridFieldNumber(
      'sizemultiple', title=_('size multiple'), initially_hidden=True, editable=False
      ),
    GridFieldNumber(
      'sizemaximum', title=_('size maximum'), initially_hidden=True, editable=False
      ),
    GridFieldInteger(
      'priority', title=_('priority'), initially_hidden=True, editable=False
      ),
    GridFieldDateTime(
      'effective_start', title=_('effective start'), initially_hidden=True, editable=False
      ),
    GridFieldDateTime(
      'effective_end', title=_('effective end'), initially_hidden=True, editable=False
      ),
    GridFieldCurrency(
      'cost', title=_('cost'), initially_hidden=True, editable=False
      ),
    GridFieldText(
      'search', title=_('search mode'), initially_hidden=True, editable=False
      ),
    GridFieldText(
      'source', title=_('source'), initially_hidden=True, editable=False
      ),
    GridFieldLastModified(
      'lastmodified', initially_hidden=True, editable=False
      ),
    # Optional fields on the location
    GridFieldText(
      'location__description', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('description'))
      ),
    GridFieldText(
      'location__category', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('category'))
      ),
    GridFieldText(
      'location__subcategory', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'location__available', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('available')),
      field_name='location__available__name',
      formatter='detail', extra='"role":"input/calendar"'
      ),
    GridFieldLastModified(
      'location__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('location'), ' - ', _('last modified'))
      ),
    # Optional fields referencing the item
    GridFieldText(
      'item__description', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('description'))
      ),
    GridFieldText(
      'item__category', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('category'))
      ),
    GridFieldText(
      'item__subcategory', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'item__owner', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('owner')),
      field_name='item__owner__name'
      ),
    GridFieldText(
      'item__source', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'item__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('last modified'))
      ),
    )

  crosses = (
    ('proposed_start', {'title': _('proposed starts')}),
    ('total_start', {'title': _('total starts')}),
    ('proposed_end', {'title': _('proposed ends')}),
    ('total_end', {'title': _('total ends')}),
    ('production_proposed', {'title': _('proposed production')}),
    ('production_total', {'title': _('total production')}),
    )


  @staticmethod
  def basequeryset(request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plan'
      return Operation.objects.all()
    else:
      current, start, end = getHorizon(request)
      return Operation.objects.all().extra(
        where=['exists (select 1 from operationplan where operationplan.operation_id = operation.name and startdate <= %s and enddate >= %s)'],
        params=[end, start]
        )


  @staticmethod
  def extra_context(request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plan'
      return {
        'title': force_text(Operation._meta.verbose_name) + " " + args[0],
        'post_title': _('plan')
        }
    else:
      return {}

  @staticmethod
  def query(request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)
    # Run the query
    cursor = connections[request.database].cursor()
    query = '''
      select
        operation.name, location.name, operation.item_id, operation.description,
        operation.category, operation.subcategory, operation.type, operation.duration,
        operation.duration_per, operation.fence, operation.posttime, operation.sizeminimum,
        operation.sizemultiple, operation.sizemaximum, operation.priority, operation.effective_start,
        operation.effective_end, operation.cost, operation.search, operation.source, operation.lastmodified,
        location.description, location.category, location.subcategory, location.available_id,
        location.lastmodified, item.description, item.category, item.subcategory, item.owner_id,
        item.source, item.lastmodified,
        res.bucket, res.startdate, res.enddate,
        res.proposed_start, res.total_start, res.proposed_end, res.total_end, res.proposed_production, res.total_production
      from operation
      left outer join item
      on operation.item_id = item.name
      left outer join location
      on operation.location_id = location.name
      inner join (
        select oper.name as operation_id, d.bucket, d.startdate, d.enddate,
         coalesce(sum(
           case when operationplan.status = 'proposed'
             and d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
           then operationplan.quantity
           else 0 end
           ), 0) proposed_start,
         coalesce(sum(
           case when d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
           then operationplan.quantity else 0 end
           ), 0) total_start,
         coalesce(sum(
           case when operationplan.status = 'proposed'
             and d.startdate < operationplan.enddate and d.enddate >= operationplan.enddate
           then operationplan.quantity else 0 end
           ), 0) proposed_end,
         coalesce(sum(
           case when d.startdate < operationplan.enddate and d.enddate >= operationplan.enddate
           then operationplan.quantity else 0 end
           ), 0) total_end,
         coalesce(sum(
           case when operationplan.status = 'proposed' then
             (
             -- Total overlap
             extract (epoch from least(operationplan.enddate, d.enddate) - greatest(operationplan.startdate, d.startdate))
             -- Minus the interruptions
             - coalesce((
                select sum(greatest(0, extract (epoch from
                  least(to_timestamp(value->>1, 'YYYY-MM-DD HH24:MI:SS'), d.enddate)
                  - greatest(to_timestamp(value->>0, 'YYYY-MM-DD HH24:MI:SS'), d.startdate)
                  )))
                from ( select * from jsonb_array_elements(plan->'interruptions')) breaks
                ), 0)
             )
             / greatest(1, extract(epoch from operationplan.enddate - operationplan.startdate) - coalesce((plan#>>'{unavailable}')::numeric, 0))
             * operationplan.quantity
           else 0 end
           ), 0) proposed_production,
         coalesce(sum(
             (
             -- Total overlap
             extract (epoch from least(operationplan.enddate, d.enddate) - greatest(operationplan.startdate, d.startdate))
             -- Minus the interruptions
             - coalesce((
                select sum(greatest(0, extract (epoch from
                  least(to_timestamp(value->>1, 'YYYY-MM-DD HH24:MI:SS'), d.enddate)
                  - greatest(to_timestamp(value->>0, 'YYYY-MM-DD HH24:MI:SS'), d.startdate)
                  )))
                from ( select * from jsonb_array_elements(plan->'interruptions')) breaks
                ), 0)
             )
           / greatest(1, extract(epoch from operationplan.enddate - operationplan.startdate) - coalesce((plan#>>'{unavailable}')::numeric, 0))
           * operationplan.quantity
           ), 0) total_production
        from (%s) oper
        -- Multiply with buckets
        cross join (
          select name as bucket, startdate, enddate
          from common_bucketdetail
          where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
          ) d
        -- Match overlapping operationplans
        left outer join operationplan
          on operationplan.operation_id = oper.name
          and (operationplan.startdate, operationplan.enddate) overlaps (d.startdate, d.enddate)
        group by oper.name, d.bucket, d.startdate, d.enddate
      ) res
      on res.operation_id = operation.name
      order by %s, res.startdate
      ''' % (
        basesql, request.report_bucket,
        request.report_startdate, request.report_enddate, sortsql
        )
    cursor.execute(query, baseparams)

    # Convert the SQl results to Python
    for row in cursor.fetchall():
      yield {
        'operation': row[0],
        'location': row[1],
        'item': row[2],
        'description': row[3],
        'category': row[4],
        'subcategory': row[5],
        'type': row[6],
        'duration': row[7],
        'duration_per': row[8],
        'fence': row[9],
        'posttime': row[10],
        'sizeminimum': row[11],
        'sizemultiple': row[12],
        'sizemaximum': row[13],
        'priority': row[14],
        'effective_start': row[15],
        'effective_end': row[16],
        'cost': row[17],
        'search': row[18],
        'source': row[19],
        'lastmodified': row[20],
        'location__description': row[21],
        'location__category': row[22],
        'location__subcategory': row[23],
        'location__available': row[24],
        'location__lastmodified': row[25],
        'item__description': row[26],
        'item__category': row[27],
        'item__subcategory': row[28],
        'item__owner': row[29],
        'item__source': row[30],
        'item__lastmodified': row[31],
        'bucket': row[32],
        'startdate': row[33].date(),
        'enddate': row[34].date(),
        'proposed_start': row[35],
        'total_start': row[36],
        'proposed_end': row[37],
        'total_end': row[38],
        'production_proposed': row[39],
        'production_total': row[40]
        }


class PurchaseReport(GridPivot):
  '''
  A report summarizing all purchase orders.
  '''
  template = 'output/purchase_order_summary.html'
  title = _('Purchase order summary')
  model = PurchaseOrder
  help_url = 'user-guide/user-interface/plan-analysis/purchase-order-summary.html'

  rows = (
    GridFieldText('key', key=True, search=False, initially_hidden=True, hidden=True, field_name="item__name", editable=False),
    GridFieldText(
      'item', title=_('item'), editable=False, field_name='item__name',
      formatter='detail', extra='"role":"input/item"'
      ),
    GridFieldText(
      'item__description', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('description'))
      ),
    GridFieldText(
      'item__category', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('category'))
      ),
    GridFieldText(
      'item__subcategory', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('subcategory'))
      ),
    GridFieldCurrency(
      'item__cost', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('cost')),
      field_name='item__cost'
      ),
    GridFieldText(
      'item__owner', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('owner')),
      field_name='item__owner__name'
      ),
    GridFieldText(
      'item__source', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'item__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('last modified'))
      ),
    GridFieldText(
      'location', title=_('location'), editable=False, field_name='location__name',
      formatter='detail', extra='"role":"input/location"'
      ),
    GridFieldText(
      'location__description', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('description'))
      ),
    GridFieldText(
      'location__category', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('category'))
      ),
    GridFieldText(
      'location__subcategory', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'location__available', editable=False, initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('available')),
      field_name='location__available__name',
      formatter='detail', extra='"role":"input/calendar"'
      ),
    GridFieldLastModified(
      'location__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('location'), ' - ', _('last modified'))
      ),
    GridFieldText(
      'supplier', title=_('supplier'), editable=False, field_name='supplier__name',
      formatter='detail', extra='"role":"input/supplier"'
      ),
    GridFieldText(
      'supplier__description', initially_hidden=True, editable=False,
      title=string_concat(_('supplier'), ' - ', _('description'))
      ),
    GridFieldText(
      'supplier__category', initially_hidden=True, editable=False,
      title=string_concat(_('supplier'), ' - ', _('category'))
      ),
    GridFieldText(
      'supplier__subcategory', initially_hidden=True, editable=False,
      title=string_concat(_('supplier'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'supplier__owner', initially_hidden=True, editable=False,
      title=string_concat(_('supplier'), ' - ', _('owner')),
      field_name='supplier__owner__name'
      ),
    GridFieldText(
      'supplier__source', initially_hidden=True, editable=False,
      title=string_concat(_('supplier'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'supplier__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('supplier'), ' - ', _('last modified'))
      ),
    )

  crosses = (
    ('proposed_start', {'title': _('proposed ordering')}),
    ('total_start', {'title': _('total ordering')}),
    ('proposed_end', {'title': _('proposed receiving')}),
    ('total_end', {'title': _('total receiving')}),
    ('proposed_on_order', {'title': _('proposed on order')}),
    ('total_on_order', {'title': _('total on order')}),
    )


  @staticmethod
  def basequeryset(request, *args, **kwargs):
    current, start, end = getHorizon(request)
    return PurchaseOrder.objects.all() \
      .filter(startdate__lte=end, enddate__gte=start) \
      .distinct('item', 'supplier', 'location') \
      .order_by()   # Ordering isn't compatible with the distinct


  @staticmethod
  def query(request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)
    # Run the query
    cursor = connections[request.database].cursor()
    query = '''
      with combinations as (%s)
      select row_to_json(data)
      from (
      select
        -- Key field
        combinations.item_id || combinations.location_id || combinations.supplier_id as key,
        -- Attribute fields of item, location and supplier
        combinations.item_id as item,
        item.description as item__description,
        item.category as item__category,
        item.subcategory as item__subcategory,
        item.cost as item__cost,
        item.owner_id as item__owner,
        item.source as item__source,
        item.lastmodified as item__lastmodified,
        combinations.location_id as location,
        location.description as location__description,
        location.category as location__category,
        location.subcategory as location__subcategory,
        location.available_id as location__available,
        location.lastmodified as location__lastmodified,
        combinations.supplier_id as supplier,
        supplier.description as supplier__description,
        supplier.category as supplier__category,
        supplier.subcategory as supplier_subcategory,
        supplier.owner_id as supplier__owner,
        supplier.source as supplier__source,
        supplier.lastmodified as supplier_lastmodified,
        -- Buckets
        res.bucket as bucket,
        to_char(res.startdate, 'YYYY-MM-DD') as startdate,
        to_char(res.enddate, 'YYYY-MM-DD') as enddate,
        -- Values
        res.proposed_start as proposed_start,
        res.total_start as total_start,
        res.proposed_end as proposed_end,
        res.total_end as total_end,
        res.proposed_on_order as proposed_on_order,
        res.total_on_order as total_on_order
      from combinations
      inner join item on combinations.item_id = item.name
      left outer join location on combinations.location_id = location.name
      left outer join supplier on combinations.supplier_id = supplier.name
      inner join (
        select
          operationplan.item_id, operationplan.location_id, operationplan.supplier_id,
          d.bucket, d.startdate, d.enddate,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity
            else 0 end
            ), 0) proposed_start,
          coalesce(sum(
            case when d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity else 0 end
            ), 0) total_start,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_end,
          coalesce(sum(
            case when d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_end,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_on_order,
          coalesce(sum(
            case when d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_on_order
        from operationplan
        inner join  combinations
        on operationplan.item_id = combinations.item_id
          and operationplan.location_id = combinations.location_id
          and operationplan.supplier_id = combinations.supplier_id
        cross join (
          select name as bucket, startdate, enddate
          from common_bucketdetail
          where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
          ) d
        where operationplan.type = 'PO'
        group by operationplan.item_id, operationplan.location_id, operationplan.supplier_id,
          d.bucket, d.startdate, d.enddate
        ) res
      on res.item_id = combinations.item_id
        and res.location_id = combinations.location_id
        and res.supplier_id = combinations.supplier_id
      order by %s, res.startdate
      ) data
      ''' % (
        basesql, request.report_bucket,
        request.report_startdate, request.report_enddate, sortsql
        )
    cursor.execute(query, baseparams)

    # Convert the SQL results to Python
    for row in cursor.fetchall():
      yield row[0]


class DistributionReport(GridPivot):
  '''
  A report summarizing all distribution orders.
  '''
  template = 'output/distribution_order_summary.html'
  title = _('Distribution order summary')
  model = DistributionOrder
  help_url = 'user-guide/user-interface/plan-analysis/distribution-order-summary.html'

  rows = (
    GridFieldText('key', key=True, search=False, initially_hidden=True, hidden=True, field_name="item__name", editable=False),
    GridFieldText(
      'item', title=_('item'), editable=False, field_name='item__name',
      formatter='detail', extra='"role":"input/item"'
      ),
    GridFieldText(
      'item__description', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('description'))
      ),
    GridFieldText(
      'item__category', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('category'))
      ),
    GridFieldText(
      'item__subcategory', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('subcategory'))
      ),
    GridFieldCurrency(
      'item__cost', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('cost')),
      field_name='item__cost'
      ),
    GridFieldText(
      'item__owner', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('owner')),
      field_name='item__owner__name'
      ),
    GridFieldText(
      'item__source', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'item__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('last modified'))
      ),
    GridFieldText(
      'origin', title=_('origin'), editable=False, field_name='origin__name',
      formatter='detail', extra='"role":"input/location"'
      ),
    GridFieldText(
      'origin__description', editable=False, initially_hidden=True,
      title=string_concat(_('origin'), ' - ', _('description'))
      ),
    GridFieldText(
      'origin__category', editable=False, initially_hidden=True,
      title=string_concat(_('origin'), ' - ', _('category'))
      ),
    GridFieldText(
      'origin__subcategory', editable=False, initially_hidden=True,
      title=string_concat(_('origin'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'origin__available', editable=False, initially_hidden=True,
      title=string_concat(_('origin'), ' - ', _('available')),
      field_name='origin__available__name',
      formatter='detail', extra='"role":"input/calendar"'
      ),
    GridFieldLastModified(
      'origin__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('origin'), ' - ', _('last modified'))
      ),
    GridFieldText(
      'destination', title=_('destination'), editable=False, field_name='destination__name',
      formatter='detail', extra='"role":"input/location"'
      ),
    GridFieldText(
      'destination__description', editable=False, initially_hidden=True,
      title=string_concat(_('destination'), ' - ', _('description'))
      ),
    GridFieldText(
      'destination__category', editable=False, initially_hidden=True,
      title=string_concat(_('destination'), ' - ', _('category'))
      ),
    GridFieldText(
      'destination__subcategory', editable=False, initially_hidden=True,
      title=string_concat(_('destination'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'destination__available', editable=False, initially_hidden=True,
      title=string_concat(_('destination'), ' - ', _('available')),
      field_name='destination__available__name',
      formatter='detail', extra='"role":"input/calendar"'
      ),
    GridFieldLastModified(
      'destination__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('destination'), ' - ', _('last modified'))
      ),
    )

  crosses = (
    ('proposed_start', {'title': _('proposed shipping')}),
    ('total_start', {'title': _('total shipping')}),
    ('proposed_end', {'title': _('proposed receiving')}),
    ('total_end', {'title': _('total receiving')}),
    ('proposed_in_transit', {'title': _('proposed in transit')}),
    ('total_in_transit', {'title': _('total in transit')}),
    )


  @staticmethod
  def basequeryset(request, *args, **kwargs):
    current, start, end = getHorizon(request)
    return DistributionOrder.objects.all() \
      .filter(startdate__lte=end, enddate__gte=start) \
      .distinct('item', 'origin', 'destination') \
      .order_by()   # Ordering isn't compatible with the distinct


  @staticmethod
  def query(request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)
    # Run the query
    cursor = connections[request.database].cursor()
    query = '''
      with combinations as (%s)
      select row_to_json(data)
      from (
      select
        -- Key field
        combinations.item_id || combinations.origin_id || combinations.destination_id as key,
        -- Attribute fields of item, location and supplier
        combinations.item_id as item,
        item.description as item__description,
        item.category as item__category,
        item.subcategory as item__subcategory,
        item.cost as item__cost,
        item.owner_id as item__owner,
        item.source as item__source,
        item.lastmodified as item__lastmodified,
        combinations.origin_id as origin,
        origin.description as origin__description,
        origin.category as origin__category,
        origin.subcategory as origin__subcategory,
        origin.available_id as origin__available,
        origin.lastmodified as origin__lastmodified,
        combinations.destination_id as destination,
        destination.description as destination__description,
        destination.category as destination__category,
        destination.subcategory as destination__subcategory,
        destination.available_id as destination__available,
        destination.lastmodified as destination__lastmodified,
        -- Buckets
        res.bucket as bucket,
        to_char(res.startdate, 'YYYY-MM-DD') as startdate,
        to_char(res.enddate, 'YYYY-MM-DD') as enddate,
        -- Values
        res.proposed_start as proposed_start,
        res.total_start as total_start,
        res.proposed_end as proposed_end,
        res.total_end as total_end,
        res.proposed_in_transit as proposed_in_transit,
        res.total_in_transit as total_in_transit
      from combinations
      inner join item on combinations.item_id = item.name
      left outer join location origin on combinations.origin_id = origin.name
      left outer join location destination on combinations.destination_id = destination.name
      inner join (
        select
          operationplan.item_id, operationplan.origin_id, operationplan.destination_id,
          d.bucket, d.startdate, d.enddate,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity
            else 0 end
            ), 0) proposed_start,
          coalesce(sum(
            case when d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity else 0 end
            ), 0) total_start,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_end,
          coalesce(sum(
            case when d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_end,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_in_transit,
          coalesce(sum(
            case when d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_in_transit
        from operationplan
        inner join combinations
        on operationplan.item_id = combinations.item_id
          and operationplan.origin_id = combinations.origin_id
          and operationplan.destination_id = combinations.destination_id
        cross join (
          select name as bucket, startdate, enddate
          from common_bucketdetail
          where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
          ) d
        where operationplan.type = 'DO'
        group by operationplan.item_id, operationplan.origin_id, operationplan.destination_id,
          d.bucket, d.startdate, d.enddate
        ) res
      on res.item_id = combinations.item_id
        and res.origin_id = combinations.origin_id
        and res.destination_id = combinations.destination_id
      order by %s, res.startdate
      ) data
      ''' % (
        basesql, request.report_bucket,
        request.report_startdate, request.report_enddate, sortsql
        )
    cursor.execute(query, baseparams)

    # Convert the SQL results to Python
    for row in cursor.fetchall():
      yield row[0]
