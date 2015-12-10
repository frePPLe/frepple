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

from django.utils.translation import ugettext_lazy as _
from django.db import connections

from freppledb.common.db import sql_datediff
from freppledb.common.models import Parameter
from freppledb.common.report import GridReport, GridFieldText, GridFieldInteger


class Report(GridReport):
  title = _("Performance Indicators")
  frozenColumns = 0
  basequeryset = Parameter.objects.all()
  permissions = (("view_kpi_report", "Can view kpi report"),)
  rows = (
    GridFieldText('category', title=_('category'), sortable=False, editable=False, align='center'),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), sortable=False, editable=False, align='center'),
    GridFieldInteger('value', title=_('value'), sortable=False, editable=False, align='center'),
    )
  default_sort = (1, 'asc')
  filterable = False
  multiselect = False

  @staticmethod
  def query(request, basequery):
    # Execute the query
    cursor = connections[request.database].cursor()
    query = '''
      select 101 as id, 'Problem count' as category, name as name, count(*) as value
      from out_problem
      group by name
      union all
      select 102, 'Problem weight', name, round(sum(weight))
      from out_problem
      group by name
      union all
      select 201, 'Demand', 'Requested', coalesce(round(sum(quantity)),0)
      from out_demand
      union all
      select 202, 'Demand', 'Planned', coalesce(round(sum(planquantity)),0)
      from out_demand
      union all
      select 203, 'Demand', 'Planned late', coalesce(round(sum(planquantity)),0)
      from out_demand
      where plandate > due and plandate is not null
      union all
      select 204, 'Demand', 'Unplanned', coalesce(round(sum(quantity)),0)
      from out_demand
      where planquantity is null
      union all
      select 205, 'Demand', 'Total lateness', coalesce(round(sum(planquantity * %s)),0)
      from out_demand
      where plandate > due and plandate is not null
      union all
      select 301, 'Operation', 'Count', count(*)
      from out_operationplan
      union all
      select 301, 'Operation', 'Quantity', coalesce(round(sum(quantity)),0)
      from out_operationplan
      union all
      select 302, 'Resource', 'Usage', coalesce(round(sum(quantity * %s)),0)
      from out_loadplan
      union all
      select 401, 'Material', 'Produced', coalesce(round(sum(quantity)),0)
      from out_flowplan
      where quantity>0
      union all
      select 402, 'Material', 'Consumed', coalesce(round(sum(-quantity)),0)
      from out_flowplan
      where quantity<0
      order by 1
      ''' % (
        sql_datediff('plandate', 'due'),
        sql_datediff('enddate', 'startdate')
      )
    cursor.execute(query)

    # Build the python result
    for row in cursor.fetchall():
      yield {
        'category': row[1],
        'name': row[2],
        'value': row[3],
        }
