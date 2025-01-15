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

import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections, transaction
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.utils.text import capfirst

from freppledb.boot import getAttributeFields
from freppledb.input.models import Demand, Item, Location, Customer
from freppledb.input.models import ManufacturingOrder, PurchaseOrder, DistributionOrder
from freppledb.common.report import (
    GridPivot,
    GridFieldText,
    GridFieldNumber,
    GridFieldInteger,
    getCurrentDate,
)
from freppledb.common.report import GridFieldCurrency, GridFieldLastModified


class OverviewReportWithoutForecast(GridPivot):
    """
    A report showing the independent demand for each item.
    """

    template = "output/demand.html"
    title = _("Demand report")
    post_title = _("plan")
    basequeryset = Item.objects.all()
    model = Item
    permissions = (("view_demand_report", "Can view demand report"),)
    rows = (
        GridFieldText(
            "item",
            title=_("item"),
            key=True,
            editable=False,
            field_name="name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/item"',
            initially_hidden=True,
        ),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldNumber("volume", title=_("volume"), initially_hidden=True),
        GridFieldNumber("weight", title=_("weight"), initially_hidden=True),
        GridFieldText("uom", title=_("unit of measure"), initially_hidden=True),
        GridFieldInteger(
            "periodofcover", title=_("period of cover"), initially_hidden=True
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified", initially_hidden=True),
    )
    crosses = (
        ("demand", {"title": _("sales orders")}),
        ("supply", {"title": _("supply")}),
        ("backlog", {"title": _("backlog")}),
        ("reasons", {"title": _("reasons"), "visible": False}),
    )
    help_url = "user-interface/plan-analysis/demand-report.html"

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom item attributes
            for f in getAttributeFields(Item, initially_hidden=False):
                f.editable = False
                reportclass.rows += (f,)
                reportclass.attr_sql += "parent.%s, " % f.name.split("__")[-1]

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plan"
            return {
                "title": force_str(Item._meta.verbose_name) + " " + args[0],
                "post_title": _("plan"),
                "model": Item,
            }
        else:
            return {}

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Assure the item hierarchy is up to date
        Item.rebuildHierarchy(database=basequery.db)

        # Execute a query to get the backlog at the start of the horizon
        startbacklogdict = {}
        query = """
          select name, sum(qty) from
            (
            select item.name, sum(demand.quantity) qty from (%s) item
            inner join item child on child.lft between item.lft and item.rght
            inner join demand on demand.item_id = child.name
            and demand.status in ('open','quote')
            and due < %%s
            group by item.name
            union all
            select item.name, sum(operationplanmaterial.quantity) qty
            from (%s) item
            inner join item child on child.lft between item.lft and item.rght
            inner join operationplanmaterial on operationplanmaterial.item_id = child.name
            inner join operationplan on operationplan.reference = operationplanmaterial.operationplan_id
              and operationplan.demand_id is not null
              and operationplan.enddate < %%s
            group by item.name
            ) t
            group by name
        """ % (
            basesql,
            basesql,
        )
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    baseparams
                    + (request.report_startdate,)
                    + baseparams
                    + (request.report_startdate,),
                )
                for row in cursor_chunked:
                    if row[0]:
                        startbacklogdict[row[0]] = max(float(row[1]), 0)

        # Execute the query
        query = """
          select
          parent.name, parent.description, parent.category, parent.subcategory,
          parent.owner_id, parent.cost, parent.volume, parent.weight, parent.uom, parent.periodofcover, parent.source, parent.lastmodified,
          %s
          d.bucket,
          d.startdate,
          d.enddate,
          sum(coalesce((
            select sum(quantity)
            from demand
            inner join item child on child.lft between parent.lft and parent.rght
            where demand.item_id = child.name
            and status in ('open','quote')
            and due >= greatest(%%s,d.startdate)
            and due < d.enddate
            ),0)) orders,
          sum(coalesce((
            select sum(operationplan.quantity)
            from operationplan
            inner join item child on child.lft between parent.lft and parent.rght
            where operationplan.item_id = child.name
            and operationplan.demand_id is not null
            and operationplan.enddate >= greatest(%%s,d.startdate)
            and operationplan.enddate < d.enddate
            ),0)) planned,
          (select json_agg(json_build_array(f1,f2)) from
            (select distinct out_constraint.name as f1, out_constraint.owner as f2
            from out_constraint
            inner join item child
              on child.lft between parent.lft and parent.rght
            inner join operationplan
              on operationplan.demand_id = out_constraint.demand
              and operationplan.due is not null
            and out_constraint.item = child.name
            and operationplan.enddate >= greatest(%%s,d.startdate)
            and operationplan.due < d.enddate
            limit 20
            ) cte_reasons
          ) reasons
          from (%s) parent
          cross join (
                       select name as bucket, startdate, enddate
                       from common_bucketdetail
                       where bucket_id = %%s and enddate > %%s and startdate < %%s
                       ) d
          group by
            parent.name, parent.description, parent.category, parent.subcategory,
            parent.owner_id, parent.cost, parent.volume, parent.weight, parent.uom, parent.periodofcover,
            parent.source, parent.lastmodified, parent.lft, parent.rght,
            %s
            d.bucket, d.startdate, d.enddate
          order by %s, d.startdate
        """ % (
            reportclass.attr_sql,
            basesql,
            reportclass.attr_sql,
            sortsql,
        )

        # Build the python result
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    (request.report_startdate,) * 3  # orders + planned + constraints
                    + baseparams  # orders planned
                    + (
                        request.report_bucket,
                        request.report_startdate,
                        request.report_enddate,
                    ),  # buckets
                )
                previtem = None
                itemattributefields = getAttributeFields(Item)
                for row in cursor_chunked:
                    numfields = len(row)
                    if row[0] != previtem:
                        backlog = startbacklogdict.get(row[0], 0)
                        previtem = row[0]
                    backlog += float(row[numfields - 3]) - float(row[numfields - 2])
                    res = {
                        "item": row[0],
                        "description": row[1],
                        "category": row[2],
                        "subcategory": row[3],
                        "owner": row[4],
                        "cost": row[5],
                        "volume": row[6],
                        "weight": row[7],
                        "uom": row[8],
                        "periodofcover": row[9],
                        "source": row[10],
                        "lastmodified": row[11],
                        "bucket": row[numfields - 6],
                        "startdate": row[numfields - 5].date(),
                        "enddate": row[numfields - 4].date(),
                        "demand": row[numfields - 3],
                        "supply": row[numfields - 2],
                        "reasons": json.dumps(row[numfields - 1]),
                        "backlog": max(backlog or 0, 0),
                    }
                    idx = 12
                    for f in itemattributefields:
                        res[f.field_name] = row[idx]
                        idx += 1
                    yield res


