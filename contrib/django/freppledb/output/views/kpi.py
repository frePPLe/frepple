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

from django.utils.translation import ugettext_lazy as _
from django.db import connections
from django.conf import settings

from freppledb.common.db import sql_datediff
from freppledb.common.models import Parameter
from freppledb.common.report import GridReport, GridFieldText, GridFieldNumber


class Report(GridReport):
  title = _("Performance Indicators")
  frozenColumns = 0
  basequeryset = Parameter.objects.all()
  rows = (
    GridFieldText('category', title=_('category'), sortable=False, editable=False, align='center'),
    GridFieldText('name', title=_('name'), sortable=False, editable=False, align='center'),
    GridFieldNumber('value', title=_('value'), sortable=False, editable=False, align='center'),
    )
  default_sort = (1,'asc')
  filterable = False
  multiselect = False

  @staticmethod
  def query(request, basequery):
    # Execute the query
    cursor = connections[request.database].cursor()
    query = '''
      select 101 as id, 'Problem count' as category, %s as name, count(*) as value
      from out_problem
      group by name
      union
      select 102, 'Problem weight', %s, round(sum(weight))
      from out_problem
      group by name
      union
      select 201, 'Demand', 'Requested', round(sum(quantity))
      from out_demand
      union
      select 202, 'Demand', 'Planned', round(sum(planquantity))
      from out_demand
      union
      select 203, 'Demand', 'Planned late', coalesce(round(sum(planquantity)),0)
      from out_demand
      where plandate > due and plandate is not null
      union
      select 204, 'Demand', 'Unplanned', coalesce(round(sum(quantity)),0)
      from out_demand
      where planquantity is null
      union
      select 205, 'Demand', 'Total lateness', coalesce(round(sum(planquantity * %s)),0)
      from out_demand
      where plandate > due and plandate is not null
      union
      select 301, 'Operation', 'Count', count(*)
      from out_operationplan
      union
      select 301, 'Operation', 'Quantity', round(sum(quantity))
      from out_operationplan
      union
      select 302, 'Resource', 'Usage', round(sum(quantity * %s))
      from out_loadplan
      union
      select 401, 'Material', 'Produced', round(sum(quantity))
      from out_flowplan
      where quantity>0
      union
      select 402, 'Material', 'Consumed', round(sum(-quantity))
      from out_flowplan
      where quantity<0
      order by 1
      ''' % (
        # Oracle needs conversion from the field out_problem.name
        # (in 'national character set') to the database 'character set'.
        settings.DATABASES[request.database]['ENGINE'] == 'oracle' and "csconvert(name,'CHAR_CS')" or 'name',
        settings.DATABASES[request.database]['ENGINE'] == 'oracle' and "csconvert(name,'CHAR_CS')" or 'name',
        sql_datediff('plandate','due'),
        sql_datediff('enddate','startdate')
        )
    cursor.execute(query)

    # Build the python result
    for row in cursor.fetchall():
      yield {
        'category': row[1],
        'name': row[2],
        'value': row[3],
        }
