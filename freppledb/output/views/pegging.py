#
# Copyright (C) 2007-2013 by frePPLe bv
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

from datetime import datetime, timedelta

from django.db import connections, transaction
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from freppledb.input.models import Demand
from freppledb.common.report import (
    GridReport,
    GridFieldText,
    GridFieldNumber,
    getCurrentDate,
)


class ReportByDemand(GridReport):
    """
    This report shows a simple Gantt chart with the delivery of a sales order.
    """

    template = "output/pegging.html"
    title = _("Demand plan")
    filterable = False
    frozenColumns = 0
    editable = False
    default_sort = None
    hasTimeBuckets = True
    multiselect = False
    help_url = "user-interface/plan-analysis/demand-gantt-report.html"
    rows = (
        GridFieldText("id", key=True, editable=False, sortable=False, hidden=True),
        GridFieldText("depth", title=_("depth"), editable=False, sortable=False),
        GridFieldText(
            "operation",
            title=_("operation"),
            editable=False,
            sortable=False,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "type", title=_("type"), editable=False, sortable=False, width=100
        ),
        GridFieldText(
            "item",
            title=_("item"),
            editable=False,
            sortable=False,
            initially_hidden=True,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "item__description",
            title=_("item description"),
            editable=False,
            sortable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            editable=False,
            sortable=False,
            extra="formatter:reslistfmt",
        ),
        GridFieldNumber(
            "quantity",
            title=_("required quantity"),
            field_name="required_quantity",
            editable=False,
            sortable=False,
        ),
        GridFieldText(
            "operationplans",
            width=1000,
            extra="formatter:ganttcell",
            editable=False,
            sortable=False,
        ),
        GridFieldText("parent", editable=False, sortable=False, hidden=True),
        GridFieldText("leaf", editable=False, sortable=False, hidden=True),
        GridFieldText("expanded", editable=False, sortable=False, hidden=True),
        GridFieldText("current", editable=False, sortable=False, hidden=True),
        GridFieldText("due", editable=False, sortable=False, hidden=True),
        GridFieldText("showdrilldown", editable=False, sortable=False, hidden=True),
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        return Demand.objects.filter(name__exact=args[0]).values("name")

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plan"
            return {
                "active_tab": "plan",
                "title": force_str(Demand._meta.verbose_name) + " " + args[0],
                "post_title": _("plan"),
                "model": Demand,
            }
        else:
            return {}

    @classmethod
    def getBuckets(reportclass, request, *args, **kwargs):
        # Get the earliest and latest operationplan, and the demand due date
        cursor = connections[request.database].cursor()
        cursor.execute(
            """
            with cte0 as (
            select t.opplan as opplan from demand
            inner join lateral (select t->>'opplan' as opplan
                                from jsonb_array_elements(demand.plan->'pegging') t) t on true
            where name = %s
            ),
            cte1 as (
            with recursive cte as
                    (
                    select 1 as level,
                        nextopplan.reference as nextreference,
                        nextopplan.type,
                        case when nextopplan.type = 'PO' then 'Purchase '||nextopplan.item_id||' @ '||nextopplan.location_id||' from '||nextopplan.supplier_id
                        when nextopplan.type = 'DO' then 'Ship '||nextopplan.item_id||' from '||nextopplan.origin_id||' to '||nextopplan.destination_id
                        else nextopplan.operation_id end,
                        nextopplan.status,
                        nextopplan.item_id,
                        coalesce(nextopplan.location_id, nextopplan.destination_id),
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.startdate,'YYYY-MM-DD hh24:mi:ss') end,
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.enddate,'YYYY-MM-DD hh24:mi:ss') end,
                        t.quantity,
                        nextopplan.quantity,
                        t.offset as x,
                        t.offset + t.quantity as y,
                        (coalesce(nextopplan.item_id,'')||'/'||nextopplan.reference)::varchar as path,
                        nextopplan.owner_id
                    from operationplan
                    inner join lateral
                    (select t->>0 reference,
                    (t->>1)::numeric quantity,
                    (t->>2)::numeric as offset from jsonb_array_elements(operationplan.plan->'upstream_opplans') t) t on true
                    inner join operationplan nextopplan on nextopplan.reference = t.reference
                    where operationplan.reference in (select opplan from cte0)
                    union all
                    select cte.level +  1,
                        nextopplan.reference,
                        nextopplan.type,
                        case when nextopplan.type = 'PO' then 'Purchase '||nextopplan.item_id||' @ '||nextopplan.location_id||' from '||nextopplan.supplier_id
                        when nextopplan.type = 'DO' then 'Ship '||nextopplan.item_id||' from '||nextopplan.origin_id||' to '||nextopplan.destination_id
                        else nextopplan.operation_id end,
                        nextopplan.status,
                        nextopplan.item_id,
                        coalesce(nextopplan.location_id, nextopplan.destination_id),
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.startdate,'YYYY-MM-DD hh24:mi:ss') end,
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.enddate,'YYYY-MM-DD hh24:mi:ss') end,
                        case when nextopplan.owner_id is not null then cte.y
						when downstream.offset is null
                        and t.offset = 0
                        and (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) = 0 then t.quantity
                        else
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.y else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        least(t.offset + t.quantity, t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        + (cte.y-cte.x)*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1))
                        else
                        greatest(0, cte.y - coalesce(downstream.offset,0))/coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) end
                        -
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end),
                        nextopplan.quantity,
                        case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end as x,
                        case when nextopplan.owner_id is not null then cte.y
						when downstream.offset is null
                        and t.offset = 0
                        and (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) = 0 then t.quantity
                        else
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.y else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        least(t.offset + t.quantity, t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        + (cte.y-cte.x)*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1))
                        else
                        greatest(0, cte.y - coalesce(downstream.offset,0))/coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) end
                        as y,
                        cte.path||'/'||coalesce(nextopplan.item_id,'')||'/'||nextopplan.reference,
                    nextopplan.owner_id
                    from operationplan
                    inner join cte on operationplan.reference = cte.nextreference
                    inner join lateral
                    (select t->>0 reference,
                    (t->>1)::numeric quantity,
                    (t->>2)::numeric as offset from jsonb_array_elements(operationplan.plan->'upstream_opplans') t) t on true
                    inner join operationplan nextopplan on nextopplan.reference = t.reference
                    left outer join operationplan nextopplan_last_step on nextopplan_last_step.owner_id = nextopplan.reference
					and nextopplan_last_step.operation_id = (select name from operation where owner_id = nextopplan.operation_id order by priority desc limit 1)
                    left outer join lateral
                    (select t->>0 reference,
                    (t->>1)::numeric quantity,
                    (t->>2)::numeric as offset from jsonb_array_elements(nextopplan.plan->'downstream_opplans') t
                    union all
					select t2->>0 reference,
                    (t2->>1)::numeric quantity,
                    (t2->>2)::numeric as offset from jsonb_array_elements(nextopplan_last_step.plan->'downstream_opplans') t2) downstream
                    on downstream.reference = operationplan.reference or downstream.reference = operationplan.owner_id
                    left outer join operationmaterial consuming_om on consuming_om.operation_id = operationplan.operation_id
                        and consuming_om.quantity < 0 and consuming_om.item_id = nextopplan.item_id
                    left outer join operationmaterial producing_om on producing_om.operation_id = operationplan.operation_id
                        and producing_om.quantity > 0 and producing_om.item_id = operationplan.item_id
                    where
                    case when nextopplan.owner_id is not null then cte.y
						when downstream.offset is null
                        and t.offset = 0
                        and (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) = 0 then t.quantity
                        else
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.y else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        least(t.offset + t.quantity, t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        + (cte.y-cte.x)*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1))
                        else
                        greatest(0, cte.y - coalesce(downstream.offset,0))/coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) end
                    -
                    (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end)
                    > 0
                    -- infinite loop security
                    and cte.level < 25
                    and cte.path not like '%%%%/'||nextopplan.reference||'/%%%%'
                    and cte.nextreference != nextopplan.reference
                    and (select count(*) from operation_dependency where operation_id = nextopplan.operation_id) <= 1
                    )
                    select nextreference from cte
                    )
                    select
                    (select due from demand where name = %s),
                    min(operationplan.startdate),
                    max(operationplan.enddate),
                    (sum(case when name is not null then 1 else 0 end)
                    -count(distinct name) != 0)
                    from operationplan
                    where reference in
                    (
                    select nextreference from cte1
                    union all
                    select opplan from cte0
                    )
                    and type != 'STCK'
            """,
            (args[0], args[0]),
        )
        x = cursor.fetchone()
        (due, start, end, requires_grouping) = x
        if not due:
            # This demand is unplanned
            request.report_startdate = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            request.report_enddate = request.report_startdate + timedelta(days=1)
            request.report_bucket = None
            request.report_bucketlist = []
            return
        if not start:
            start = due
        if not end:
            end = due

        # Adjust the horizon
        if due > end:
            end = due
        if due < start:
            start = due
        end += timedelta(days=1)
        start -= timedelta(days=1)
        request.report_startdate = start.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        request.report_enddate = end.replace(hour=0, minute=0, second=0, microsecond=0)
        request.report_bucket = None
        request.report_bucketlist = []
        request.requires_grouping = requires_grouping

    @classmethod
    def query(reportclass, request, basequery):
        # Build the base query
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Get current date and horizon
        horizon = (
            request.report_enddate - request.report_startdate
        ).total_seconds() / 10000
        current = getCurrentDate(request.database)

        # Collect demand due date, all operationplans and loaded resources
        query = """
          with cte as (
          with recursive cte as
                    (
                    select 1 as level,
                        nextopplan.reference as nextreference,
                        nextopplan.type,
                        case when nextopplan.type = 'PO' then 'Purchase '||nextopplan.item_id||' @ '||nextopplan.location_id||' from '||nextopplan.supplier_id
                        when nextopplan.type = 'DO' then 'Ship '||nextopplan.item_id||' from '||nextopplan.origin_id||' to '||nextopplan.destination_id
                        else nextopplan.operation_id end,
                        nextopplan.status,
                        nextopplan.item_id,
                        coalesce(nextopplan.location_id, nextopplan.destination_id),
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.startdate,'YYYY-MM-DD hh24:mi:ss') end,
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.enddate,'YYYY-MM-DD hh24:mi:ss') end,
                        nextopplan.quantity::numeric  as quantity,
                        nextopplan.quantity::numeric as total_quantity,
                        0::numeric as x,
                        0::numeric + nextopplan.quantity as y,
                        (coalesce(nextopplan.item_id,'')||'/'||nextopplan.reference)::varchar as path,
                        nextopplan.owner_id
                    from operationplan nextopplan
                    inner join demand on demand.name = %s
                    inner join lateral
                    (select t->>'opplan' as reference,
                    (t->>'quantity')::numeric as quantity from jsonb_array_elements(demand.plan->'pegging') t) t on true
                    where nextopplan.reference = t.reference
                    union all
                    select cte.level +  1,
                        nextopplan.reference,
                        nextopplan.type,
                        case when nextopplan.type = 'PO' then 'Purchase '||nextopplan.item_id||' @ '||nextopplan.location_id||' from '||nextopplan.supplier_id
                        when nextopplan.type = 'DO' then 'Ship '||nextopplan.item_id||' from '||nextopplan.origin_id||' to '||nextopplan.destination_id
                        else nextopplan.operation_id end,
                        nextopplan.status,
                        nextopplan.item_id,
                        coalesce(nextopplan.location_id, nextopplan.destination_id),
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.startdate,'YYYY-MM-DD hh24:mi:ss') end,
                        case when nextopplan.type = 'STCK' then null else to_char(nextopplan.enddate,'YYYY-MM-DD hh24:mi:ss') end,
                        case when nextopplan.owner_id is not null then cte.y
						when downstream.offset is null
                        and t.offset = 0
                        and (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) = 0 then t.quantity
                        else
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.y else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        least(t.offset + t.quantity, t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        + (cte.y-cte.x)*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1))
                        else
                        greatest(0, cte.y - coalesce(downstream.offset,0))/coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) end
                        -
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end),
                        nextopplan.quantity,
                        case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end as x,
                        case when nextopplan.owner_id is not null then cte.y
						when downstream.offset is null
                        and t.offset = 0
                        and (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) = 0 then t.quantity
                        else
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.y else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        least(t.offset + t.quantity, t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        + (cte.y-cte.x)*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1))
                        else
                        greatest(0, cte.y - coalesce(downstream.offset,0))/coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) end
                        as y,
                        cte.path||'/'||coalesce(nextopplan.item_id,'')||'/'||nextopplan.reference,
                    nextopplan.owner_id
                    from operationplan
                    inner join cte on operationplan.reference = cte.nextreference
                    inner join lateral
                    (select t->>0 reference,
                    (t->>1)::numeric quantity,
                    (t->>2)::numeric as offset from jsonb_array_elements(operationplan.plan->'upstream_opplans') t) t on true
                    inner join operationplan nextopplan on nextopplan.reference = t.reference
                    left outer join operationplan nextopplan_last_step on nextopplan_last_step.owner_id = nextopplan.reference
					and nextopplan_last_step.operation_id = (select name from operation where owner_id = nextopplan.operation_id order by priority desc limit 1)
                    left outer join lateral
                    (select t->>0 reference,
                    (t->>1)::numeric quantity,
                    (t->>2)::numeric as offset from jsonb_array_elements(nextopplan.plan->'downstream_opplans') t
                    union all
					select t2->>0 reference,
                    (t2->>1)::numeric quantity,
                    (t2->>2)::numeric as offset from jsonb_array_elements(nextopplan_last_step.plan->'downstream_opplans') t2) downstream
                    on downstream.reference = operationplan.reference or downstream.reference = operationplan.owner_id
                    left outer join operationmaterial consuming_om on consuming_om.operation_id = operationplan.operation_id
                        and consuming_om.quantity < 0 and consuming_om.item_id = nextopplan.item_id
                    left outer join operationmaterial producing_om on producing_om.operation_id = operationplan.operation_id
                        and producing_om.quantity > 0 and producing_om.item_id = operationplan.item_id
                    where
                    case when nextopplan.owner_id is not null then cte.y
						when downstream.offset is null
                        and t.offset = 0
                        and (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) = 0 then t.quantity
                        else
                        (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.y else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        least(t.offset + t.quantity, t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        + (cte.y-cte.x)*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1))
                        else
                        greatest(0, cte.y - coalesce(downstream.offset,0))/coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end) end
                    -
                    (case when nextopplan.owner_id = cte.nextreference or cte.owner_id = nextopplan.owner_id then cte.x else
                        least( nextopplan.quantity, case when t.offset > 0 then
                        t.offset + cte.x*coalesce(-consuming_om.quantity,1)/coalesce(producing_om.quantity,1)
                        else
                        greatest(0,cte.x - coalesce(downstream.offset,0)) /coalesce(producing_om.quantity,1)*coalesce(-consuming_om.quantity,1)
                        end) end)
                    > 0
                    -- infinite loop security
                    and cte.level < 25
                    and cte.path not like '%%%%/'||nextopplan.reference||'/%%%%'
                    and cte.nextreference != nextopplan.reference
                    and (select count(*) from operation_dependency where operation_id = nextopplan.operation_id) <= 1
                    )
                    select distinct cte.level, cte.nextreference, cte.quantity, cte.path from cte
                    order by path,level desc
          ),
           pegging_0 as (
            select
              min(rownum) as rownum,
              min(due) as due,
              opplan,
              min(lvl) as lvl,
              quantity as required_quantity,
              sum(quantity) as quantity,
              path
            from (select
              row_number() over () as rownum, opplan, due, lvl, quantity, path
            from (select
              due,
              cte.nextreference as opplan,
              cte.level as lvl,
              cte.quantity as quantity,
              cte.path
              from demand
              cross join cte
              where name = %s
              ) d1
              ) d2
            group by opplan, quantity, path
            ),
            pegging as (select
              child.rownum,
              child.due,
              child.opplan,
			  parent.opplan as parent_reference,
              child.lvl,
              child.required_quantity,
              child.quantity,
              child.path
            from pegging_0 child
			left outer join pegging_0 parent
			on parent.lvl = child.lvl -1
			and parent.rownum < child.rownum
			and not exists (select 1 from pegging_0 where lvl = parent.lvl and rownum > parent.rownum
						   and rownum < child.rownum)
		)
          select
            pegging.due,
            operationplan.name,
            pegging.lvl,
            ops.pegged,
            pegging.rownum,
            operationplan.startdate,
            operationplan.enddate,
            operationplan.quantity,
            operationplan.status,
            array_agg(operationplanresource.resource_id) FILTER (WHERE operationplanresource.resource_id is not null),
            operationplan.type,
            case when operationplan.operation_id is not null then 1 else 0 end as show,
            operationplan.color,
            operationplan.reference,
            operationplan.item_id,
            coalesce(operationplan.location_id, operationplan.destination_id),
            operationplan.supplier_id,
            operationplan.origin_id,
            operationplan.criticality,
            operationplan.demand_id,
            extract(epoch from operationplan.delay),
            pegging.required_quantity,
            operationplan.batch,
            item.description,
            pegging.path
          from pegging
          inner join operationplan
            on operationplan.reference = pegging.opplan
          left outer join item
            on operationplan.item_id = item.name
          inner join (
            select name,
			  parent_reference,
              min(rownum) as rownum,
              sum(pegging.quantity) as pegged
            from pegging
            inner join operationplan
              on pegging.opplan = operationplan.reference
            group by operationplan.name, parent_reference
            ) ops
          on operationplan.name = ops.name
		  and pegging.parent_reference is not distinct from ops.parent_reference
          left outer join operationplanresource
            on pegging.opplan = operationplanresource.operationplan_id
          group by
            pegging.due, operationplan.name, pegging.lvl, ops.pegged,
            pegging.rownum, operationplan.startdate, operationplan.enddate, operationplan.quantity,
            operationplan.status,
            operationplan.type,
            case when operationplan.operation_id is not null then 1 else 0 end,
            operationplan.color, operationplan.reference, operationplan.item_id,
            item.description,
            coalesce(operationplan.location_id, operationplan.destination_id),
            operationplan.supplier_id, operationplan.origin_id,
            operationplan.criticality, operationplan.demand_id,
            extract(epoch from operationplan.delay), ops.rownum, pegging.required_quantity,
            pegging.path
          order by pegging.rownum
          """

        # Build the Python result
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(query, baseparams * 2)
                prevrec = None
                parents = {}
                response = []
                for rec in cursor_chunked:
                    if not prevrec or rec[1] != prevrec["operation"]:
                        # Return prev operation
                        if prevrec:
                            if prevrec["depth"] < rec[2]:
                                prevrec["leaf"] = "false"
                            response.append(prevrec)
                        # New operation
                        prevrec = {
                            "id": rec[24],
                            "operation": rec[1],
                            "type": rec[10],
                            "showdrilldown": rec[11],
                            "depth": rec[2],
                            "quantity": str(rec[3]),
                            "item": rec[14],
                            "item__description": rec[23],
                            "due": round(
                                (rec[0] - request.report_startdate).total_seconds()
                                / horizon,
                                3,
                            ),
                            "current": round(
                                (current - request.report_startdate).total_seconds()
                                / horizon,
                                3,
                            ),
                            "parent": parents.get(rec[2] - 1, None)
                            if rec[2] and rec[2] >= 1
                            else None,
                            "leaf": "true",
                            "expanded": "true",
                            "resource": sorted(rec[9]) if rec[9] else None,
                            "required_quantity": str(rec[21]),
                            "operationplans": [
                                {
                                    "operation": rec[1],
                                    "quantity": str(rec[7]),
                                    "x": round(
                                        (
                                            rec[5] - request.report_startdate
                                        ).total_seconds()
                                        / horizon,
                                        3,
                                    ),
                                    "w": max(
                                        50,
                                        round(
                                            (rec[6] - rec[5]).total_seconds() / horizon,
                                            3,
                                        ),
                                    ),
                                    "startdate": str(rec[5]),
                                    "enddate": str(rec[6]),
                                    "status": rec[8],
                                    "reference": rec[13],
                                    "color": round(rec[12])
                                    if rec[12] is not None
                                    else None,
                                    "type": rec[10],
                                    "item": rec[14],
                                    "location": rec[15],
                                    "supplier": rec[16],
                                    "origin": rec[17],
                                    "criticality": round(rec[18]),
                                    "demand": rec[19],
                                    "delay": str(rec[20]),
                                    "required_quantity": str(rec[21]),
                                    "batch": rec[22],
                                    "item__description": rec[23],
                                }
                            ],
                        }
                        parents[rec[2]] = rec[24]
                    elif rec[4] != prevrec["operationplans"][-1]["reference"]:
                        # Extra operationplan for the operation
                        prevrec["operationplans"].append(
                            {
                                "operation": rec[1],
                                "quantity": str(rec[7]),
                                "x": round(
                                    (rec[5] - request.report_startdate).total_seconds()
                                    / horizon,
                                    3,
                                ),
                                "w": round(
                                    (rec[6] - rec[5]).total_seconds() / horizon, 3
                                ),
                                "startdate": str(rec[5]),
                                "enddate": str(rec[6]),
                                "status": rec[8],
                                "reference": rec[13],
                                "color": round(rec[12])
                                if rec[12] is not None
                                else None,
                                "type": rec[10],
                                "item": rec[14],
                                "location": rec[15],
                                "supplier": rec[16],
                                "origin": rec[17],
                                "criticality": round(rec[18]),
                                "demand": rec[19],
                                "delay": str(rec[20]),
                                "required_quantity": str(rec[21]),
                                "batch": rec[22],
                                "item__description": rec[23],
                            }
                        )
                        prevrec["required_quantity"] = float(
                            prevrec["required_quantity"]
                        ) + float(rec[21])
                    elif rec[9] and not rec[9] in prevrec["resource"]:
                        # Extra resource loaded by the operationplan
                        prevrec["resource"] = sorted(prevrec["resource"].append(rec[9]))
                if prevrec:
                    response.append(prevrec)

                # group by operation
                if request.requires_grouping:
                    indexOfOperation = {}
                    updateParent = {}
                    index = 0
                    removed = 0
                    deletedRecords = []
                    for r in response[:]:
                        if r["operation"] not in indexOfOperation:
                            indexOfOperation[r["operation"]] = index - removed
                        else:
                            deletedRecords.append(response.pop(index - removed))
                            removed += 1
                        index += 1

                    for rec in deletedRecords:
                        # store the old and new id
                        if (
                            rec["id"]
                            != response[indexOfOperation[rec["operation"]]]["id"]
                        ):
                            val = response[indexOfOperation[rec["operation"]]]["id"]
                            for i in updateParent:
                                if i in val:
                                    val = val.replace(i, updateParent[i])
                            updateParent[rec["id"]] = val

                        # aggregate the resources:
                        if rec.get("resource"):
                            if (
                                "resource"
                                not in response[indexOfOperation[rec["operation"]]]
                            ):
                                response[indexOfOperation[rec["operation"]]][
                                    "resource"
                                ] = []
                            response[indexOfOperation[rec["operation"]]][
                                "resource"
                            ] = sorted(
                                response[indexOfOperation[rec["operation"]]]["resource"]
                                + [
                                    r
                                    for r in rec["resource"]
                                    if r
                                    not in response[indexOfOperation[rec["operation"]]][
                                        "resource"
                                    ]
                                ]
                            )

                        # aggregate the operationplans:
                        response[indexOfOperation[rec["operation"]]][
                            "operationplans"
                        ] += rec["operationplans"]
                        # remove possible duplicates opplans from list
                        duplicates = 0
                        refdict = {}
                        index2 = 0
                        for i in response[indexOfOperation[rec["operation"]]][
                            "operationplans"
                        ][:]:
                            if i["reference"] not in refdict:
                                refdict[i["reference"]] = index2 - duplicates
                            else:
                                deleted_opplan = response[
                                    indexOfOperation[rec["operation"]]
                                ]["operationplans"].pop(index2 - duplicates)
                                duplicates += 1
                                # update the required_quantity
                                response[indexOfOperation[rec["operation"]]][
                                    "operationplans"
                                ][refdict[i["reference"]]]["required_quantity"] = float(
                                    response[indexOfOperation[rec["operation"]]][
                                        "operationplans"
                                    ][refdict[i["reference"]]]["required_quantity"]
                                ) + float(
                                    deleted_opplan["required_quantity"]
                                )
                            index2 += 1

                        # update the required_quantity at record level
                        response[indexOfOperation[rec["operation"]]][
                            "required_quantity"
                        ] = sum(
                            float(opplan["required_quantity"])
                            for opplan in response[indexOfOperation[rec["operation"]]][
                                "operationplans"
                            ]
                        )

                    # A final loop to update the ids
                    for r in response:
                        for i in reversed(list(updateParent.keys())):
                            if i in r["id"] or (
                                r.get("parent") and i in r.get("parent")
                            ):
                                r["id"] = r["id"].replace(i, updateParent[i])
                                if "parent" in r:
                                    r["parent"] = r["parent"].replace(
                                        i, updateParent[i]
                                    )

                for r in sorted(response, key=lambda d: d["id"]):
                    yield r