class OverviewReportWithForecast(GridPivot):
    """
    A report showing the independent demand for each item.
    """

    template = "output/demand_forecast.html"
    title = _("Demand report")
    basequeryset = Item.objects.all()
    model = Item
    permissions = (("view_demand_report", "Can view demand report"),)
    rows = (
        GridFieldText(
            "item",
            title=_("item"),
            key=True,
            editable=False,
            field_name="name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/item"',
            initially_hidden=True,
        ),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified", initially_hidden=True),
    )
    crosses = (
        ("forecast", {"title": _("net forecast"), "initially_hidden": True}),
        ("orders", {"title": _("sales orders"), "initially_hidden": True}),
        ("demand", {"title": _("total demand")}),
        ("supply", {"title": _("supply")}),
        (
            "backlog_orders",
            {"title": _("sales order backlog"), "initially_hidden": True},
        ),
        (
            "backlog_forecast",
            {"title": _("forecast backlog"), "initially_hidden": True},
        ),
        ("backlog", {"title": _("total backlog")}),
        ("reasons", {"title": _("reasons"), "visible": False}),
    )
    help_url = "user-interface/plan-analysis/demand-report.html"

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom item attributes
            for f in getAttributeFields(Item, initially_hidden=False):
                f.editable = False
                reportclass.rows += (f,)
                reportclass.attr_sql += "parent.%s, " % f.name.split("__")[-1]

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plan"
            return {
                "title": capfirst(force_str(Item._meta.verbose_name) + " " + args[0]),
                "post_title": _("plan"),
            }
        else:
            return {}

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Assure the hierarchies are up to date
        Item.createRootObject(database=basequery.db)
        Location.createRootObject(database=basequery.db)
        Customer.createRootObject(database=basequery.db)

        current = getCurrentDate(basequery.db, lastplan=True)

        # Execute a query to get the backlog at the start of the horizon
        startbacklogdict = {}

        # code assumes no max lateness is set to calculate the backlog
        query = """
          select name, sum(qty_orders), sum(qty_forecast) from
          (
          select item.name, sum(demand.quantity) qty_orders, 0::numeric qty_forecast
          from (%s) item
          inner join item child on child.lft between item.lft and item.rght
          inner join demand on demand.item_id = child.name and demand.status in ('open','quote') and due < %%s
          group by item.name
          union all
          select item.name, 0::numeric qty_orders, coalesce(sum(forecastplan.forecastnet),0) qty_forecast
          from forecastplan
          left outer join common_parameter cp on cp.name = 'forecast.DueWithinBucket'
          inner join (%s) item on forecastplan.item_id = item.name
          where forecastplan.location_id = (select name from location where lvl=0)
          and forecastplan.customer_id = (select name from customer where lvl=0)
          and case when coalesce(cp.value, 'start') = 'start' then forecastplan.startdate
                   when coalesce(cp.value, 'start') = 'end' then forecastplan.enddate - interval '1 second'
                   when coalesce(cp.value, 'start') = 'middle' then forecastplan.startdate + age(forecastplan.enddate, forecastplan.startdate)/2 end < %%s
          and forecastplan.enddate >= %%s
          group by item.name
          union all
          select item.name,
            sum(case when operationplan.demand_id is not null then operationplanmaterial.quantity end) qty_orders,
            sum(case when operationplan.forecast is not null then operationplanmaterial.quantity end) qty_forecast
          from (%s) item
          inner join item child on child.lft between item.lft and item.rght
          inner join operationplanmaterial on operationplanmaterial.item_id = child.name
          inner join operationplan on operationplan.reference = operationplanmaterial.operationplan_id
            and (operationplan.demand_id is not null or operationplan.forecast is not null)
            and operationplan.enddate < %%s
          group by item.name
          ) t
          group by name
        """ % (
            basesql,
            basesql,
            basesql,
        )
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    baseparams
                    + (request.report_startdate,)
                    + baseparams
                    + (request.report_startdate,)
                    + (current,)
                    + baseparams
                    + (request.report_startdate,),
                )
                for row in cursor_chunked:
                    if row[0]:
                        startbacklogdict[row[0]] = (
                            max(float(row[1]), 0),
                            max(float(row[2]), 0),
                        )

        # Execute the query
        query = """
          select
          parent.name, parent.description, parent.category, parent.subcategory,
          parent.owner_id, parent.cost, parent.source, parent.lastmodified,
          %s
          d.bucket,
          d.startdate,
          d.enddate,
          sum(coalesce((
            select sum(quantity)
            from demand
            inner join item child on child.lft between parent.lft and parent.rght
            where demand.item_id = child.name
            and status in ('open','quote')
            and due >= greatest(%%s,d.startdate)
            and due < d.enddate
            ),0)) orders,
          (select coalesce(sum(operationplan.quantity),0)
            from operationplan
            inner join item child on child.lft between parent.lft and parent.rght
            where operationplan.demand_id is not null
            and operationplan.item_id = child.name
            and operationplan.enddate >= greatest(%%s,d.startdate)
            and operationplan.enddate < d.enddate
            ) planned_orders,
          (select coalesce(sum(operationplan.quantity),0)
            from operationplan
            inner join item child on child.lft between parent.lft and parent.rght
            where operationplan.forecast is not null
            and operationplan.item_id = child.name
            and operationplan.enddate >= greatest(%%s,d.startdate)
            and operationplan.enddate < d.enddate
            ) planned_forecast,
          (select json_agg(json_build_array(f1,f2)) from
            (select distinct out_constraint.name as f1, out_constraint.owner as f2
            from out_constraint
            inner join item child
              on child.lft between parent.lft and parent.rght
              and out_constraint.item = child.name
            inner join operationplan
              on (operationplan.demand_id = out_constraint.demand
               or operationplan.forecast = out_constraint.forecast)
              and operationplan.enddate >= greatest(%%s,d.startdate)
              and operationplan.due < d.enddate
            limit 20
            ) cte_reasons
            ) reasons,
          coalesce((
            select sum(forecastplan.forecastnet)
            from forecastplan
            left outer join common_parameter cp on cp.name = 'forecast.DueWithinBucket'
            where forecastplan.item_id = parent.name
            and forecastplan.location_id = (select name from location where lvl=0)
            and forecastplan.customer_id = (select name from customer where lvl=0)
            and case when coalesce(cp.value, 'start') = 'start' then forecastplan.startdate
                     when coalesce(cp.value, 'start') = 'end' then forecastplan.enddate - interval '1 second'
                     when coalesce(cp.value, 'start') = 'middle' then forecastplan.startdate + age(forecastplan.enddate, forecastplan.startdate)/2 end >= greatest(%%s,d.startdate)
            and case when coalesce(cp.value, 'start') = 'start' then forecastplan.startdate
                     when coalesce(cp.value, 'start') = 'end' then forecastplan.enddate - interval '1 second'
                     when coalesce(cp.value, 'start') = 'middle' then forecastplan.startdate + age(forecastplan.enddate, forecastplan.startdate)/2 end < d.enddate
            and forecastplan.enddate >= %%s
            ),0) forecast
          from (%s) parent
          cross join (
                       select name as bucket, startdate, enddate
                       from common_bucketdetail
                       where bucket_id = %%s and enddate > %%s and startdate < %%s
                       ) d
          group by
            parent.name, parent.description, parent.category, parent.subcategory,
            parent.owner_id, parent.cost, parent.source, parent.lastmodified, parent.lft, parent.rght,
            %s
            d.bucket, d.startdate, d.enddate
          order by %s, d.startdate
        """ % (
            reportclass.attr_sql,
            basesql,
            reportclass.attr_sql,
            sortsql,
        )

        # Build the python result
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    (
                        request.report_startdate,  # orders
                        request.report_startdate,  # planned orders
                        request.report_startdate,  # planned forecast
                        request.report_startdate,  # reasons
                        request.report_startdate,  # forecast
                        current,
                    )
                    + baseparams
                    + (
                        request.report_bucket,
                        request.report_startdate,
                        request.report_enddate,  # buckets
                    ),
                )
                previtem = None
                itemattributefields = getAttributeFields(Item)
                for row in cursor_chunked:
                    numfields = len(row)
                    if row[0] != previtem:
                        (backlog_o, backlog_f) = startbacklogdict.get(row[0], (0, 0))
                        previtem = row[0]
                    backlog_o += float(row[numfields - 5] - row[numfields - 4])
                    backlog_f += float(row[numfields - 1] - row[numfields - 3])
                    res = {
                        "item": row[0],
                        "description": row[1],
                        "category": row[2],
                        "subcategory": row[3],
                        "owner": row[4],
                        "cost": row[5],
                        "source": row[6],
                        "lastmodified": row[7],
                        "bucket": row[numfields - 8],
                        "startdate": row[numfields - 7].date(),
                        "enddate": row[numfields - 6].date(),
                        "orders": row[numfields - 5],
                        "demand": row[numfields - 5] + row[numfields - 1],
                        "supply": row[numfields - 4] + row[numfields - 3],
                        "reasons": json.dumps(row[numfields - 2]),
                        "forecast": row[numfields - 1],
                        "backlog_orders": max(backlog_o or 0, 0),
                        "backlog_forecast": max(backlog_f or 0, 0),
                        "backlog": max(backlog_o or 0, 0) + max(backlog_f or 0, 0),
                    }
                    idx = 8
                    for f in itemattributefields:
                        res[f.field_name] = row[idx]
                        idx += 1
                    yield res


if "freppledb.forecast" in settings.INSTALLED_APPS:

    class OverviewReport(OverviewReportWithForecast):
        pass

else:

    class OverviewReport(OverviewReportWithoutForecast):
        pass


def OperationPlans(request):
    if (
        request.method != "GET"
        or request.headers.get("x-requested-with") != "XMLHttpRequest"
    ):
        return HttpResponseBadRequest("Only ajax get requests allowed")
    if not request.user.has_perm("auth.view_demand_report"):
        return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

    # Collect list of selected sales orders
    so_list = request.GET.getlist("demand")

    # Collect operationplans associated with the sales order(s)
    result = {
        "PO": [],
        "DO": [],
        "MO": [],
    }
    with connections[request.database].cursor() as cursor:
        cursor.execute(
            """
            select operationplan.reference,
            operationplan.type,
            operationplan.item_id,
            case when operationplan.type = 'DO' then operationplan.destination_id
            else operationplan.location_id end as location_id,
            operationplan.origin_id,
            operationplan.startdate,
            operationplan.enddate,
            operationplan.quantity,
            operationplan.quantity * item.cost as value,
            operationplan.status,
            case when operationplan.type = 'PO' then operationplan.supplier_id else operationplan.operation_id end
            from operationplan
            inner join item on item.name = operationplan.item_id and item.source is not null
            where operationplan.plan->'pegging' ?| %s
            and operationplan.type in ('PO','DO','MO')
            and operationplan.status in ('proposed', 'approved')
            and operationplan.owner_id is null
            and case when operationplan.type = 'PO'
			then exists (select 1 from supplier where operationplan.supplier_id = supplier.name and supplier.source is not null)
			when operationplan.type = 'MO'
			then exists (select 1 from operation where operationplan.operation_id = operation.name and operation.source is not null)
			when operationplan.type = 'DO'
			then exists (select 1 from location where operationplan.origin_id = location.name and location.source is not null)
			and exists (select 1 from location where operationplan.destination_id = location.name and location.source is not null)
			else true end = true
            order by operationplan.type, operationplan.startdate
            """,
            (so_list,),
        )

        po_ok = request.user.has_perm("input.change_purchaseorder")
        do_ok = request.user.has_perm("input.change_distributionorder")
        mo_ok = request.user.has_perm("input.change_manufacturingorder")

        for i in cursor:

            if i[1] == "MO" and not mo_ok:
                continue

            if i[1] == "PO" and not po_ok:
                continue

            if i[1] == "DO" and not do_ok:
                continue

            l = [
                # ["fieldname", value, hidden, value type]
                # front-end relies on the fact that the reference is the first of the list
                [_("reference"), i[0], 0, "text"],
                [_("item"), i[2], 0, "text"],
                [_("destination") if i[1] == "DO" else _("location"), i[3], 0, "text"],
                [
                    (
                        _("start date")
                        if i[1] == "MO"
                        else (
                            _("ordering date") if i[1] == "PO" else _("shipping date")
                        )
                    ),
                    i[5],
                    0,
                    "date",
                ],
                [_("end date") if i[1] == "MO" else _("receipt date"), i[6], 0, "date"],
                [_("quantity"), i[7], 0, "number"],
                [_("value"), i[8], 0, "number"],
                [_("status"), _(i[9]), 0, "text"],
            ]
            if i[1] == "DO":
                l.insert(
                    2,
                    [_("origin"), i[4], 0],
                )
            elif i[1] == "MO":
                l.insert(3, [_("operation"), i[10], 0])
            elif i[1] == "PO":
                l.insert(3, [_("supplier"), i[10], 0])

            result[i[1]].append(l)
    return JsonResponse(result)
