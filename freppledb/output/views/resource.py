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
from freppledb.input.models import Resource, Location, OperationPlanResource, Operation
from freppledb.input.views import OperationPlanMixin
from freppledb.common.models import Parameter
from freppledb.common.report import GridReport, GridPivot, GridFieldCurrency
from freppledb.common.report import GridFieldLastModified, GridFieldDuration
from freppledb.common.report import GridFieldDateTime, GridFieldInteger
from freppledb.common.report import GridFieldNumber, GridFieldText, GridFieldBool


class OverviewReport(GridPivot):
  '''
  A report showing the loading of each resource.
  '''
  template = 'output/resource.html'
  title = _('Resource report')
  basequeryset = Resource.objects.all()
  model = Resource
  permissions = (("view_resource_report", "Can view resource report"),)
  editable = False
  help_url = 'user-guide/user-interface/plan-analysis/resource-report.html'

  rows = (
    GridFieldText('resource', title=_('resource'), key=True, editable=False, field_name='name', formatter='detail', extra='"role":"input/resource"'),
    GridFieldText('description', title=_('description'), editable=False, field_name='description', initially_hidden=True),
    GridFieldText('category', title=_('category'), editable=False, field_name='category', initially_hidden=True),
    GridFieldText('subcategory', title=_('subcategory'), editable=False, field_name='subcategory', initially_hidden=True),
    GridFieldText('type', title=_('type'), editable=False, field_name='type', initially_hidden=True),
    GridFieldNumber('maximum', title=_('maximum'), editable=False, field_name='maximum', initially_hidden=True),
    GridFieldText('maximum_calendar', title=_('maximum calendar'), editable=False, field_name='maximum_calendar__name', formatter='detail', extra='"role":"input/calendar"', initially_hidden=True),
    GridFieldCurrency('cost', title=_('cost'), editable=False, field_name='cost', initially_hidden=True),
    GridFieldDuration('maxearly', title=_('maxearly'), editable=False, field_name='maxearly', initially_hidden=True),
    GridFieldText('setupmatrix', title=_('setupmatrix'), editable=False, field_name='setupmatrix__name', formatter='detail', extra='"role":"input/setupmatrix"', initially_hidden=True),
    GridFieldText('setup', title=_('setup'), editable=False, field_name='setup', initially_hidden=True),
    GridFieldText('location__name', title=_('location'), editable=False, field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('location__description', title=string_concat(_('location'), ' - ', _('description')), editable=False, initially_hidden=True),
    GridFieldText('location__category', title=string_concat(_('location'), ' - ', _('category')), editable=False, initially_hidden=True),
    GridFieldText('location__subcategory', title=string_concat(_('location'), ' - ', _('subcategory')), editable=False, initially_hidden=True),
    GridFieldText('location__available', title=string_concat(_('location'), ' - ', _('available')), editable=False, field_name='location__available__name', formatter='detail', extra='"role":"input/calendar"', initially_hidden=True),
    GridFieldText('avgutil', title=_('utilization %'), field_name='util', formatter='percentage', editable=False, width=100, align='center', search=False),
    GridFieldText('available_calendar', title=_('available calendar'), editable=False, field_name='available__name', formatter='detail', extra='"role":"input/calendar"', initially_hidden=True),
    )
  crosses = (
    ('available', {
       'title': _('available')
       }),
    ('unavailable', {'title': _('unavailable')}),
    ('setup', {'title': _('setup')}),
    ('load', {'title': _('load')}),
    ('utilization', {'title': _('utilization %')}),
    )

  @classmethod
  def initialize(reportclass, request):
    if reportclass._attributes_added != 2:
      reportclass._attributes_added = 2
      reportclass.attr_sql = ''
      # Adding custom resource attributes
      for f in getAttributeFields(Resource, initially_hidden=True):
        f.editable = False
        reportclass.rows += (f,)
        reportclass.attr_sql += 'res.%s, ' % f.name.split('__')[-1]
      # Adding custom location attributes
      for f in getAttributeFields(Location, related_name_prefix="location", initially_hidden=True):
        f.editable = False
        reportclass.rows += (f,)
        reportclass.attr_sql += 'location.%s, ' % f.name.split('__')[-1]

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plan'
      return {
        'units': reportclass.getUnits(request),
        'title': force_text(Resource._meta.verbose_name) + " " + args[0],
        'post_title': _('plan'),
        }
    else:
      return {'units': reportclass.getUnits(request)}

  @classmethod
  def getUnits(reportclass, request):
    try:
      units = Parameter.objects.using(request.database).get(name="loading_time_units")
      if units.value == 'hours':
        return (1.0, _('hours'))
      elif units.value == 'weeks':
        return (1.0 / 168.0, _('weeks'))
      else:
        return (1.0 / 24.0, _('days'))
    except Exception:
      return (1.0 / 24.0, _('days'))

  @classmethod
  def query(reportclass, request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)

    # Get the time units
    units = OverviewReport.getUnits(request)

    # Assure the item hierarchy is up to date
    Resource.rebuildHierarchy(database=basequery.db)

    # Execute the query
    cursor = connections[request.database].cursor()
    query = '''
      select res.name, res.description, res.category, res.subcategory,
        res.type, res.maximum, res.maximum_calendar_id, res.cost, res.maxearly,
        res.setupmatrix_id, res.setup, location.name, location.description,
        location.category, location.subcategory, location.available_id,
        coalesce(max(plan_summary.avg_util),0) as avgutil, res.available_id available_calendar, 
        %s
        d.bucket as col1, d.startdate as col2,
        coalesce(sum(out_resourceplan.available),0) * (case when res.type = 'buckets' then 1 else %f end) as available,
        coalesce(sum(out_resourceplan.unavailable),0) * (case when res.type = 'buckets' then 1 else %f end) as unavailable,
        coalesce(sum(out_resourceplan.load),0) * (case when res.type = 'buckets' then 1 else %f end) as loading,
        coalesce(sum(out_resourceplan.setup),0) * (case when res.type = 'buckets' then 1 else %f end) as setup
      from (%s) res
      left outer join location
        on res.location_id = location.name
      -- Multiply with buckets
      cross join (
                   select name as bucket, startdate, enddate
                   from common_bucketdetail
                   where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
                   ) d
      -- Utilization info
      left join out_resourceplan
      on res.name = out_resourceplan.resource
      and d.startdate <= out_resourceplan.startdate
      and d.enddate > out_resourceplan.startdate
      and out_resourceplan.startdate >= '%s'
      and out_resourceplan.startdate < '%s'
      -- Average utilization info
      left join (
          select
            resource,
            ( coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0) )
             * 100.0 / coalesce(greatest(sum(out_resourceplan.available), 0.0001),1) as avg_util
          from out_resourceplan
          where out_resourceplan.startdate >= '%s'
          and out_resourceplan.startdate < '%s'
          group by resource
          ) plan_summary
      on res.name = plan_summary.resource
      -- Grouping and sorting
      group by res.name, res.description, res.category, res.subcategory,
        res.type, res.maximum, res.maximum_calendar_id, res.available_id, res.cost, res.maxearly,
        res.setupmatrix_id, res.setup, location.name, location.description,
        location.category, location.subcategory, location.available_id,
        %s d.bucket, d.startdate
      order by %s, d.startdate
      ''' % (
        reportclass.attr_sql, units[0], units[0], units[0], units[0],
        basesql, request.report_bucket, request.report_startdate,
        request.report_enddate,
        request.report_startdate, request.report_enddate,
        request.report_startdate, request.report_enddate,
        reportclass.attr_sql, sortsql
      )
    cursor.execute(query, baseparams)

    # Build the python result
    for row in cursor.fetchall():
      numfields = len(row)
      if row[numfields-4] != 0:
        util = row[numfields-2] * 100 / row[numfields-4]
      else:
        util = 0
      result = {
        'resource': row[0], 'description': row[1], 'category': row[2],
        'subcategory': row[3], 'type': row[4], 'maximum': row[5],
        'maximum_calendar': row[6], 'cost': row[7], 'maxearly': row[8],
        'setupmatrix': row[9], 'setup': row[10],
        'location__name': row[11], 'location__description': row[12],
        'location__category': row[13], 'location__subcategory': row[14],
        'location__available': row[15],
        'avgutil': round(row[16], 2),
        'available_calendar': row[17],
        'bucket': row[numfields-6],
        'startdate': row[numfields-5].date(),
        'available': round(row[numfields-4], 1),
        'unavailable': round(row[numfields-3], 1),
        'load': round(row[numfields-2], 1),
        'setup': round(row[numfields-1], 1),
        'utilization': round(util, 2)
        }
      idx = 17
      for f in getAttributeFields(Resource):
        result[f.field_name] = row[idx]
        idx += 1
      for f in getAttributeFields(Location):
        result[f.field_name] = row[idx]
        idx += 1
      yield result


class DetailReport(OperationPlanMixin, GridReport):
  '''
  A list report to show OperationPlanResources.
  '''
  template = 'input/operationplanreport.html'
  title = _("Resource detail report")
  model = OperationPlanResource
  permissions = (("view_resource_report", "Can view resource report"),)
  frozenColumns = 3
  editable = False
  multiselect = False
  height = 250
  help_url = 'user-guide/user-interface/plan-analysis/resource-detail-report.html'

  @ classmethod
  def basequeryset(reportclass, request, *args, **kwargs):
    if args and args[0]:
      try:
        res = Resource.objects.using(request.database).get(name__exact=args[0])
        base = OperationPlanResource.objects.filter(resource__lft__gte=res.lft, resource__rght__lte=res.rght)
      except OperationPlanResource.DoesNotExist:
        base = OperationPlanResource.objects.filter(resource__exact=args[0])
    else:
      base = OperationPlanResource.objects
    base = reportclass.operationplanExtraBasequery(base, request)
    return base.select_related().extra(select={
      'opplan_duration': "(operationplan.enddate - operationplan.startdate)",
      'opplan_net_duration': "(operationplan.enddate - operationplan.startdate - coalesce((operationplan.plan->>'unavailable')::int * interval '1 second', interval '0 second'))",
      'setup_end': "(operationplan.plan->>'setupend')",
      'setup_duration': "(operationplan.plan->>'setup')",
      'feasible': "coalesce((operationplan.plan->>'feasible')::boolean, true)"
      })

  @classmethod
  def initialize(reportclass, request):
    if reportclass._attributes_added != 2:
      reportclass._attributes_added = 2
      # Adding custom operation attributes
      for f in getAttributeFields(Operation, related_name_prefix="operationplan__operation"):
        f.editable = False
        reportclass.rows += (f,)
      # Adding custom resource attributes
      for f in getAttributeFields(Resource, related_name_prefix="resource"):
        f.editable = False
        reportclass.rows += (f,)

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      request.session['lasttab'] = 'plandetail'
      return {
        'active_tab': 'plandetail',
        'model': Resource,
        'title': force_text(Resource._meta.verbose_name) + " " + args[0],
        'post_title': _('plan detail')
        }
    else:
      return {'active_tab': 'plandetail', 'model': None}

  rows = (
    GridFieldInteger('id', title='internal id', key=True, editable=False, hidden=True),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', editable=False, formatter='detail', extra='"role":"input/resource"'),
    GridFieldInteger('operationplan__id', title=_('identifier'), editable=False),
    GridFieldText('operationplan__reference', title=_('reference'), editable=False),
    GridFieldText('operationplan__color', title=_('inventory status'), formatter='color', width='125', editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"'),
    GridFieldText('operationplan__operation__item', title=_('item'), editable=False, formatter='detail', extra='"role":"input/item"'),
    GridFieldText('operationplan__operation__location', title=_('location'), editable=False, formatter='detail', extra='"role":"input/location"'),
    GridFieldText('operationplan__operation__name', title=_('operation'), editable=False, formatter='detail', extra='"role":"input/operation"'),
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
    GridFieldDateTime('operationplan__startdate', title=_('start date'), editable=False, extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"'),
    GridFieldDateTime('operationplan__enddate', title=_('end date'), editable=False, extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"'),
    GridFieldDuration('opplan_duration', title=_('duration'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldDuration('opplan_net_duration', title=_('net duration'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldNumber('operationplan__quantity', title=_('quantity'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldText('operationplan__status', title=_('status'), editable=False),
    GridFieldNumber('operationplan__criticality', title=_('criticality'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"'),
    GridFieldDuration('operationplan__delay', title=_('delay'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"'),
    GridFieldText('demand', title=_('demands'), formatter='demanddetail', extra='"role":"input/demand"', width=300, editable=False, sortable=False),
    GridFieldText('operationplan__type', title=_('type'), field_name='operationplan__type', editable=False),
    GridFieldNumber('quantity', title=_('load quantity'), editable=False, extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"'),
    GridFieldText('setup', title=_('setup'), editable=False, initially_hidden=True),
    GridFieldDateTime('setup_end', title=_('setup end date'), editable=False, initially_hidden=True),
    GridFieldDuration('setup_duration', title=_('setup duration'), editable=False, initially_hidden=True),
    GridFieldBool('feasible', title=_('feasible'), editable=False, initially_hidden=True, search=False),
    # Optional fields referencing the item
    GridFieldText(
      'operationplan__operation__item__description', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('description'))
      ),
    GridFieldText(
      'operationplan__operation__item__category', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('category'))
      ),
    GridFieldText(
      'operationplan__operation__item__subcategory', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'operationplan__operation__item__owner', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('owner')),
      field_name='operationplan__operation__item__owner__name'
      ),
    GridFieldText(
      'operationplan__operation__item__source', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'operationplan__operation__item__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('item'), ' - ', _('last modified')),
      ),
    # Optional fields referencing the operation location
    GridFieldText(
      'operationplan__operation__location__description',
      initially_hidden=True, editable=False,
      title=string_concat(_('location'), ' - ', _('description'))
      ),
    GridFieldText(
      'operationplan__operation__location__category',
      title=string_concat(_('location'), ' - ', _('category')),
      initially_hidden=True, editable=False
      ),
    GridFieldText(
      'operationplan__operation__location__subcategory',
      title=string_concat(_('location'), ' - ', _('subcategory')),
      initially_hidden=True, editable=False
      ),
    GridFieldText(
      'operationplan__operation__location__available', editable=False,
      title=string_concat(_('location'), ' - ', _('available')),
      initially_hidden=True, field_name='operationplan__operation__location__available__name', formatter='detail',
      extra='"role":"input/calendar"'
      ),
    GridFieldText(
      'operationplan__operation__location__owner', initially_hidden=True,
      title=string_concat(_('location'), ' - ', _('owner')),
      field_name='operationplan__operation__location__owner__name', formatter='detail',
      extra='"role":"input/location"', editable=False
      ),
    GridFieldText(
      'operationplan__operation__location__source', initially_hidden=True, editable=False,
      title=string_concat(_('location'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'operationplan__operation__location__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('location'), ' - ', _('last modified'))
      ),
    # Optional fields referencing the resource
    GridFieldText(
      'resource__description', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('description'))
      ),
    GridFieldText(
      'resource__category', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('category'))
      ),
    GridFieldText(
      'resource__subcategory', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'resource__type', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('type'))
      ),
    GridFieldNumber(
      'resource__maximum', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('maximum'))
      ),
    GridFieldText(
      'resource__maximum_calendar', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('maximum calendar')),
      field_name='resource__maximum_calendar__name',
      formatter='detail', extra='"role":"input/calendar"'
      ),
    GridFieldCurrency(
      'resource__cost', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('cost'))
      ),
    GridFieldDuration(
      'resource__maxearly', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('maxearly'))
      ),
    GridFieldText(
      'resource__setupmatrix', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('setupmatrix')),
      field_name='resource__setupmatrix__name',
      formatter='detail', extra='"role":"input/setupmatrix"'
      ),
    GridFieldText(
      'resource__setup', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('setup'))
      ),
    GridFieldText(
      'resource_location', editable=False, initially_hidden=True,
      title=string_concat(_('resource'), ' - ', _('location')),
      field_name='resource__location__name',
      formatter='detail', extra='"role":"input/location"'
      ),
    # Optional fields referencing the resource location
    GridFieldText(
      'resource__location__description', initially_hidden=True, editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('description'))
      ),
    GridFieldText(
      'resource__location__category', initially_hidden=True, editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('category'))
      ),
    GridFieldText(
      'resource__location__subcategory', initially_hidden=True, editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('subcategory'))
      ),
    GridFieldText(
      'resource__location__available', initially_hidden=True, editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('available')),
      field_name='resource__location__available__name', formatter='detail',
      extra='"role":"input/calendar"'
      ),
    GridFieldText(
      'resource__location__owner', extra='"role":"input/location"', editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('owner')),
      initially_hidden=True, field_name='resource__location__owner__name', formatter='detail'
      ),
    GridFieldText(
      'resource__location__source', initially_hidden=True, editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('source'))
      ),
    GridFieldLastModified(
      'resource__location__lastmodified', initially_hidden=True, editable=False,
      title=string_concat(_('resource'), ' - ', _('location'), ' - ', _('last modified'))
      ),
    )
