#
# Copyright (C) 2007 by Johan De Taeye
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
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.db import connection
from django.utils.translation import ugettext_lazy as _

from input.models import Forecast, Plan
from utils.db import *
from utils.report import *


class OverviewReport(TableReport):
  '''
  A report allowing easy editing of forecast numbers.
  '''
  template = 'output/forecast.html'
  title = _('Forecast Report')
  basequeryset = Forecast.objects.all()
  model = Forecast
  rows = (
    ('forecast',{
      'filter': FilterText(field='name'),
      'order_by': 'name',
      'title': _('forecast')}),
    ('item',{
      'filter': FilterText(field='item__name'),
      'title': _('item')
      }),
    ('customer',{
      'filter': FilterText(field='customer__name'),
      'title': _('customer')
      }),
    )
  crosses = (
    ('total',{'title': _('total forecast'), 'editable': lambda req: req.user.has_perm('input.change_forecastdemand'),}),
    ('orders',{'title': _('orders')}),
    ('net',{'title': _('net forecast')}),
    ('planned',{'title': _('planned net forecast')}),
    )
  columns = (
    ('bucket',{'title': _('bucket')}),
    )
  javascript_imports = [ "/static/prototype.js", ]

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
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
               select %s as bucket, %s_start as startdate, %s_end as enddate
               from dates
               where day_start >= '%s' and day_start < '%s'
               group by %s, %s_start, %s_end
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
        -- Grouping
        group by x.name, x.item_id, x.customer_id,
               x.bucket, x.startdate, x.enddate
        ) y
        -- Planned quantity
        left join out_demand
        on y.name = out_demand.demand
        and y.startdate <= out_demand.plandatetime
        and y.enddate > out_demand.plandatetime
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
         basesql,connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
         connection.ops.quote_name(bucket),bucket,bucket,sortsql)
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
