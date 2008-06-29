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
from django.conf import settings

from utils.db import sql_datediff
from utils.report import *
from input.models import Plan


class Report(ListReport):
  template = 'output/kpi.html'
  title = _("Performance Indicators")
  reset_crumbs = True
  frozenColumns = 0
  basequeryset = Plan.objects.all()
  rows = (
    ('category', {'sort': False, 'title': _('category')}),
    ('name', {'sort': False, 'title': _('name')}),
    ('value', {'sort': False, 'title': _('value')}),
    )
  default_sort = '2a'
  
  @staticmethod
  def resultlist1(basequery, bucket, startdate, enddate, sortsql='1 asc'):
    # Execute the query
    cursor = connection.cursor()
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
      where plandatetime > duedatetime and plandatetime is not null
      union
      select 204, 'Demand', 'Unplanned', coalesce(round(sum(quantity)),0)
      from out_demand
      where planquantity is null
      union
      select 205, 'Demand', 'Total lateness', coalesce(round(sum(planquantity * %s)),0)
      from out_demand
      where plandatetime > duedatetime and plandatetime is not null
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
      ''' % (
        # Oracle needs conversion from the field out_problem.name
        # (in 'national character set') to the database 'character set'.
        settings.DATABASE_ENGINE == 'oracle' and "csconvert(name,'CHAR_CS')" or 'name',
        settings.DATABASE_ENGINE == 'oracle' and "csconvert(name,'CHAR_CS')" or 'name',
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
