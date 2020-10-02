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
from dateutil.parser import parse

from django.db import connections
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

from freppledb.input.models import Demand
from freppledb.common.report import GridReport, GridFieldText, GridFieldNumber
from freppledb.common.models import Parameter


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
    heightmargin = 87
    help_url = "user-interface/plan-analysis/demand-gantt-report.html"
    rows = (
        GridFieldText("depth", title=_("depth"), editable=False, sortable=False),
        GridFieldText(
            "operation",
            title=_("operation"),
            editable=False,
            sortable=False,
            key=True,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "type", title=_("type"), editable=False, sortable=False, width=100
        ),
        GridFieldText(
            "item",
            title=_("item"),
            formatter="item",
            editable=False,
            sortable=False,
            initially_hidden=True,
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
            field_name="quantity",
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
                "title": force_text(Demand._meta.verbose_name) + " " + args[0],
                "post_title": _("plan"),
            }
        else:
            return {}

    @classmethod
    def getBuckets(reportclass, request, *args, **kwargs):
        # Get the earliest and latest operationplan, and the demand due date
        cursor = connections[request.database].cursor()
        cursor.execute(
            """
            with dmd as (
                select
                  due,
                  cast(jsonb_array_elements(plan->'pegging')->>'opplan' as varchar) opplan
                from demand
                where name = %s
                )
            select min(dmd.due), min(startdate), max(enddate)
            from dmd
            inner join operationplan
            on dmd.opplan = operationplan.reference
            and type <> 'STCK'
            """,
            (args[0]),
        )
        x = cursor.fetchone()
        (due, start, end) = x
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
        try:
            current = parse(
                Parameter.objects.using(request.database).get(name="currentdate").value
            )
        except Exception:
            current = datetime.now()
            current = current.replace(microsecond=0)

        # Collect demand due date, all operationplans and loaded resources
        query = """
          with pegging as (
            select
              min(rownum) as rownum,
              min(due) as due,
              opplan,
              min(lvl) as lvl,
              quantity as required_quantity,
              sum(quantity) as quantity
            from (select
              row_number() over () as rownum, opplan, due, lvl, quantity
            from (select
              due,
              cast(jsonb_array_elements(plan->'pegging')->>'opplan' as varchar) as opplan,
              cast(jsonb_array_elements(plan->'pegging')->>'level' as integer) as lvl,
              cast(jsonb_array_elements(plan->'pegging')->>'quantity' as numeric) as quantity
              from demand
              where name = %s
              ) d1
              ) d2
            group by opplan, quantity
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
            item.description
          from pegging
          inner join operationplan
            on operationplan.reference = pegging.opplan
          left outer join item
            on operationplan.item_id = item.name
          inner join (
            select name,
              min(rownum) as rownum,
              sum(pegging.quantity) as pegged
            from pegging
            inner join operationplan
              on pegging.opplan = operationplan.reference
            group by operationplan.name
            ) ops
          on operationplan.name = ops.name
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
            extract(epoch from operationplan.delay), ops.rownum, pegging.required_quantity
          order by ops.rownum, pegging.rownum
          """

        # Build the Python result
        with connections[request.database].chunked_cursor() as cursor_chunked:
            cursor_chunked.execute(query, baseparams)
            prevrec = None
            parents = {}
            for rec in cursor_chunked:
                print(rec)
                if not prevrec or rec[1] != prevrec["operation"]:
                    # Return prev operation
                    if prevrec:
                        if prevrec["depth"] < rec[2]:
                            prevrec["leaf"] = "false"
                        yield prevrec
                    # New operation
                    prevrec = {
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
                        "resource": rec[9],
                        "operationplans": [
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
                        ],
                    }
                    parents[rec[2]] = rec[1]
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
                            "w": round((rec[6] - rec[5]).total_seconds() / horizon, 3),
                            "startdate": str(rec[5]),
                            "enddate": str(rec[6]),
                            "status": rec[8],
                            "reference": rec[13],
                            "color": round(rec[12]) if rec[12] is not None else None,
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
                elif rec[9] and not rec[9] in prevrec["resource"]:
                    # Extra resource loaded by the operationplan
                    prevrec["resource"].append(rec[9])
            if prevrec:
                yield prevrec
