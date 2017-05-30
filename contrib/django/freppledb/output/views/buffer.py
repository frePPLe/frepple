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
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat

from freppledb.boot import getAttributeFields
from freppledb.input.models import Buffer, Item, Location, OperationPlanMaterial
from freppledb.common.report import GridReport, GridPivot, GridFieldText, GridFieldNumber
from freppledb.common.report import GridFieldDateTime, GridFieldInteger, GridFieldDuration
from freppledb.common.report import GridFieldCurrency, GridFieldLastModified


class OverviewReport(GridPivot):
  '''
  A report showing the inventory profile of buffers.
  '''
  template = 'output/buffer.html'
  title = _('Inventory report')
  basequeryset = Buffer.objects.only('name', 'item__name', 'location__name', 'lft', 'rght', 'onhand')
  model = Buffer
  permissions = (('view_inventory_report', 'Can view inventory report'),)
  help_url = 'user-guide/user-interface/plan-analysis/inventory-report.html'
  rows = (
    GridFieldText('buffer', title=_('buffer'), key=True, editable=False, field_name='name', formatter='detail', extra='"role":"input/buffer"'),
    GridFieldText('item', title=_('item'), editable=False, field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), editable=False, field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    )
  crosses = (
    ('startoh', {'title': _('start inventory')}),
    ('produced', {'title': _('produced')}),
    ('consumed', {'title': _('consumed')}),
    ('endoh', {'title': _('end inventory')}),
    )

  @classmethod
  def initialize(reportclass, request):
    if reportclass._attributes_added != 2:
      reportclass._attributes_added = 2
      reportclass.attr_sql = ''
      # Adding custom item attributes
      for f in getAttributeFields(Item, related_name_prefix="item", initially_hidden=True):
        reportclass.rows += (f,)
        reportclass.attr_sql += 'item.%s, ' % f.name.split('__')[-1]
      # Adding custom location attributes
      for f in getAttributeFields(Location, related_name_prefix="location", initially_hidden=True):
        reportclass.rows += (f,)
        reportclass.attr_sql += 'location.%s, ' % f.name.split('__')[-1]

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plan'
      return {
        'title': force_text(Buffer._meta.verbose_name) + " " + args[0],
        'post_title': _('plan')
        }
    else:
      return {}

  @classmethod
  def query(reportclass, request, basequery, sortsql='1 asc'):
    cursor = connections[request.database].cursor()
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)

    # Assure the item hierarchy is up to date
    Buffer.rebuildHierarchy(database=basequery.db)

    # Execute a query  to get the onhand value at the start of our horizon
    startohdict = {}
    query = '''
      select buffers.name, sum(oh.onhand)
      from (%s) buffers
      inner join buffer
      on buffer.lft between buffers.lft and buffers.rght
      inner join (
        select operationplanmaterial.item_id,
          operationplanmaterial.location_id,
          operationplanmaterial.onhand as onhand
        from operationplanmaterial,
          (select item_id, location_id, max(id) as id
           from operationplanmaterial
           where flowdate < '%s'
           group by item_id, location_id
          ) maxid
        where maxid.item_id = operationplanmaterial.item_id
          and maxid.location_id = operationplanmaterial.location_id
        and maxid.id = operationplanmaterial.id
      ) oh
      on oh.item_id = buffer.item_id
      and oh.location_id = buffer.location_id
      group by buffers.name
      ''' % (basesql, request.report_startdate)
    cursor.execute(query, baseparams)
    for row in cursor.fetchall():
      startohdict[row[0]] = float(row[1])

    # Execute the actual query
    query = '''
      select
        invplan.name, invplan.item_id, invplan.location_id, %s
        invplan.bucket, invplan.startdate, invplan.enddate,
        invplan.consumed, invplan.produced
      from (
        select
          buf.name, buf.item_id, buf.location_id,
          d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
          coalesce(sum(greatest(operationplanmaterial.quantity, 0)),0) as consumed,
          coalesce(-sum(least(operationplanmaterial.quantity, 0)),0) as produced
        from (%s) buf
        -- Multiply with buckets
        cross join (
             select name as bucket, startdate, enddate
             from common_bucketdetail
             where bucket_id = %%s and enddate > %%s and startdate < %%s
             ) d
        -- Include child buffers
        inner join buffer
        on buffer.lft between buf.lft and buf.rght
        -- Consumed and produced quantities
        left join operationplanmaterial
        on buffer.item_id = operationplanmaterial.item_id
        and buffer.location_id = operationplanmaterial.location_id
        and d.startdate <= operationplanmaterial.flowdate
        and d.enddate > operationplanmaterial.flowdate
        and operationplanmaterial.flowdate >= %%s
        and operationplanmaterial.flowdate < %%s
        -- Grouping and sorting
        group by buf.name, buf.item_id, buf.location_id, buf.onhand, d.bucket, d.startdate, d.enddate
        ) invplan
      left outer join buffer on
        invplan.name = buffer.name
      left outer join item on
        buffer.item_id = item.name
      left outer join location on
        buffer.location_id = location.name
      order by %s, invplan.startdate
      ''' % (
        reportclass.attr_sql, basesql, sortsql
      )
    cursor.execute(
      query, baseparams + (
        request.report_bucket, request.report_startdate,
        request.report_enddate, request.report_startdate, request.report_enddate
        )
      )

    # Build the python result
    prevbuf = None
    for row in cursor.fetchall():
      numfields = len(row)
      if row[0] != prevbuf:
        prevbuf = row[0]
        startoh = startohdict.get(prevbuf, 0)
        endoh = startoh + float(row[numfields - 2] - row[numfields - 1])
      else:
        startoh = endoh
        endoh += float(row[numfields - 2] - row[numfields - 1])
      res = {
        'buffer': row[0],
        'item': row[1],
        'location': row[2],
        'bucket': row[numfields - 5],
        'startdate': row[numfields - 4].date(),
        'enddate': row[numfields - 3].date(),
        'startoh': round(startoh, 1),
        'produced': round(row[numfields - 2], 1),
        'consumed': round(row[numfields - 1], 1),
        'endoh': round(endoh, 1),
        }
      # Add attribute fields
      idx = 3
      for f in getAttributeFields(Item, related_name_prefix="item"):
        res[f.field_name] = row[idx]
        idx += 1
      for f in getAttributeFields(Location, related_name_prefix="location"):
        res[f.field_name] = row[idx]
        idx += 1
      yield res


