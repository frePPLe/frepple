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
from freppledb.input.models import Item


@PlanTaskRegistry.register
class GetPlanMetrics(PlanTask):

    description = "Update item and resource metrics"

    sequence = 530

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        with connections[database].cursor() as cursor:
            # Update item metrics
            try:

                Item.createRootObject(database=database)

                cursor.execute(
                    """
                    create temporary table item_hierarchy (parent character varying(300),
                                                           child character varying(300));
                    
                    insert into item_hierarchy
                    select parent.name, item.name from item
                    inner join item parent on item.lft > parent.lft and item.lft < parent.rght;
                    
                    create index on item_hierarchy (child);
                    
                    create temporary table out_problem_tmp
                    as 
                    select item.name as item_id, out_problem.name, out_problem.weight, out_problem.weight*coalesce(item.cost,0) as weight_cost 
                     from out_problem
                    inner join demand on demand.name = out_problem.owner
                    inner join item on item.name = demand.item_id
                    where out_problem.name in ('unplanned', 'late');
                    """
                )

                cursor.execute(
                    """
                    create temporary table metrics as
                    select item.name as item_id, 
                    sum(case when out_problem_tmp.name = 'late' then 1 else 0 end) as latedemandcount,
                    sum(case when out_problem_tmp.name = 'late' then out_problem_tmp.weight else 0 end) as latedemandquantity,
                    sum(case when out_problem_tmp.name = 'late' then out_problem_tmp.weight_cost else 0 end) as latedemandvalue,
                    sum(case when out_problem_tmp.name = 'unplanned' then 1 else 0 end) as unplanneddemandcount,
                    sum(case when out_problem_tmp.name = 'unplanned' then out_problem_tmp.weight else 0 end) as unplanneddemandquantity,
                    sum(case when out_problem_tmp.name = 'unplanned' then out_problem_tmp.weight_cost else 0 end) as unplanneddemandvalue
                    from item
                    left outer join out_problem_tmp on out_problem_tmp.item_id = item.name
                    where item.lft = item.rght - 1
                    group by item.name;
                    
                    create unique index on metrics (item_id);
                    
                    insert into metrics
                    select parent,
                    sum(latedemandcount),
                    sum(latedemandquantity),
                    sum(latedemandvalue),
                    sum(unplanneddemandcount),
                    sum(unplanneddemandquantity),
                    sum(unplanneddemandvalue)
                    from metrics
                    inner join item_hierarchy on item_hierarchy.child = metrics.item_id
                    group by parent;                    
                """
                )

                cursor.execute(
                    """
                    update item
                    set latedemandcount = metrics.latedemandcount,
                    latedemandquantity = metrics.latedemandquantity,
                    latedemandvalue = metrics.latedemandvalue,
                    unplanneddemandcount = metrics.unplanneddemandcount,
                    unplanneddemandquantity = metrics.unplanneddemandquantity,
                    unplanneddemandvalue = metrics.unplanneddemandvalue
                    from metrics
                    where item.name = metrics.item_id
                    and (item.latedemandcount is distinct from metrics.latedemandcount
                    or item.latedemandquantity is distinct from metrics.latedemandquantity
                    or item.latedemandvalue is distinct from metrics.latedemandvalue
                    or item.unplanneddemandcount is distinct from metrics.unplanneddemandcount
                    or item.unplanneddemandquantity is distinct from metrics.unplanneddemandquantity
                    or item.unplanneddemandvalue is distinct from metrics.unplanneddemandvalue);
                """
                )

                cursor.execute(
                    """
                    drop table item_hierarchy;
                    drop table out_problem_tmp;
                    drop table metrics;
                """
                )

            except Exception as e:
                print("Error updating item metrics: %s" % e)

            # Update resource metrics
            try:
                cursor.execute(
                    """
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
          """
                )
            except Exception as e:
                print("Error updating resource metrics: %s" % e)
