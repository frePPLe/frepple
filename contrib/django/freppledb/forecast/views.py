#
# Copyright (C) 2012 by Johan De Taeye, frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.  
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code 
# or in the form of compiled binaries.
#

# file : $URL: file:///C:/Users/Johan/Dropbox/SVNrepository/frepple/addon/contrib/django/freppledb_extra/views/forecast.py $
# revision : $LastChangedRevision: 449 $  $LastChangedBy: Johan $
# date : $LastChangedDate: 2012-12-28 18:59:56 +0100 (Fri, 28 Dec 2012) $

from datetime import datetime
import json

from django.db import connections, transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.encoding import force_unicode
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.conf import settings

from freppledb_extra.models import Forecast
from freppledb.common.db import python_date, sql_datediff, sql_overlap
from freppledb.common.report import GridPivot, GridFieldText, GridFieldInteger, getBuckets
from freppledb.common.report import GridReport, GridFieldBool, GridFieldLastModified, GridFieldNumber

class ForecastList(GridReport):
  '''
  A list report to show forecasts.
  '''
  template = 'input/forecastlist.html'
  title = _("Forecast List")
  basequeryset = Forecast.objects.all()
  model = Forecast
  frozenColumns = 1

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='forecast'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='item'),
    GridFieldText('customer', title=_('customer'), field_name='customer__name', formatter='customer'),
    GridFieldText('calendar', title=_('calendar'), field_name='calendar__name', formatter='calendar'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldNumber('maxlateness', title=_('maximum lateness')),
    GridFieldNumber('minshipment', title=_('minimum shipment')),
    GridFieldBool('discrete', title=_('discrete')),
    GridFieldLastModified('lastmodified'),
    )
    

