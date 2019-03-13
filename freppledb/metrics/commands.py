#
# Copyright (C) 2019 by frePPLe bvba
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

import os

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.commands import PlanTaskRegistry, PlanTask


@PlanTaskRegistry.register
class GetPlanMetrics(PlanTask):

  description = "Update item and resource metrics"

  sequence = 530

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    if 'supply' in os.environ:
      return 1
    else:
      return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    with connections[database].cursor() as cursor:
      # Update item metrics
      try:
        cursor.execute('''
          with metrics as (
            select
              item.name as item,
              coalesce(sum(case when out_problem.name = 'late' then 1 else 0 end),0) latedemandcount,
              coalesce(sum(case when out_problem.name = 'late' then weight else 0 end),0) latedemandquantity,
              coalesce(sum(case when out_problem.name = 'late' then weight * item.cost else 0 end),0) latedemandvalue,
              coalesce(sum(case when out_problem.name = 'unplanned' then 1 else 0 end),0) unplanneddemandcount,
              coalesce(sum(case when out_problem.name = 'unplanned' then weight else 0 end),0) unplanneddemandquantity,
              coalesce(sum(case when out_problem.name = 'unplanned' then weight * item.cost else 0 end),0) unplanneddemandvalue
            from out_problem
            inner join demand
              on out_problem.owner = demand.name and out_problem.name in ('unplanned', 'late')
            right outer join item -- right outer join to assure all items are in the output
              on demand.item_id = item.name
            group by item.name
            )
          update item set
            latedemandcount = metrics.latedemandcount,
            latedemandquantity = metrics.latedemandquantity,
            latedemandvalue = metrics.latedemandvalue,
            unplanneddemandcount = metrics.unplanneddemandcount,
            unplanneddemandquantity = metrics.unplanneddemandquantity,
            unplanneddemandvalue = metrics.unplanneddemandvalue
          from metrics
          where metrics.item = item.name
          and (item.latedemandcount is distinct from metrics.latedemandcount
            or item.latedemandquantity is distinct from metrics.latedemandquantity
            or item.latedemandvalue is distinct from metrics.latedemandvalue
            or item.unplanneddemandcount is distinct from metrics.unplanneddemandcount
            or item.unplanneddemandquantity is distinct from metrics.unplanneddemandquantity
            or item.unplanneddemandvalue is distinct from metrics.unplanneddemandvalue
            )
          ''')
      except Exception as e:
        print("Error updating item metrics: %s" % e)

      # Update resource metrics
      try:
        cursor.execute('''
          with metrics as (
            select
              resource.name as resource,
              coalesce(count(out_problem.name), 0) as overloadcount
            from out_problem
            right outer join resource -- right outer join to assure all resources are in the output
              on out_problem.owner = resource.name
            where out_problem.name is null or out_problem.name = 'overload'
            group by resource.name
            )
          update resource set
            overloadcount = metrics.overloadcount
          from metrics
          where metrics.resource = resource.name
            and resource.overloadcount is distinct from metrics.overloadcount
          ''')
      except Exception as e:
        print("Error updating resource metrics: %s" % e)
