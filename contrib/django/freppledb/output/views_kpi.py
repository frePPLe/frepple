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

from django.utils.translation import ugettext_lazy as _
from django.db import connection

from utils.db import sql_datediff
from utils.report import ListReport
from utils.reportfilter import FilterText
from input.models import Plan


class OverviewReport(ListReport):
  template = 'output/kpi.html'
  title = _("Plan performance indicators")
  reset_crumbs = True
  basequeryset = Plan.objects.all()
  rows = (
    ('category', {'sort': False, 'title': _('category')}),
    ('name', {'sort': False, 'title': _('name')}),
    ('value', {'sort': False, 'title': _('value')}),
    )

  @staticmethod
  def resultquery(basesql, baseparams, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
    query = '''
      select 1, 'Problem', 'Count', count(*)
      from out_problem
      union
      select 2, 'Problem', 'Weight', round(sum(weight),2)
      from out_problem
      union
      select 3, 'Demand', 'Requested', round(sum(quantity),2)
      from out_demand
      union
      select 4, 'Demand', 'Planned', round(sum(planquantity),2)
      from out_demand
      union
      select 5, 'Demand', 'Planned late', coalesce(round(sum(planquantity),2),0)
      from out_demand
      where plandatetime > duedatetime and plandatetime is not null
      union
      select 6, 'Demand', 'Unplanned', coalesce(round(sum(quantity),2),0)
      from out_demand
      where planquantity is null
      union
      select 7, 'Demand', 'Total lateness', coalesce(round(sum(planquantity * %s),2),0)
      from out_demand
      where plandatetime > duedatetime and plandatetime is not null
      union
      select 8, 'Operation', 'Quantity', round(sum(quantity),2)
      from out_operationplan
      union
      select 9, 'Resource', 'Usage', round(sum(quantity * %s),2)
      from out_loadplan
      union
      select 10, 'Material', 'Produced', round(sum(quantity),2)
      from out_flowplan
      where quantity>0
      union
      select 11, 'Material', 'Consumed', round(sum(-quantity),2)
      from out_flowplan
      where quantity<0
      ''' % (
        sql_datediff('plandatetime','duedatetime'),
        sql_datediff('enddatetime','startdatetime')
        )
    cursor.execute(query)

    # Build the python result
    for row in cursor.fetchall():
      yield {
        'category': row[1],
        'name': row[2],
        'value': row[3],
        }

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified