#
# Copyright (C) 2007-2013 by frePPLe bv
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
        GridFieldNumber(
            "quantity_proposed",
            title=_("required quantity proposed"),
            field_name="required_quantity_proposed",
            editable=False,
            sortable=False,
            initially_hidden=True,
        ),
        GridFieldNumber(
            "quantity_confirmed",
            title=_("required quantity confirmed"),
            field_name="required_quantity_confirmed",
            editable=False,
            sortable=False,
            initially_hidden=True,
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
            with cte as (
                with recursive cte as
                    (
                        select 1 as level,
                        (coalesce(operationplan.item_id,'')||'/'||operationplan.reference)::varchar as path,
                        operationplan.reference::text as reference,
                        0::numeric as pegged_x,
                        operationplan.quantity::numeric as pegged_y
                        from operationplan
                        inner join demand on demand.name = %s
                            inner join lateral
                            (select t->>'opplan' as reference,
                            (t->>'quantity')::numeric as quantity from jsonb_array_elements(demand.plan->'pegging') t) t on true
                            where operationplan.reference = t.reference
                        union all
                        select cte.level+1,
                        cte.path||'/'||coalesce(upstream_opplan.item_id,'')||'/'||upstream_opplan.reference,
                        t1.upstream_reference::text,
                        greatest(t1.x, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x)) as pegged_x,
                        least(t1.y, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x) + (cte.pegged_y-cte.pegged_x)*(t1.y-t1.x)/(t2.y-t2.x)) as pegged_y
                        from operationplan
                        inner join cte on cte.reference = operationplan.reference
                        inner join lateral
                        (select t->>0 upstream_reference,
                        (t->>1)::numeric + (t->>2)::numeric as y,
                        (t->>2)::numeric as x from jsonb_array_elements(operationplan.plan->'upstream_opplans') t) t1 on true
                        inner join operationplan upstream_opplan on upstream_opplan.reference = t1.upstream_reference
                        inner join lateral
                        (select t->>0 downstream_reference,
                        (t->>1)::numeric+(t->>2)::numeric as y,
                        (t->>2)::numeric as x from jsonb_array_elements(upstream_opplan.plan->'downstream_opplans') t) t2
                            on t2.downstream_reference = operationplan.reference and numrange(t2.x,t2.y) && numrange(cte.pegged_x,cte.pegged_y)
                    )
                select reference from cte
                where level < 25
                order by path,level desc
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
                    select reference from cte
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
        end += timedelta(days=2)
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

        # pos1 is the position in the list l of the last suboperation
        # pos2 is the id==position in the list of the routing
        # id1 < id2
        # swap will move the routing in front of its subops and update the depth and parent
        # of its suboperations
        def swap(l: list, pos1, pos2):

            # store the depth
            depth = l[pos1]["depth"]

            # move the routing in front of the first suboperation
            l.insert(pos1, l.pop(pos2))
            # give to the routing the parent/depth of the last subop
            l[pos1]["parent"] = l[pos1 + 1]["parent"]
            l[pos1]["depth"] = l[pos1 + 1]["depth"]
            # iterate over the suboperations
            i = pos1 + 1
            while i <= pos2:
                l[i]["parent"] = l[pos1]["id"]
                l[i]["depth"] = depth + 1
                l[i]["leaf"] = "true"
                i += 1

        # swap_mo_wo will move a routing operation before its suboperations
        # in the delivery plan
        def swap_mo_wo(l: list):
            visited = []
            owner = None
            counter = 0
            for r in l:
                if owner and owner[0] in [l["reference"] for l in r["operationplans"]]:
                    # ...and now we found the owner, let's make the swap
                    swap(l, owner[2], counter)
                    # we need to reset the variables as we may find other routings in the path
                    owner = None
                    visited.clear()
                if not owner and r["owner"] and r["owner"] not in visited:
                    # We found a suboperation before its owner...
                    owner = (r["owner"], r["id"], counter)
                visited.append(r["id"])
                counter += 1
            return l

        # Build the base query
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Get current date and horizon
        horizon = (
            request.report_enddate - request.report_startdate
        ).total_seconds() / 10000
        current = getCurrentDate(request.database, lastplan=True)

        # Collect demand due date, all operationplans and loaded resources
        query = """
          with cte as (
                with recursive cte as
                (
                select 1 as level,
                (coalesce(operationplan.item_id,'')||'/'||operationplan.reference)::varchar as path,
                operationplan.reference::text,
                0::numeric as pegged_x,
                operationplan.quantity::numeric as pegged_y,
                operationplan.owner_id
                from operationplan
                inner join demand on demand.name = %s
                    inner join lateral
                    (select t->>'opplan' as reference,
                    (t->>'quantity')::numeric as quantity from jsonb_array_elements(demand.plan->'pegging') t) t on true
                    where operationplan.reference = t.reference
                union all
                select case when upstream_opplan.owner_id = cte.owner_id then cte.level else cte.level+1 end,
                cte.path||'/'||coalesce(upstream_opplan.item_id,'')||'/'||upstream_opplan.reference,
                t1.upstream_reference::text,
                greatest(t1.x, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x)) as pegged_x,
                least(t1.y, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x) + (cte.pegged_y-cte.pegged_x)*(t1.y-t1.x)/(t2.y-t2.x)) as pegged_y,
                upstream_opplan.owner_id
                from operationplan
                inner join cte on cte.reference = operationplan.reference
                inner join lateral
                (select t->>0 upstream_reference,
                (t->>1)::numeric + (t->>2)::numeric as y,
                (t->>2)::numeric as x from jsonb_array_elements(operationplan.plan->'upstream_opplans') t) t1 on true
                inner join operationplan upstream_opplan on upstream_opplan.reference = t1.upstream_reference
                inner join lateral
                (select t->>0 downstream_reference,
                (t->>1)::numeric+(t->>2)::numeric as y,
                (t->>2)::numeric as x from jsonb_array_elements(upstream_opplan.plan->'downstream_opplans') t) t2
                    on t2.downstream_reference = operationplan.reference and numrange(t2.x,t2.y) && numrange(cte.pegged_x,cte.pegged_y)
                )
                select level, reference, (pegged_y-pegged_x) as quantity, path from cte
                where level < 25
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
              cte.reference as opplan,
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
            pegging.due, --0
            operationplan.name,
            pegging.lvl,
            ops.pegged,
            pegging.rownum,
            operationplan.startdate,
            operationplan.enddate,
            operationplan.quantity,
            operationplan.status,
            array_agg(operationplanresource.resource_id) FILTER (WHERE operationplanresource.resource_id is not null),
            operationplan.type, --10
            case when operationplan.operation_id is not null then 1 else 0 end as show,
            operationplan.color,
            operationplan.reference,
            operationplan.item_id,
            coalesce(operationplan.location_id, operationplan.destination_id),
            operationplan.supplier_id,
            operationplan.origin_id,
            operationplan.criticality,
            operationplan.demand_id,
            extract(epoch from operationplan.delay), -- 20
            pegging.required_quantity,
            operationplan.batch,
            item.description,
            pegging.path,
            case when operationplan.status = 'proposed' then pegging.required_quantity else 0 end as required_quantity_proposed, -- 25
            case when operationplan.status in ('confirmed','approved','completed','closed') then pegging.required_quantity else 0 end as required_quantity_confirmed, --26
            operationplan.owner_id --27
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
                            "parent": (
                                parents.get(rec[2] - 1, None)
                                if rec[2] and rec[2] >= 1
                                else None
                            ),
                            "leaf": "true",
                            "owner": rec[27],
                            "expanded": "true",
                            "resource": sorted(rec[9]) if rec[9] else None,
                            "required_quantity": rec[21],
                            "required_quantity_proposed": rec[25],
                            "required_quantity_confirmed": rec[26],
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
                                    "color": (
                                        round(rec[12]) if rec[12] is not None else None
                                    ),
                                    "type": rec[10],
                                    "item": rec[14],
                                    "location": rec[15],
                                    "supplier": rec[16],
                                    "origin": rec[17],
                                    "criticality": round(rec[18]),
                                    "demand": rec[19],
                                    "delay": str(rec[20]),
                                    "required_quantity": float(rec[21]),
                                    "required_quantity_proposed": float(rec[25]),
                                    "required_quantity_confirmed": float(rec[26]),
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
                                "color": (
                                    round(rec[12]) if rec[12] is not None else None
                                ),
                                "type": rec[10],
                                "item": rec[14],
                                "location": rec[15],
                                "supplier": rec[16],
                                "origin": rec[17],
                                "criticality": round(rec[18]),
                                "demand": rec[19],
                                "delay": str(rec[20]),
                                "required_quantity": float(rec[21]),
                                "required_quantity_proposed": float(rec[25]),
                                "required_quantity_confirmed": float(rec[26]),
                                "batch": rec[22],
                                "item__description": rec[23],
                            }
                        )
                        prevrec["required_quantity"] = float(
                            prevrec["required_quantity"]
                        ) + float(rec[21])
                        prevrec["required_quantity_proposed"] = float(
                            prevrec["required_quantity_proposed"]
                        ) + float(rec[25])
                        prevrec["required_quantity_confirmed"] = float(
                            prevrec["required_quantity_confirmed"]
                        ) + float(rec[26])
                    elif rec[9] and not rec[9] in prevrec["resource"]:
                        # Extra resource loaded by the operationplan
                        prevrec["resource"] = sorted(prevrec["resource"].append(rec[9]))
                if prevrec:
                    response.append(prevrec)

                # group by operation
                if getattr(request, "requires_grouping", False):
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
                            response[indexOfOperation[rec["operation"]]]["resource"] = (
                                sorted(
                                    response[indexOfOperation[rec["operation"]]][
                                        "resource"
                                    ]
                                    + [
                                        r
                                        for r in rec["resource"]
                                        if r
                                        not in response[
                                            indexOfOperation[rec["operation"]]
                                        ]["resource"]
                                    ]
                                )
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
                                for st in [
                                    "required_quantity",
                                    "required_quantity_proposed",
                                    "required_quantity_confirmed",
                                ]:
                                    response[indexOfOperation[rec["operation"]]][
                                        "operationplans"
                                    ][refdict[i["reference"]]][st] = float(
                                        response[indexOfOperation[rec["operation"]]][
                                            "operationplans"
                                        ][refdict[i["reference"]]][st]
                                    ) + float(
                                        deleted_opplan[st]
                                    )
                            index2 += 1

                        # update the required_quantity at record level
                        for st in [
                            "required_quantity",
                            "required_quantity_proposed",
                            "required_quantity_confirmed",
                        ]:
                            response[indexOfOperation[rec["operation"]]][st] = sum(
                                float(opplan[st])
                                for opplan in response[
                                    indexOfOperation[rec["operation"]]
                                ]["operationplans"]
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

                # The report is being downloaded, adjust the output
                if request.GET.get("format", None) in [
                    "spreadsheetlist",
                    "spreadsheettable",
                    "spreadsheet",
                    "csvlist",
                    "csvtable",
                    "csv",
                ]:
                    for r in sorted(response, key=lambda d: d["id"]):
                        r["operationplans"] = [
                            "reference=%s start=%s end=%s"
                            % (p["reference"], p["startdate"], p["enddate"])
                            for p in r["operationplans"]
                        ]
                        yield r
                else:
                    # swap_mo_wo is a post-processing step to move a routing operation
                    # before its suboperations
                    for r in swap_mo_wo(sorted(response, key=lambda d: d["id"])):
                        yield r
