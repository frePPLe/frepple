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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from datetime import datetime

from django.db import connections, transaction
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden

from freppledb.input.models import Resource
from freppledb.output.models import LoadPlan
from freppledb.common.models import Parameter
from freppledb.common.db import sql_overlap3, python_date
from freppledb.common.report import getBuckets, GridReport, GridPivot
from freppledb.common.report import GridFieldText, GridFieldNumber, GridFieldDateTime, GridFieldBool, GridFieldInteger

  
class OverviewReport(GridPivot):
  '''
  A report showing the loading of each resource.
  '''
  template = 'output/resource.html'
  title = _('Resource report')
  basequeryset = Resource.objects.all()
  model = Resource
  editable = True
  rows = (
    GridFieldText('resource', title=_('resource'), key=True, field_name='name', formatter='resource', editable=False),
    GridFieldText('location', title=_('location'), key=True, field_name='location__name', formatter='location', editable=False),
    )
  crosses = (
    ('available',{'title': _('available'), 'editable': lambda req: req.user.has_perm('input.change_resource'),}),
    ('unavailable',{'title': _('unavailable')}),
    ('setup',{'title': _('setup')}),
    ('load',{'title': _('load')}),
    ('utilization',{'title': _('utilization %'),}),
    )
  
  @classmethod 
  def extra_context(reportclass, request):
    return {'units' : reportclass.getUnits()}
  
  @classmethod
  def parseJSONupload(reportclass, request): 
    # Check permissions
    if not request.user.has_perm('input.change_resource'):
      return HttpResponseForbidden(_('Permission denied'))

    # Loop over the data records 
    transaction.enter_transaction_management(using=request.database)
    transaction.managed(True, using=request.database)
    resp = HttpResponse()
    ok = True
    try:          
      for rec in simplejson.JSONDecoder().decode(request.read()):
        try:
          # Find the resource
          res = Resource.objects.using(request.database).get(name = rec['id'])
          if not res.maximum_calendar:
            ok = False
            resp.write("%s: %s<br/>" % (escape(rec['id']), _('Resource has no maximum calendar')))
            continue
          # Update the calendar
          start = datetime.strptime(rec['startdate'],'%Y-%m-%d')
          end = datetime.strptime(rec['enddate'],'%Y-%m-%d')
          res.maximum_calendar.setvalue(
            start,
            end,
            float(rec['value']) / (end - start).days,
            user = request.user)            
        except Exception as e:
          ok = False
          resp.write(e)
          resp.write('<br/>')                          
    finally:
      transaction.commit(using=request.database)
      transaction.leave_transaction_management(using=request.database)
    if ok: resp.write("OK")
    resp.status_code = ok and 200 or 403
    return resp
  
  @classmethod
  def getUnits(reportclass):    
    try:
      units = Parameter.objects.using(request.database).get(name="loading_time_units")
      if units.value == 'hours':
        return 1.0
      elif units.value == 'weeks':
        return 1.0 / 168.0
      else:
        return 1.0 / 24.0
    except:
      return 1.0 / 24.0
    
      
  @staticmethod
  def query(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)        
        
    # Get the time units
    units = OverviewReport.getUnits()
        
    # Assure the item hierarchy is up to date
    Resource.rebuildHierarchy(database=basequery.db)
    
    # Execute the query
    # TODO available field takes the whole bucket.  Load field only considers the dates that are in the reporting interval - could be part of a bucket
    cursor = connections[request.database].cursor()
    query = '''
      select res.name as row1, res.location_id as row2,
                   d.bucket as col1, d.startdate as col2,
                   coalesce(sum(out_resourceplan.available),0) * %f as available, 
                   coalesce(sum(out_resourceplan.unavailable),0) * %f as unavailable,
                   coalesce(sum(out_resourceplan.load),0) * %f as loading,
                   coalesce(sum(out_resourceplan.setup),0) * %f as setup
      from (%s) res
      -- Multiply with buckets
      cross join (
                   select name as bucket, startdate, enddate
                   from common_bucketdetail
                   where bucket_id = '%s' and enddate > '%s' and startdate <= '%s'
                   ) d
      -- Include child buffers
      inner join resource
      on resource.lft between res.lft and res.rght
      -- Utilization info
      left join out_resourceplan
      on resource.name = out_resourceplan.theresource
      and d.startdate <= out_resourceplan.startdate
      and d.enddate > out_resourceplan.startdate
      and out_resourceplan.startdate >= '%s'
      and out_resourceplan.startdate < '%s'
      -- Grouping and sorting
      group by res.name, res.location_id, d.bucket, d.startdate
      order by %s, d.startdate    
      ''' % ( units, units, units, units,
        basesql, bucket, startdate, enddate,
        startdate, enddate, sortsql
       )
    print query
    cursor.execute(query, baseparams)
    
    # Build the python result
    for row in cursor.fetchall():
      if row[4] != 0: util = row[6] * 100 / row[4]
      else: util = 0
      yield {
        'resource': row[0],
        'location': row[1],
        'bucket': row[2],
        'startdate': python_date(row[3]),
        'available': round(row[4],1),
        'unavailable': round(row[5],1),
        'load': round(row[6],1),
        'setup': round(row[7],1),
        'utilization': round(util,2),
        }


class DetailReport(GridReport):
  '''
  A list report to show loadplans.
  '''
  template = 'output/loadplan.html'
  title = _("Resource detail report")
  basequeryset = LoadPlan.objects.select_related() \
    .extra(select={'operation_in': "select name from operation where out_operationplan.operation = operation.name",})
  model = LoadPlan
  frozenColumns = 0
  editable = False
  
  rows = (
    GridFieldText('theresource', title=_('resource'), key=True, formatter='resource', editable=False),
    GridFieldText('operationplan__operation', title=_('operation'), formatter='operation', editable=False),
    GridFieldDateTime('startdate', title=_('start date'), editable=False),
    GridFieldDateTime('enddate', title=_('end date'), editable=False),
    GridFieldNumber('quantity', title=_('quantity'), editable=False),
    GridFieldText('setup', title=_('setup'), editable=False),
    GridFieldBool('operationplan__locked', title=_('locked'), editable=False),
    GridFieldNumber('operationplan__unavailable', title=_('unavailable'), editable=False),
    GridFieldInteger('operationplan', title=_('operationplan'), editable=False),
    )


@staff_member_required
def GraphData(request, entity):
  basequery = Resource.objects.filter(pk__exact=entity)
  (bucket,start,end,bucketlist) = getBuckets(request)
  load = []
  free = []
  overload = []
  unavailable = []
  setup = []
  for x in OverviewReport.query(request, basequery, bucket, start, end):
    if x['available'] > x['load']:
      free.append(x['available'] - x['load'])
      overload.append(0)
      load.append(x['load'])
    else:
      load.append(x['available'])
      free.append(0)
      overload.append(x['load'] - x['available'])
    unavailable.append(x['unavailable'])
    setup.append(x['setup'])
  # Get the time units
  try:
    units = Parameter.objects.using(request.database).get(name="loading_time_units")
    if units.value == 'hours':
      units = _('hours')
    elif units.value == 'weeks':
      units = _('weeks')
    else:
      units = _('days')
  except:
    units = _('days')
  context = { 
    'buckets': bucketlist, 
    'load': load, 
    'setup': setup, 
    'free': free, 
    'overload': overload, 
    'unavailable': unavailable, 
    'axis_nth': len(bucketlist) / 20 + 1,
    'units': units,
    }
  return HttpResponse(
    loader.render_to_string("output/resource.xml", context, context_instance=RequestContext(request)),
    mimetype='application/xml; charset=%s' % settings.DEFAULT_CHARSET
    )