class OverviewReport(GridPivot):
  '''
  A report allowing easy editing of forecast numbers.
  '''
  template = 'output/forecast.html'
  title = _('Forecast Report')
  basequeryset = Forecast.objects.all()
  model = Forecast
  editable = True
  rows = (
    GridFieldText('forecast', title=_('forecast'), key=True, field_name='name', formatter='forecast', editable=False),
    GridFieldText('item', title=_('item'), key=True, field_name='item__name', formatter='item', editable=False),
    GridFieldText('customer', title=_('customer'), key=True, field_name='customer__name', formatter='customer', editable=False),
    GridFieldText(None, width="(5*numbuckets<200 ? 5*numbuckets : 200)", extra='formatter:graph', editable=False),
    )
  crosses = (
    ('total',{'title': _('total forecast'), 'editable': lambda req: req.user.has_perm('input.change_forecastdemand'),}),
    ('orders',{'title': _('orders')}),
    ('net',{'title': _('net forecast')}),
    ('planned',{'title': _('planned net forecast')}),
    )

    
  @classmethod
  def parseJSONupload(reportclass, request): 
    # Check permissions
    if not request.user.has_perm('input.change_forecastdemand'):
      return HttpResponseForbidden(_('Permission denied'))

    # Loop over the data records 
    transaction.enter_transaction_management(using=request.database)
    transaction.managed(True, using=request.database)
    resp = HttpResponse()
    ok = True
    try:          
      for rec in json.JSONDecoder().decode(request.read()):
        try:
          # Find the forecast
          start = datetime.strptime(rec['startdate'],'%Y-%m-%d')
          end = datetime.strptime(rec['enddate'],'%Y-%m-%d')
          fcst = Forecast.objects.using(request.database).get(name = rec['id'])
          # Update the forecast
          fcst.setTotal(start,end,rec['value'])      
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
  def extra_context(reportclass, request, *args, **kwargs):
    if args and args[0]:
      return {
        'title': capfirst(force_unicode(Forecast._meta.verbose_name) + " " + args[0]),
        'post_title': ': ' + capfirst(force_unicode(_('plan'))),
        }      
    else:
      return {}
                
  @staticmethod
  def query(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)
    # Execute the query
    cursor = connections[request.database].cursor()
    query = '''
        select y.name as row1, y.item_id as row2, y.customer_id as row3,
               y.bucket as col1, y.startdate as col2, y.enddate as col3,
               min(y.total),
               min(y.consumed),
               min(y.net),
               coalesce(sum(out_demand.planquantity),0)
        from (
          select x.name as name, x.item_id as item_id, x.customer_id as customer_id,
                 x.bucket as bucket, x.startdate as startdate, x.enddate as enddate,
                 coalesce(sum(out_forecast.consumed * %s / %s),0) as consumed,
                 coalesce(sum(out_forecast.net * %s / %s),0) as net,
                 min(x.total) as total
        from (
          select fcst.name as name, fcst.item_id as item_id, fcst.customer_id as customer_id,
                 d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
                 coalesce(sum(forecastdemand.quantity * %s / %s),0) as total
          from (%s) fcst
          -- Multiply with buckets
          cross join (
             select name as bucket, startdate, enddate
             from common_bucketdetail
             where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
             ) d
          -- Forecasted quantity
          left join forecastdemand
          on fcst.name = forecastdemand.forecast_id
          and forecastdemand.enddate >= d.startdate
          and forecastdemand.startdate <= d.enddate
          -- Grouping
          group by fcst.name, fcst.item_id, fcst.customer_id,
                 d.bucket, d.startdate, d.enddate
          ) x
        -- Net and consumed quantity
        left join out_forecast
        on x.name = out_forecast.forecast
        and out_forecast.enddate >= x.startdate
        and out_forecast.startdate <= x.enddate
        and out_forecast.enddate >= '%s'
        and out_forecast.enddate < '%s'
        -- Grouping
        group by x.name, x.item_id, x.customer_id,
               x.bucket, x.startdate, x.enddate
        ) y
        -- Planned quantity
        left join out_demand
        on out_demand.demand like y.name || ' - %%%%'
        and y.startdate <= out_demand.plandate
        and y.enddate > out_demand.plandate
        and out_demand.plandate >= '%s'
        and out_demand.plandate < '%s'
        -- Ordering and grouping
        group by y.name, y.item_id, y.customer_id,
           y.bucket, y.startdate, y.enddate
        order by %s, y.startdate
        ''' % (sql_overlap('out_forecast.startdate','out_forecast.enddate','x.startdate','x.enddate'),
         sql_datediff('out_forecast.enddate','out_forecast.startdate'),
         sql_overlap('out_forecast.startdate','out_forecast.enddate','x.startdate','x.enddate'),
         sql_datediff('out_forecast.enddate','out_forecast.startdate'),
         sql_overlap('forecastdemand.startdate','forecastdemand.enddate','d.startdate','d.enddate'),
         sql_datediff('forecastdemand.enddate','forecastdemand.startdate'),
         basesql,bucket,startdate,enddate,startdate,enddate,startdate,enddate,sortsql)
    cursor.execute(query, baseparams)

    # Build the python result
    for row in cursor.fetchall():
      yield {
        'forecast': row[0],
        'item': row[1],
        'customer': row[2],
        'bucket': row[3],
        'startdate': python_date(row[4]),
        'enddate': python_date(row[5]),
        'total': row[6],
        'orders': row[7],
        'net': row[8],
        'planned': row[9],
        }
        
        
@staff_member_required
def GraphData(request, entity):
  basequery = Forecast.objects.filter(pk__exact=entity)
  (bucket,start,end,bucketlist) = getBuckets(request)
  total = []
  net = []
  orders = []
  planned = []
  for x in OverviewReport.query(request, basequery, bucket, start, end):
    total.append(x['total'])
    net.append(x['net'])
    orders.append(x['orders'])
    planned.append(x['planned'])
  context = { 
    'buckets': bucketlist, 
    'total': total, 
    'net': net, 
    'orders': orders, 
    'planned': planned,
    'axis_nth': len(bucketlist) / 20 + 1,
    }
  return HttpResponse(
    loader.render_to_string("output/forecast.xml", context, context_instance=RequestContext(request)),
    mimetype='application/xml; charset=%s' % settings.DEFAULT_CHARSET
    )
    
