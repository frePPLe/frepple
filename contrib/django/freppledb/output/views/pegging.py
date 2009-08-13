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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from datetime import timedelta

from django.utils.translation import ugettext_lazy as _
from django.db.models import Min, Max

from input.models import Plan, Demand
from output.models import DemandPegging
from common.report import *
 
    
class Report(ListReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/pegging.html'
  title = _("Pegging Report")
  reset_crumbs = False
  basequeryset = Demand.objects.all().values('name')
  frozenColumns = 0
  editable = False
  timebuckets = True
  rows = (
    ('name', {   # XXX TODO
      'title': _('depth'),
      }),
    ('operation', {
      'title': _('operation'),
      }),
    ('buffer', {
      'title': _('buffer'),
      }),
    ('item', {
      'title': _('item'),
      }),
    ('resource', {
      'title': _('resource'),
      }),
    ('startdate', {
      'title': _('startdate'),
      }),
    ('enddate', {
      'title': _('enddate'),
      }),
    ('quantity', {
      'title': _('quantity'),
      }),
    ('percent used', {
      'title': _('% used'),
      }),
    )

  @staticmethod
  def resultlist1(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    basesql, baseparams = basequery.query.as_sql(with_col_aliases=True)
    cursor = connection.cursor()

    # query 1: pick up all resources loaded 
    resource = {}
    query = '''
      select operationplan, theresource
      from out_loadplan
      where operationplan in (
        select prod_operationplan as opplan_id
          from out_demandpegging
          where demand in (select dms.name from (%s) dms)
        union 
        select cons_operationplan as opplan_id
          from out_demandpegging
          where demand in (select dms.name from (%s) dms)
      )
      ''' % (basesql, basesql)
    cursor.execute(query, baseparams + baseparams)
    for row in cursor.fetchall():
      if row[0] in resource:
        resource[row[0]] += (row[1], )
      else:
        resource[row[0]] = ( row[1], )
     
    # query 2: pick up all operationplans
    query = '''    
      select min(depth), min(opplans.id), operation, opplans.quantity, 
        opplans.startdate, opplans.enddate, operation.name,
        max(buffer), max(opplans.item), opplan_id, out_demand.due,
        sum(quantity_demand) * 100 / opplans.quantity
      from (
        select depth, peg.id+1 as id, operation, quantity, startdate, enddate, 
          buffer, item, prod_operationplan as opplan_id, quantity_demand
        from out_demandpegging peg, out_operationplan prod
        where peg.demand in (select dms.name from (%s) dms)
        and peg.prod_operationplan = prod.id
        union
        select depth, peg.id, operation, quantity, startdate, enddate, 
          null, null, cons_operationplan, 0
        from out_demandpegging peg, out_operationplan cons
        where peg.demand in (select dms.name from (%s) dms)
        and peg.cons_operationplan = cons.id
      ) opplans
      left join operation 
      on operation = operation.name
      left join out_demand 
      on opplan_id = out_demand.operationplan
      group by operation, opplans.quantity, opplans.startdate, opplans.enddate, 
        operation.name, opplan_id, out_demand.due
      order by min(opplans.id)
      ''' % (basesql, basesql)
    cursor.execute(query, baseparams + baseparams)

    # Build the python result
    for row in cursor.fetchall():    
      yield {
          'depth': row[0],
          'peg_id': row[1],
          'operation': row[2],
          'quantity': row[3],
          'startdate': row[4],
          'enddate': row[5],
          'hidden': row[6] == None,
          'buffer': row[7],
          'item': row[8],
          'id': row[9],
          'due': row[10],
          'percent_used': row[11],
          'resource': row[9] in resource and resource[row[9]] or None,
          }


@staff_member_required
def GraphData(request, entity):
  basequery = Demand.objects.filter(name__exact=entity).values('name')
  (bucket,start,end,bucketlist) = getBuckets(request)
  current = Plan.objects.get(pk="1").currentdate
  total_start = []
  total_end = []
  result = [ i for i in Report.resultlist1(basequery,bucket,start,end) ]
  min = None
  max = None

  # extra query: pick up the linked operation plans  
  cursor = connection.cursor()
  query = '''
    select cons_operationplan, prod_operationplan
    from out_demandpegging
    where demand = '%s'
    group by cons_operationplan, prod_operationplan
    ''' % entity
  cursor.execute(query)
  connections = [ {'to':row[1], 'from':row[0]} for row in cursor.fetchall() ]

  # Rebuild result list
  for i in result:
    if i['enddate'] < i['startdate'] + timedelta(1):
      i['enddate'] = i['startdate']
    else:
      i['enddate'] = i['enddate'] - timedelta(1)
    if i['startdate'] < current: i['startdate'] = current
    if i['enddate'] < current: i['enddate'] = current
    if min == None or i['startdate'] < min: min = i['startdate']  
    if max == None or i['enddate'] > max: max = i['enddate']
    if min == None or i['due'] and i['due'] < min: min = i['due']
    if max == None or i['due'] and i['due'] > max: max = i['due']
  
  # Add a line to mark the current date
  if min <= current and max >= current:
    todayline = current
  else:
    todayline = None

  # Snap to dates
  min = min.date()
  max = max.date()
  
  buckets = []
  for i in bucketlist:
    if i['end'] > min and i['start'] < max:
      buckets.append( {'start': i['start'], 'end': i['end'] - timedelta(1), 'name': i['name']} )
  context = { 
    'buckets': buckets, 
    'reportbucket': bucket,
    'reportstart': start,
    'reportend': end,
    'objectlist1': result, 
    'connections': connections,
    'todayline': todayline,
    }
  return HttpResponse(
    loader.render_to_string("output/pegging.xml", context, context_instance=RequestContext(request)),
    )
