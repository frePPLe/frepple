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

from django.db import connections
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst

from freppledb.input.models import Resource
from freppledb.output.models import LoadPlan
from freppledb.common.models import Parameter
from freppledb.common.db import python_date, sql_max
from freppledb.common.report import GridReport, GridPivot
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
  rows = (
    GridFieldText('resource', title=_('resource'), key=True, field_name='name', formatter='resource', editable=False),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='location', editable=False),
    GridFieldText('avgutil', title=_('utilization %'), field_name='util', formatter='percentage', editable=False, width=100, align='center', search=False),
    )
  crosses = (
    ('available', {
       'title': _('available'),
       'editable': lambda req: req.user.has_perm('input.change_resource')
       }),
    ('unavailable', {'title': _('unavailable')}),
    ('setup', {'title': _('setup')}),
    ('load', {'title': _('load')}),
    ('utilization', {'title': _('utilization %')}),
    )

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
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

  @staticmethod
  def query(request, basequery, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)

    # Get the time units
    units = OverviewReport.getUnits(request)

    # Assure the item hierarchy is up to date
    Resource.rebuildHierarchy(database=basequery.db)

    # Execute the query
    cursor = connections[request.database].cursor()
    query = '''
      select res.name as row1, res.location_id as row2,
             coalesce(max(plan_summary.avg_util),0) as avgutil,
             d.bucket as col1, d.startdate as col2,
             coalesce(sum(out_resourceplan.available),0) * (case when res.type = 'buckets' then 1 else %f end) as available,
             coalesce(sum(out_resourceplan.unavailable),0) * (case when res.type = 'buckets' then 1 else %f end) as unavailable,
             coalesce(sum(out_resourceplan.load),0) * (case when res.type = 'buckets' then 1 else %f end) as loading,
             coalesce(sum(out_resourceplan.setup),0) * (case when res.type = 'buckets' then 1 else %f end) as setup
      from (%s) res
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
      on res2.name = out_resourceplan.theresource
      and d.startdate <= out_resourceplan.startdate
      and d.enddate > out_resourceplan.startdate
      and out_resourceplan.startdate >= '%s'
      and out_resourceplan.startdate < '%s'
      -- Average utilization info
      left join (
                select
                  theresource,
                  ( coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0) )
                   * 100.0 / coalesce(%s,1) as avg_util
                from out_resourceplan
                where out_resourceplan.startdate >= '%s'
                and out_resourceplan.startdate < '%s'
                group by theresource
                ) plan_summary
      on res2.name = plan_summary.theresource
      -- Grouping and sorting
      group by res.name, res.location_id, res.type, d.bucket, d.startdate
      order by %s, d.startdate
      ''' % (
        units[0], units[0], units[0], units[0],
        basesql, request.report_bucket, request.report_startdate,
        request.report_enddate,
        connections[basequery.db].ops.quote_name('resource'),
        request.report_startdate, request.report_enddate,
        sql_max('sum(out_resourceplan.available)', '0.0001'),
        request.report_startdate, request.report_enddate, sortsql
      )
    cursor.execute(query, baseparams)

    # Build the python result
    for row in cursor.fetchall():
      if row[5] != 0:
        util = row[7] * 100 / row[5]
      else:
        util = 0
      yield {
        'resource': row[0],
        'location': row[1],
        'avgutil': round(row[2], 2),
        'bucket': row[3],
        'startdate': python_date(row[4]),
        'available': round(row[5], 1),
        'unavailable': round(row[6], 1),
        'load': round(row[7], 1),
        'setup': round(row[8], 1),
        'utilization': round(util, 2)
        }


class DetailReport(GridReport):
  '''
  A list report to show loadplans.
  '''
  template = 'output/loadplan.html'
  title = _("Resource detail report")
  model = LoadPlan
  permissions = (("view_resource_report", "Can view resource report"),)
  frozenColumns = 0
  editable = False
  multiselect = False

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    if args and args[0]:
      return LoadPlan.objects.filter(theresource__exact=args[0]).select_related() \
        .extra(select={'operation_in': "select name from operation where out_operationplan.operation = operation.name"})
    else:
      return LoadPlan.objects.select_related() \
        .extra(select={'operation_in': "select name from operation where out_operationplan.operation = operation.name"})

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    return {'active_tab': 'plandetail'}

  rows = (
    GridFieldText('theresource', title=_('resource'), key=True, formatter='resource', editable=False),
    GridFieldText('operationplan__operation', title=_('operation'), formatter='operation', editable=False),
    GridFieldDateTime('startdate', title=_('start date'), editable=False),
    GridFieldDateTime('enddate', title=_('end date'), editable=False),
    GridFieldNumber('operationplan__quantity', title=_('operationplan quantity'), editable=False),
    GridFieldNumber('quantity', title=_('load quantity'), editable=False),
    GridFieldNumber('operationplan__criticality', title=_('criticality'), editable=False),
    GridFieldBool('operationplan__locked', title=_('locked'), editable=False),
    GridFieldNumber('operationplan__unavailable', title=_('unavailable'), editable=False),
    GridFieldInteger('operationplan', title=_('operationplan'), editable=False),
    GridFieldText('setup', title=_('setup'), editable=False),
    )