class DetailReport(GridReport):
  '''
  A list report to show OperationPlanMaterial.
  '''
  template = 'input/operationplanreport.html'
  title = _("Inventory detail report")
  model = OperationPlanMaterial
  permissions = (('view_inventory_report', 'Can view inventory report'),)
  frozenColumns = 0
  editable = False
  multiselect = False
  height = 250
  help_url = 'user-guide/user-interface/plan-analysis/inventory-detail-report.html'

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    if len(args) and args[0]:
      dlmtr = args[0].find(" @ ")
      base = OperationPlanMaterial.objects.filter(
        item=args[0][:dlmtr], location=args[0][dlmtr + 3:]
        )
    else:
      base = OperationPlanMaterial.objects
    return base.select_related().extra(select={
      'pegging': "(select string_agg(value || ' : ' || key, ', ') from (select key, value from jsonb_each_text(plan->'pegging') order by key desc) peg)"
      })

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plandetail'
      return {
        'active_tab': 'plandetail',
        'model': Buffer,
        'title': force_text(Buffer._meta.verbose_name) + " " + args[0],
        'post_title': _('plan detail')
        }
    else:
      return {'active_tab': 'plandetail', 'model': None}

  rows = (
    #. Translators: Translation included with Django
    GridFieldInteger('id', title=_('internal id'), key=True, editable=False, hidden=True),
    GridFieldText('item', title=_('item'), field_name='item__name', editable=False, formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), field_name='location__name', editable=False, formatter='detail', extra='"role":"input/location"'),
    GridFieldInteger('operationplan__id', title=_('identifier'), editable=False),
    GridFieldText('operationplan__reference', title=_('reference'), editable=False),
    GridFieldText('operationplan__color', title=_('inventory status'), formatter='color', width='125', editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"'),
    GridFieldText('operationplan__type', title=_('type'), field_name='operationplan__type', editable=False),
    GridFieldText('operationplan__name', title=_('operation'), editable=False, field_name='operationplan__name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('operationplan__operation__description', title=string_concat(_('operation'), ' - ', _('description')), editable=False, initially_hidden=True),
    GridFieldText('operationplan__operation__category', title=string_concat(_('operation'), ' - ', _('category')), editable=False, initially_hidden=True),
    GridFieldText('operationplan__operation__subcategory', title=string_concat(_('operation'), ' - ', _('subcategory')), editable=False, initially_hidden=True),
    GridFieldText('operationplan__operation__type', title=string_concat(_('operation'), ' - ', _('type')), initially_hidden=True),
    GridFieldDuration('operationplan__operation__duration', title=string_concat(_('operation'), ' - ', _('duration')), initially_hidden=True),
    GridFieldDuration('operationplan__operation__duration_per', title=string_concat(_('operation'), ' - ', _('duration per unit')), initially_hidden=True),
    GridFieldDuration('operationplan__operation__fence', title=string_concat(_('operation'), ' - ', _('release fence')), initially_hidden=True),
    GridFieldDuration('operationplan__operation__posttime', title=string_concat(_('operation'), ' - ', _('post-op time')), initially_hidden=True),
    GridFieldNumber('operationplan__operation__sizeminimum', title=string_concat(_('operation'), ' - ', _('size minimum')), initially_hidden=True),
    GridFieldNumber('operationplan__operation__sizemultiple', title=string_concat(_('operation'), ' - ', _('size multiple')), initially_hidden=True),
    GridFieldNumber('operationplan__operation__sizemaximum', title=string_concat(_('operation'), ' - ', _('size maximum')), initially_hidden=True),
    GridFieldInteger('operationplan__operation__priority', title=string_concat(_('operation'), ' - ', _('priority')), initially_hidden=True),
    GridFieldDateTime('operationplan__operation__effective_start', title=string_concat(_('operation'), ' - ', _('effective start')), initially_hidden=True),
    GridFieldDateTime('operationplan__operation__effective_end', title=string_concat(_('operation'), ' - ', _('effective end')), initially_hidden=True),
    GridFieldCurrency('operationplan__operation__cost', title=string_concat(_('operation'), ' - ', _('cost')), initially_hidden=True),
    GridFieldText('operationplan__operation__search', title=string_concat(_('operation'), ' - ', _('search mode')), initially_hidden=True),
    GridFieldText('operationplan__operation__source', title=string_concat(_('operation'), ' - ', _('source')), initially_hidden=True),
    GridFieldLastModified('operationplan__operation__lastmodified', title=string_concat(_('operation'), ' - ', _('last modified')), initially_hidden=True),
    GridFieldDateTime('flowdate', title=_('date'), editable=False, extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"'),
    GridFieldNumber('quantity', title=_('quantity'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldNumber('onhand', title=_('expected onhand'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldText('operationplan__status', title=_('status'), editable=False, field_name='operationplan__status'),
    GridFieldNumber('operationplan__criticality', title=_('criticality'), field_name='operationplan__criticality', editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"'),
    GridFieldDuration('operationplan__delay', title=_('delay'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"'),
    GridFieldNumber('operationplan__quantity', title=_('operationplan quantity'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldText('pegging', title=_('demands'), formatter='demanddetail', extra='"role":"input/demand"', width=300, editable=False, sortable=False),
    )
