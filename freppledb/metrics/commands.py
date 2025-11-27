#
# Copyright (C) 2019 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
from datetime import timedelta, datetime

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.models import Parameter
from freppledb.input.models import Item, Resource


@PlanTaskRegistry.register
class GetPlanMetrics(PlanTask):
    description = "Update item and resource metrics"

    sequence = 530

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "supply" in os.environ and "noexport" not in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        with connections[database].cursor() as cursor:
            # Update item metrics
            try:
                try:
                    window = frepple.settings.current + timedelta(
                        days=int(
                            Parameter.getValue("metrics.demand_window", database, "999")
                        )
                    )
                except Exception:
                    print("Warning: invalid parameter 'metrics.demand_window'")
                    window = datetime(2030, 12, 31)

                Item.createRootObject(database=database)

                cursor.execute(
                    """
                    create temporary table item_hierarchy (parent character varying,
                                                           child character varying);

                    insert into item_hierarchy
                    select parent.name, item.name from item
                    inner join item parent on item.lft > parent.lft and item.lft < parent.rght;

                    create index on item_hierarchy (child);

                    create temporary table demand_late_unplanned as
                    with dmd_late_unplanned as (
                      select
                        demand.name,
                        demand.item_id,
                        demand.quantity,
                        sum(case when demand.due < operationplan.enddate then operationplan.quantity end) as late_quantity,
                        sum(operationplan.quantity) as planned_quantity
                      from demand
                      left outer join operationplan on operationplan.demand_id = demand.name
                      where demand.status = 'open'
                        and demand.due < %s
                      group by demand.name
                    )
                    select
                      item_id,
                      sum(case when late_quantity is not null then 1 end) as late_count,
                      sum(late_quantity) as late_quantity,
                      sum(late_quantity * coalesce(item.cost, 0)) as late_cost,
                      sum(case when planned_quantity is null then 1 end) as unplanned_count,
                      sum(case when planned_quantity is null then quantity end) as unplanned_quantity,
                      sum(case when planned_quantity is null then quantity * coalesce(item.cost, 0) end) as unplanned_cost
                    from dmd_late_unplanned
                    inner join item
                      on item_id = item.name
                    group by item_id
                    """,
                    (window,),
                )

                # TODO REFACTOR TO WORK WITHOUT OUT_PROBLEM TABLE
                # if "freppledb.forecast" in settings.INSTALLED_APPS:
                #     cursor.execute(
                #         """
                #         insert into out_problem_tmp
                #         select item.name as item_id, out_problem.name, out_problem.weight, out_problem.weight*coalesce(item.cost) from out_problem
                #         inner join forecast on forecast.name = left(out_problem.owner, -13)
                #         inner join item on item.name = forecast.item_id
                #         where out_problem.name in ('unplanned', 'late')
                #         and out_problem.startdate < %s;
                #        """,
                #         (window,),
                #     )

                cursor.execute(
                    """
                    create temporary table metrics as
                    select item.name as item_id,
                    coalesce(sum(late_count),0) as latedemandcount,
                    coalesce(sum(late_quantity),0) as latedemandquantity,
                    coalesce(sum(late_cost),0) as latedemandvalue,
                    coalesce(sum(unplanned_count),0) as unplanneddemandcount,
                    coalesce(sum(unplanned_quantity),0) as unplanneddemandquantity,
                    coalesce(sum(unplanned_cost),0) as unplanneddemandvalue
                    from item
                    left outer join demand_late_unplanned
                      on demand_late_unplanned.item_id = item.name
                    where item.lft = item.rght - 1
                    group by item.name;

                    create unique index on metrics (item_id);

                    insert into metrics
                    select parent,
                    coalesce(sum(latedemandcount),0),
                    coalesce(sum(latedemandquantity),0),
                    coalesce(sum(latedemandvalue),0),
                    coalesce(sum(unplanneddemandcount),0),
                    coalesce(sum(unplanneddemandquantity),0),
                    coalesce(sum(unplanneddemandvalue),0)
                    from item_hierarchy
                    left outer join metrics on item_hierarchy.child = metrics.item_id
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
                    drop table demand_late_unplanned;
                    drop table metrics;
                    """
                )

            except Exception as e:
                print("Error updating item metrics: %s" % e)

            # Update resource metrics
            try:
                Resource.rebuildHierarchy(database)

                cursor.execute(
                    """
                    with resource_hierarchy as (select child.name child, parent.name parent
                    from resource child
                    inner join resource parent on child.lft between parent.lft and parent.rght
                    where child.lft = child.rght-1),
                    cte as (
                        select parent, count(out_problem.id) as overloadcount from resource_hierarchy
                        left outer join out_problem
                          on out_problem.name = 'overload'
                          and out_problem.owner = resource_hierarchy.child
                        group by parent
                    )
                    update resource
                    set overloadcount = cte.overloadcount
                    from cte
                    where cte.parent = resource.name
                    and resource.overloadcount is distinct from cte.overloadcount;
                    """
                )

            except Exception as e:
                print("Error updating resource metrics: %s" % e)
