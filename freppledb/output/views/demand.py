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
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str

from freppledb.boot import getAttributeFields
from freppledb.input.models import Demand, Item
from freppledb.input.models import ManufacturingOrder, PurchaseOrder, DistributionOrder
from freppledb.common.report import (
    GridPivot,
    GridFieldText,
    GridFieldNumber,
    GridFieldInteger,
)
from freppledb.common.report import GridFieldCurrency, GridFieldLastModified


class OverviewReport(GridPivot):
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
            and (
              out_constraint.name not in ('before current', 'before fence')
              or out_constraint.enddate > d.enddate
              )
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


@staff_member_required
def OperationPlans(request):
    # Check permissions
    if (
        request.method != "GET"
        or request.headers.get("x-requested-with") != "XMLHttpRequest"
    ):
        return HttpResponseBadRequest("Only ajax get requests allowed")
    if not request.user.has_perm("view_demand_report"):
        return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

    # Collect list of selected sales orders
    so_list = request.GET.getlist("demand")

    # Collect operationplans associated with the sales order(s)
    id_list = []
    for dm in (
        Demand.objects.all().using(request.database).filter(pk__in=so_list).only("plan")
    ):
        for op in dm.plan["pegging"]:
            id_list.append(op["opplan"])

    # Collect details on the operationplans
    result = []
    for o in (
        PurchaseOrder.objects.all()
        .using(request.database)
        .filter(id__in=id_list, status="proposed")
    ):
        result.append(
            {
                "id": o.id,
                "type": "PO",
                "item": o.item.name,
                "location": o.location.name,
                "origin": o.supplier.name,
                "startdate": str(o.startdate.date()),
                "enddate": str(o.enddate.date()),
                "quantity": float(o.quantity),
                "value": float(o.quantity * o.item.cost),
                "criticality": float(o.criticality),
            }
        )
    for o in (
        DistributionOrder.objects.all()
        .using(request.database)
        .filter(id__in=id_list, status="proposed")
    ):
        result.append(
            {
                "id": o.id,
                "type": "DO",
                "item": o.item.name,
                "location": o.location.name,
                "origin": o.origin.name,
                "startdate": str(o.startdate),
                "enddate": str(o.enddate),
                "quantity": float(o.quantity),
                "value": float(o.quantity * o.item.cost),
                "criticality": float(o.criticality),
            }
        )
    for o in (
        ManufacturingOrder.objects.all()
        .using(request.database)
        .filter(id__in=id_list, status="proposed")
    ):
        result.append(
            {
                "id": o.id,
                "type": "MO",
                "item": "",
                "location": o.operation.location.name,
                "origin": o.operation.name,
                "startdate": str(o.startdate.date()),
                "enddate": str(o.enddate.date()),
                "quantity": float(o.quantity),
                "value": "",
                "criticality": float(o.criticality),
            }
        )

    return HttpResponse(
        content=json.dumps(result),
        content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
    )
