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

from datetime import timedelta, datetime
import json
import os

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.commands import (
    PlanTaskRegistry,
    PlanTask,
    CopyFromGenerator,
    clean_value,
)
from freppledb.common.models import Parameter, UserPreference
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

                with_fcst_module = "freppledb.forecast" in settings.INSTALLED_APPS

                cursor.execute(
                    """
                    create temporary table item_hierarchy (parent character varying,
                                                           child character varying);

                    insert into item_hierarchy
                    select parent.name, item.name from item
                    inner join item parent on item.lft > parent.lft and item.lft < parent.rght;

                    create index on item_hierarchy (child);

                    create temporary table demand_late_unplanned (
                       item_id varchar,
                       late_count numeric(20,8),
                       late_quantity numeric(20,8),
                       late_cost numeric(20,8),
                       unplanned_count numeric(20,8),
                       unplanned_quantity numeric(20,8),
                       unplanned_cost numeric(20,8)
                       );
                    """,
                    (window,),
                )

                def getItemMetrics(window, performance):
                    import frepple

                    metrics = {}
                    for f in frepple.demands():
                        if (
                            f.due > window
                            or not f.item
                            or f.status != "open"
                            or f.quantity <= 0
                            or (
                                with_fcst_module
                                and isinstance(f, (frepple.demand_forecast))
                            )
                        ):
                            continue
                        planned = 0
                        planned_late = 0
                        for op in f.operationplans:
                            planned += op.quantity
                            if op.end > f.due:
                                planned_late += op.quantity
                        if not planned:
                            # Unplanned
                            category = "unplanned"
                            if f.item.name in metrics:
                                metrics[f.item.name]["unplanned_count"] += 1
                                metrics[f.item.name]["unplanned_quantity"] += f.quantity
                                metrics[f.item.name]["unplanned_cost"] += (
                                    f.quantity * f.item.cost
                                )
                            else:
                                metrics[f.item.name] = {
                                    "late_count": 0,
                                    "late_quantity": 0,
                                    "late_cost": 0,
                                    "unplanned_count": 1,
                                    "unplanned_quantity": (f.quantity),
                                    "unplanned_cost": (f.quantity * f.item.cost),
                                }
                        elif planned_late:
                            # Late
                            category = "late"
                            if f.item.name in metrics:
                                metrics[f.item.name]["late_count"] += 1
                                metrics[f.item.name]["late_quantity"] += planned_late
                                metrics[f.item.name]["late_cost"] += (
                                    planned_late * f.item.cost
                                )
                            else:
                                metrics[f.item.name] = {
                                    "late_count": 1,
                                    "late_quantity": planned_late,
                                    "late_cost": planned_late * f.item.cost,
                                    "unplanned_count": 0,
                                    "unplanned_quantity": 0,
                                    "unplanned_cost": 0,
                                }
                        else:
                            # On time
                            category = "ontime"

                        # Overall delivery performance
                        key = category + (
                            "_fcst"
                            if with_fcst_module
                            and isinstance(f, frepple.demand_forecastbucket)
                            else "_so"
                        )
                        performance[key]["count"] += 1
                        performance[key]["quantity"] += f.quantity
                        performance[key]["cost"] += f.quantity * f.item.cost

                    for i, m in metrics.items():
                        yield (
                            f"{clean_value(i)}\v{m["late_count"]}\v{m["late_quantity"]}\v{m["late_cost"]}\v"
                            f"{m["unplanned_count"]}\v{m["unplanned_quantity"]}\v{m["unplanned_cost"]}\n"
                        )

                performance = {
                    "ontime_so": {
                        "count": 0,
                        "quantity": 0,
                        "cost": 0,
                    },
                    "late_so": {
                        "count": 0,
                        "quantity": 0,
                        "cost": 0,
                    },
                    "unplanned_so": {
                        "count": 0,
                        "quantity": 0,
                        "cost": 0,
                    },
                }
                if with_fcst_module:
                    performance.update(
                        {
                            "ontime_fcst": {
                                "count": 0,
                                "quantity": 0,
                                "cost": 0,
                            },
                            "late_fcst": {
                                "count": 0,
                                "quantity": 0,
                                "cost": 0,
                            },
                            "unplanned_fcst": {
                                "count": 0,
                                "quantity": 0,
                                "cost": 0,
                            },
                        }
                    )

                # Export item-level metrics (and compute overal performance)
                cursor.copy_from(
                    CopyFromGenerator(getItemMetrics(window, performance)),
                    table="demand_late_unplanned",
                    size=1024,
                    sep="\v",
                )

                # Store the delivery performance metrics
                UserPreference.objects.using(database).update_or_create(
                    property="widget.deliveryperformance",
                    defaults={"value": performance},
                )

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
                    update item set
                        latedemandcount = updated.latedemandcount,
                        latedemandquantity = updated.latedemandquantity,
                        latedemandvalue = updated.latedemandvalue,
                        unplanneddemandcount = updated.unplanneddemandcount,
                        unplanneddemandquantity = updated.unplanneddemandquantity,
                        unplanneddemandvalue = updated.unplanneddemandvalue
                    from (
                        select
                            i.name,
                            m.latedemandcount as latedemandcount,
                            m.latedemandquantity as latedemandquantity,
                            m.latedemandvalue as latedemandvalue,
                            m.unplanneddemandcount as unplanneddemandcount,
                            m.unplanneddemandquantity as unplanneddemandquantity,
                            m.unplanneddemandvalue as unplanneddemandvalue
                        from item i
                        left join metrics m on i.name = m.item_id
                    ) as updated
                    where item.name = updated.name
                    and (
                      item.latedemandcount is distinct from updated.latedemandcount
                      or item.latedemandquantity is distinct from updated.latedemandquantity
                      or item.latedemandvalue is distinct from updated.latedemandvalue
                      or item.unplanneddemandcount is distinct from updated.unplanneddemandcount
                      or item.unplanneddemandquantity is distinct from updated.unplanneddemandquantity
                      or item.unplanneddemandvalue is distinct from updated.unplanneddemandvalue
                    )
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
