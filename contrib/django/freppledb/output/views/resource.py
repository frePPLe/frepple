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

from input.models import Resource, Plan
from output.models import LoadPlan
from utils.db import *
from utils.report import *


class OverviewReport(TableReport):
  '''
  A report showing the loading of each resource.
  '''
  template = 'output/resource.html'
  title = _('Resource Report')
  basequeryset = Resource.objects.all()
  model = Resource
  rows = (
    ('resource',{
      'filter': FilterText(field='name'),
      'order_by': 'name',
      'title': _('resource'),
      }),
    ('location',{
      'filter': FilterText(field='location__name'),
      'title': _('location'),
      }),
    )
  crosses = (
    ('available',{'title': _('available'), 'editable': lambda req: req.user.has_perm('input.change_resource'),}),
    ('load',{'title': _('load')}),
    ('utilization',{'title': _('utilization %'),}),
    )
  columns = (
    ('bucket',{'title': _('bucket')}),
    )

  @staticmethod
  def resultlist1(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    return basequery.values('name','location')

  @staticmethod
  def resultlist2(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    # Execute the query
    cursor = connection.cursor()
    query = '''
       select x.name as row1, x.location_id as row2,
             x.bucket as col1, x.startdate as col2, x.enddate as col3,
             min(x.available),
             coalesce(sum(loaddata.quantity * %s), 0) as loading
       from (
         select res.name as name, res.location_id as location_id,
               d.bucket as bucket, d.startdate as startdate, d.enddate as enddate,
               coalesce(sum(bucket.value * %s),0) as available
         from (%s) res
         -- Multiply with buckets
         cross join (
              select %s as bucket, %s_start as startdate, %s_end as enddate
              from dates
              where day_start >= '%s' and day_start < '%s'
              group by %s, %s_start, %s_end
              ) d
         -- Available capacity
         left join bucket
         on res.maximum_id = bucket.calendar_id
         and d.startdate <= bucket.enddate
         and d.enddate >= bucket.startdate
         -- Grouping
         group by res.name, res.location_id, d.bucket, d.startdate, d.enddate
       ) x
       -- Load data
       left join (
         select %s as resource_id, startdatetime, enddatetime, quantity
         from out_loadplan
         ) loaddata
       on x.name = loaddata.resource_id
       and x.startdate <= loaddata.enddatetime
       and x.enddate >= loaddata.startdatetime
       -- Grouping and ordering
       group by x.name, x.location_id, x.bucket, x.startdate, x.enddate
       order by %s, x.startdate
       ''' % ( sql_overlap('loaddata.startdatetime','loaddata.enddatetime','x.startdate','x.enddate'),
         sql_overlap('bucket.startdate','bucket.enddate','d.startdate','d.enddate'),
         basesql,connection.ops.quote_name(bucket),bucket,bucket,startdate,enddate,
         connection.ops.quote_name(bucket),bucket,bucket,connection.ops.quote_name('resource'),sortsql)
    cursor.execute(query, baseparams)

    # Build the python result
    for row in cursor.fetchall():
      if row[5] != 0: util = row[6] * 100 / row[5]
      else: util = 0
      yield {
        'resource': row[0],
        'location': row[1],
        'bucket': row[2],
        'startdate': python_date(row[3]),
        'enddate': python_date(row[4]),
        'available': row[5],
        'load': row[6],
        'utilization': util,
        }


class DetailReport(ListReport):
  '''
  A list report to show loadplans.
  '''
  template = 'output/loadplan.html'
  title = _("Resource Load Detail")
  reset_crumbs = False
  basequeryset = LoadPlan.objects.extra(
    select={'operation':'out_operationplan.operation'},
    where=['out_operationplan.identifier = out_loadplan.operationplan'],
    tables=['out_operationplan'])
  model = LoadPlan
  frozenColumns = 0
  editable = False
  rows = (
    ('resource', {
      'filter': FilterText(),
      'title': _('resource')
      }),
    # @todo Eagerly awaiting the Django queryset refactoring to be able to filter on the operation field.
    ('operation', {
      'title': _('operation'),
      }),
    ('startdatetime', {
      'title': _('startdate'),
      'filter': FilterDate(field='startdate'),
      }),
    ('enddatetime', {
      'title': _('enddate'),
      'filter': FilterDate(field='enddate'),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('operationplan', {
      'filter': FilterNumber(),
      'title': _('operationplan')
      }),
    )

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified
