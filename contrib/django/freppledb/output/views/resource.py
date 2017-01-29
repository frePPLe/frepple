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
from django.utils.text import capfirst

from freppledb.boot import getAttributeFields
from freppledb.input.models import Resource, Location, OperationPlanResource, Operation
from freppledb.common.models import Parameter
from freppledb.common.report import GridReport, GridPivot, GridFieldCurrency,\
  GridFieldDuration
from freppledb.common.report import GridFieldText, GridFieldNumber, GridFieldDateTime, GridFieldBool, GridFieldInteger


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
    GridFieldText('maximum_calendar', title=_('maximum calendar'), editable=False, field_name='maximum_calendar', formatter='detail', extra='"role":"input/calendar"', initially_hidden=True),
    GridFieldCurrency('cost', title=_('cost'), editable=False, field_name='cost', initially_hidden=True),
    GridFieldDuration('maxearly', title=_('maxearly'), editable=False, field_name='maxearly', initially_hidden=True),
    GridFieldText('setupmatrix', title=_('setupmatrix'), editable=False, field_name='setupmatrix', formatter='detail', extra='"role":"input/setupmatrix"', initially_hidden=True),
    GridFieldText('setup', title=_('setup'), editable=False, field_name='setup', initially_hidden=True),
    GridFieldText('location__name', title=_('location'), editable=False, field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('location__description', title=_('description'), editable=False, field_name='location__description', initially_hidden=True),
    GridFieldText('location__category', title=_('category'), editable=False, field_name='location__category', initially_hidden=True),
    GridFieldText('location__subcategory', title=_('subcategory'), editable=False, field_name='location__subcategory', initially_hidden=True),
    GridFieldText('location__available', title=_('available'), editable=False, field_name='location__available', formatter='detail', extra='"role":"input/calendar"', initially_hidden=True),
    GridFieldText('avgutil', title=_('utilization %'), field_name='util', formatter='percentage', editable=False, width=100, align='center', search=False),
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
        'title': capfirst(force_text(Resource._meta.verbose_name) + " " + args[0]),
        'post_title': ': ' + capfirst(force_text(_('plan'))),
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
    except:
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
        coalesce(max(plan_summary.avg_util),0) as avgutil,
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
      -- Include child resources
      inner join %s res2
      on res2.lft between res.lft and res.rght
      -- Utilization info
      left join out_resourceplan
      on res2.name = out_resourceplan.resource
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
      on res2.name = plan_summary.resource
      -- Grouping and sorting
      group by res.name, res.description, res.category, res.subcategory,
        res.type, res.maximum, res.maximum_calendar_id, res.cost, res.maxearly,
        res.setupmatrix_id, res.setup, location.name, location.description, 
        location.category, location.subcategory, location.available_id, 
        %s d.bucket, d.startdate
      order by %s, d.startdate
      ''' % (
        reportclass.attr_sql, units[0], units[0], units[0], units[0],
        basesql, request.report_bucket, request.report_startdate,
        request.report_enddate,
        connections[basequery.db].ops.quote_name('resource'),
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


class DetailReport(GridReport):
  '''
  A list report to show OperationPlanResources.
  '''
  template = 'output/loadplan.html'
  title = _("Resource detail report")
  model = OperationPlanResource
  permissions = (("view_resource_report", "Can view resource report"),)
  frozenColumns = 0
  editable = False
  multiselect = False
  help_url = 'user-guide/user-interface/plan-analysis/resource-detail-report.html'

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    if args and args[0]:
      base = OperationPlanResource.objects.filter(resource__exact=args[0])
    else:
      base = OperationPlanResource.objects
    return base.select_related().extra(select={
      'pegging': "(select string_agg(value || ' : ' || key, ', ') from (select key, value from json_each_text(plan) order by key desc) peg)"
      })
    
  @classmethod
  def initialize(reportclass, request):
    if reportclass._attributes_added != 2:
      reportclass._attributes_added = 2
      # Adding custom operation attributes
      for f in getAttributeFields(Operation, related_name_prefix="operation"):
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
    return {'active_tab': 'plandetail'}

  rows = (
    GridFieldInteger('id', title='internal id', key=True, editable=False, hidden=True),
    GridFieldText('resource', title=_('resource'), editable=False, formatter='detail', extra='"role":"input/resource"'),
    GridFieldInteger('operationplan__id', title=_('id'), editable=False),    
    GridFieldText('operationplan__reference', title=_('reference'), editable=False),
    GridFieldText('operationplan__type', title=_('type'), field_name='operationplan__type', editable=False),
    GridFieldText('operationplan__operation', title=_('operation'), editable=False, formatter='detail', extra='"role":"input/operation"'),
    GridFieldDateTime('operationplan__startdate', title=_('start date'), editable=False),
    GridFieldDateTime('operationplan__enddate', title=_('end date'), editable=False),
    GridFieldNumber('operationplan__quantity', title=_('operationplan quantity'), editable=False),
    GridFieldText('pegging', title=_('demand quantity'), formatter='demanddetail', extra='"role":"input/demand"', width=300, editable=False, sortable=False),
    GridFieldNumber('quantity', title=_('load quantity'), editable=False),
    GridFieldNumber('operationplan__criticality', title=_('criticality'), editable=False),
    GridFieldBool('operationplan__status', title=_('status'), editable=False),
    GridFieldText('setup', title=_('setup'), editable=False),
    )
