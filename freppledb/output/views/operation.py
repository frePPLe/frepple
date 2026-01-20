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

from django.db import connections, transaction
from django.db.models.expressions import RawSQL
from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy
from django.utils.encoding import force_str

from freppledb.boot import getAttributeFields
from freppledb.input.models import (
    Operation,
    DistributionOrder,
    PurchaseOrder,
    Item,
    Location,
    Supplier,
)
from freppledb.common.report import getHorizon, GridFieldNumber, GridFieldInteger
from freppledb.common.report import GridPivot, GridFieldText, GridFieldDuration
from freppledb.common.report import (
    GridFieldCurrency,
    GridFieldDateTime,
    GridFieldLastModified,
    GridFieldBool,
)


class OverviewReport(GridPivot):
    """
    A report summarizing all manufacturing orders.
    """

    template = "output/operation.html"
    title = _("Operations summary")
    model = Operation
    permissions = (("view_operation_report", "Can view operation report"),)
    help_url = "user-interface/plan-analysis/operations-summary.html"

    rows = (
        GridFieldText(
            "operation",
            title=_("operation"),
            key=True,
            editable=False,
            field_name="name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            editable=False,
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        # Optional fields on the operation
        GridFieldText(
            "item",
            title=_("item"),
            editable=False,
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
            initially_hidden=True,
        ),
        GridFieldText(
            "description", title=_("description"), editable=False, initially_hidden=True
        ),
        GridFieldText(
            "category", title=_("category"), editable=False, initially_hidden=True
        ),
        GridFieldText(
            "subcategory", title=_("subcategory"), editable=False, initially_hidden=True
        ),
        GridFieldText("type", title=_("type"), initially_hidden=True, editable=False),
        GridFieldDuration(
            "duration", title=_("duration"), initially_hidden=True, editable=False
        ),
        GridFieldDuration(
            "duration_per",
            title=_("duration per unit"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "fence", title=_("release fence"), initially_hidden=True, editable=False
        ),
        GridFieldDuration(
            "posttime", title=_("post-op time"), initially_hidden=True, editable=False
        ),
        GridFieldNumber(
            "sizeminimum",
            title=_("size minimum"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "sizemultiple",
            title=_("size multiple"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "sizemaximum",
            title=_("size maximum"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "priority", title=_("priority"), initially_hidden=True, editable=False
        ),
        GridFieldDateTime(
            "effective_start",
            title=_("effective start"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "effective_end",
            title=_("effective end"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "cost", title=_("cost"), initially_hidden=True, editable=False
        ),
        GridFieldText(
            "search", title=_("search mode"), initially_hidden=True, editable=False
        ),
        GridFieldText(
            "source", title=_("source"), initially_hidden=True, editable=False
        ),
        GridFieldLastModified("lastmodified", initially_hidden=True, editable=False),
        # Optional fields on the location
        GridFieldText(
            "location__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("description")),
        ),
        GridFieldText(
            "location__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("category")),
        ),
        GridFieldText(
            "location__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
        ),
        GridFieldText(
            "location__available",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("available")),
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldLastModified(
            "location__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("last modified")),
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("description")),
        ),
        GridFieldText(
            "item__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("category")),
        ),
        GridFieldText(
            "item__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
        ),
        GridFieldCurrency(
            "item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "item__volume",
            title=format_lazy("{} - {}", _("item"), _("volume")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "item__weight",
            title=format_lazy("{} - {}", _("item"), _("weight")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__uom",
            title=format_lazy("{} - {}", _("item"), _("unit of measure")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "item__periodofcover",
            title=format_lazy("{} - {}", _("item"), _("period of cover")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
        ),
        GridFieldText(
            "item__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("source")),
        ),
        GridFieldLastModified(
            "item__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("last modified")),
        ),
        GridFieldBool(
            "is_work_order", title="is_work_order", hidden=True, search=False
        ),
    )

    crosses = (
        ("proposed_start", {"title": _("proposed starts"), "initially_hidden": True}),
        ("total_start", {"title": _("total starts")}),
        ("proposed_end", {"title": _("proposed ends"), "initially_hidden": True}),
        ("total_end", {"title": _("total ends")}),
        (
            "production_proposed",
            {"title": _("proposed production"), "initially_hidden": True},
        ),
        ("production_total", {"title": _("total production")}),
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom operation attributes
            for f in getAttributeFields(
                Operation, related_name_prefix="operation", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                reportclass.attr_sql += "operation.%s, " % f.name.split("__")[-1]
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                reportclass.attr_sql += "item.%s, " % f.name.split("__")[-1]
            # Adding custom location attributes
            for f in getAttributeFields(
                Location, related_name_prefix="location", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                reportclass.attr_sql += "location.%s, " % f.name.split("__")[-1]

    @staticmethod
    def basequeryset(request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plan"
            return Operation.objects.filter(name=args[0])
        else:
            current, start, end = getHorizon(request)
            return Operation.objects.all().extra(
                where=[
                    "exists (select 1 from operationplan where operationplan.operation_id = operation.name and startdate <= %s and enddate >= %s)"
                ],
                params=[end, start],
            )

    @staticmethod
    def extra_context(request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plan"
            return {
                "title": force_str(Operation._meta.verbose_name) + " " + args[0],
                "post_title": _("plan"),
                "model": Operation,
            }
        else:
            return {}

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )
        # Build the query
        query = """
      select
        operation.name, location.name, operation.item_id, operation.description,
        operation.category, operation.subcategory, operation.type, operation.duration,
        operation.duration_per, operation.fence, operation.posttime, operation.sizeminimum,
        operation.sizemultiple, operation.sizemaximum, operation.priority, operation.effective_start,
        operation.effective_end, operation.cost, operation.search, operation.source, operation.lastmodified,
        location.description, location.category, location.subcategory, location.available_id,
        location.lastmodified, item.description, item.category, item.subcategory, item.cost,
        item.volume, item.weight, item.uom, item.periodofcover, item.owner_id, item.source, item.lastmodified,
        %s
        (operation.owner_id is not null and exists (select 1 from operation parent_op where type = 'routing' and name = operation.owner_id)) as is_work_order,
        res.bucket, res.startdate, res.enddate,
        res.proposed_start, res.total_start, res.proposed_end, res.total_end, res.proposed_production, res.total_production

      from operation
      left outer join item
      on operation.item_id = item.name
      left outer join location
      on operation.location_id = location.name
      inner join (
        select oper.name as operation_id, d.bucket, d.startdate, d.enddate,
         coalesce(sum(
           case when operationplan.status = 'proposed'
             and d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
           then operationplan.quantity
           end
           ), 0) proposed_start,
         coalesce(sum(
           case when d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
           then operationplan.quantity end
           ), 0) total_start,
         coalesce(sum(
           case when operationplan.status = 'proposed'
             and d.startdate <= operationplan.enddate and d.enddate >= operationplan.enddate
           then operationplan.quantity end
           ), 0) proposed_end,
         coalesce(sum(
           case when d.startdate <= operationplan.enddate and d.enddate >= operationplan.enddate
           then operationplan.quantity end
           ), 0) total_end,
         coalesce(sum(
           case
           when operationplan.status = 'proposed'
            and operationplan.enddate = operationplan.startdate
            and d.startdate <= operationplan.enddate
            and d.enddate > operationplan.enddate
            then
                operationplan.quantity
           when operationplan.status = 'proposed'
            then
             (
             -- Total overlap
             extract (epoch from least(operationplan.enddate, d.enddate) - greatest(operationplan.startdate, d.startdate))
             -- Minus the interruptions
             - coalesce((
                select sum(greatest(0, extract (epoch from
                  least(to_timestamp(value->>1, 'YYYY-MM-DD HH24:MI:SS'), d.enddate)
                  - greatest(to_timestamp(value->>0, 'YYYY-MM-DD HH24:MI:SS'), d.startdate)
                  )))
                from ( select * from jsonb_array_elements(plan->'interruptions')) breaks
                ), 0)
             )
             / greatest(1, extract(epoch from operationplan.enddate - operationplan.startdate) - coalesce((plan#>>'{unavailable}')::numeric, 0))
             * operationplan.quantity
           end
           ), 0) proposed_production,
         coalesce(sum(
           case
           when operationplan.enddate = operationplan.startdate
            and d.startdate <= operationplan.enddate
            and d.enddate > operationplan.enddate
            then
                operationplan.quantity
           else
             (
             -- Total overlap
             extract (epoch from least(operationplan.enddate, d.enddate) - greatest(operationplan.startdate, d.startdate))
             -- Minus the interruptions
             - coalesce((
                select sum(greatest(0, extract (epoch from
                  least(to_timestamp(value->>1, 'YYYY-MM-DD HH24:MI:SS'), d.enddate)
                  - greatest(to_timestamp(value->>0, 'YYYY-MM-DD HH24:MI:SS'), d.startdate)
                  )))
                from ( select * from jsonb_array_elements(plan->'interruptions')) breaks
                ), 0)
             )
           / greatest(1, extract(epoch from operationplan.enddate - operationplan.startdate) - coalesce((plan#>>'{unavailable}')::numeric, 0))
           * operationplan.quantity
           end
           ), 0) total_production
        from (%s) oper
        -- Multiply with buckets
        cross join (
          select name as bucket, startdate, enddate
          from common_bucketdetail
          where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
          ) d
        -- Match overlapping operationplans
        left outer join operationplan
          on operationplan.operation_id = oper.name
          and (operationplan.startdate, operationplan.enddate) overlaps (d.startdate, d.enddate)
        group by oper.name, d.bucket, d.startdate, d.enddate
      ) res
      on res.operation_id = operation.name
      order by %s, res.startdate
      """ % (
            reportclass.attr_sql,
            basesql,
            request.report_bucket,
            request.report_startdate,
            request.report_enddate,
            sortsql,
        )

        # Convert the SQl results to Python
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(query, baseparams)
                operationattributefields = getAttributeFields(Operation)
                itemattributefields = getAttributeFields(Item)
                locationattributefields = getAttributeFields(Location)
                for row in cursor_chunked:
                    numfields = len(row)
                    result = {
                        "operation": row[0],
                        "location": row[1],
                        "item": row[2],
                        "description": row[3],
                        "category": row[4],
                        "subcategory": row[5],
                        "type": row[6],
                        "duration": row[7],
                        "duration_per": row[8],
                        "fence": row[9],
                        "posttime": row[10],
                        "sizeminimum": row[11],
                        "sizemultiple": row[12],
                        "sizemaximum": row[13],
                        "priority": row[14],
                        "effective_start": row[15],
                        "effective_end": row[16],
                        "cost": row[17],
                        "search": row[18],
                        "source": row[19],
                        "lastmodified": row[20],
                        "location__description": row[21],
                        "location__category": row[22],
                        "location__subcategory": row[23],
                        "location__available": row[24],
                        "location__lastmodified": row[25],
                        "item__description": row[26],
                        "item__category": row[27],
                        "item__subcategory": row[28],
                        "item__cost": row[29],
                        "item__volume": row[30],
                        "item__weight": row[31],
                        "item__uom": row[32],
                        "item__periodofcover": row[33],
                        "item__owner": row[34],
                        "item__source": row[35],
                        "item__lastmodified": row[36],
                        "is_work_order": row[numfields - 10],
                        "bucket": row[numfields - 9],
                        "startdate": row[numfields - 8].date(),
                        "enddate": row[numfields - 7].date(),
                        "proposed_start": row[numfields - 6],
                        "total_start": row[numfields - 5],
                        "proposed_end": row[numfields - 4],
                        "total_end": row[numfields - 3],
                        "production_proposed": row[numfields - 2],
                        "production_total": row[numfields - 1],
                    }
                    idx = 37
                    for f in operationattributefields:
                        result["operation__%s" % f.field_name] = row[idx]
                        idx += 1
                    for f in itemattributefields:
                        result["item__%s" % f.field_name] = row[idx]
                        idx += 1
                    for f in locationattributefields:
                        result["location__%s" % f.field_name] = row[idx]
                        idx += 1
                    yield result


class PurchaseReport(GridPivot):
    """
    A report summarizing all purchase orders.
    """

    template = "output/purchase_order_summary.html"
    title = _("Purchase order summary")
    model = PurchaseOrder
    permissions = (("view_purchaseorder", "Can view purchase order"),)
    help_url = "user-interface/plan-analysis/purchase-order-summary.html"

    rows = (
        GridFieldText(
            "key",
            key=True,
            search=False,
            initially_hidden=True,
            hidden=True,
            field_name="item__name",
            editable=False,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            editable=False,
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "item__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("description")),
        ),
        GridFieldText(
            "item__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("category")),
        ),
        GridFieldText(
            "item__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
        ),
        GridFieldCurrency(
            "item__cost",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("cost")),
            field_name="item__cost",
        ),
        GridFieldNumber(
            "item__volume",
            title=format_lazy("{} - {}", _("item"), _("volume")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "item__weight",
            title=format_lazy("{} - {}", _("item"), _("weight")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__uom",
            title=format_lazy("{} - {}", _("item"), _("unit of measure")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "item__periodofcover",
            title=format_lazy("{} - {}", _("item"), _("period of cover")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
        ),
        GridFieldText(
            "item__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("source")),
        ),
        GridFieldLastModified(
            "item__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("last modified")),
        ),
        GridFieldText(
            "location",
            title=_("location"),
            editable=False,
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "location__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("description")),
        ),
        GridFieldText(
            "location__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("category")),
        ),
        GridFieldText(
            "location__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
        ),
        GridFieldText(
            "location__available",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("available")),
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldLastModified(
            "location__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("last modified")),
        ),
        GridFieldDuration(
            "leadtime", title=_("lead time"), editable=False, search=False
        ),
        GridFieldDuration(
            "batchwindow", title=_("batching window"), editable=False, search=False
        ),
        GridFieldText(
            "supplier",
            title=_("supplier"),
            editable=False,
            field_name="supplier__name",
            formatter="detail",
            extra='"role":"input/supplier"',
        ),
        GridFieldText(
            "supplier__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("supplier"), _("description")),
        ),
        GridFieldText(
            "supplier__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("supplier"), _("category")),
        ),
        GridFieldText(
            "supplier__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("supplier"), _("subcategory")),
        ),
        GridFieldText(
            "supplier__owner",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("supplier"), _("owner")),
            field_name="supplier__owner__name",
        ),
        GridFieldText(
            "supplier__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("supplier"), _("source")),
        ),
        GridFieldLastModified(
            "supplier__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("supplier"), _("last modified")),
        ),
    )

    crosses = (
        ("proposed_start", {"title": _("proposed ordering"), "initially_hidden": True}),
        ("total_start", {"title": _("total ordering")}),
        ("proposed_end", {"title": _("proposed receiving"), "initially_hidden": True}),
        ("total_end", {"title": _("total receiving")}),
        (
            "proposed_on_order",
            {"title": _("proposed on order"), "initially_hidden": True},
        ),
        ("total_on_order", {"title": _("total on order")}),
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                t = f.name.split("__")[-1]
                reportclass.attr_sql += "item.%s as item__%s, " % (t, t)
            # Adding custom location attributes
            for f in getAttributeFields(
                Location, related_name_prefix="location", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                t = f.name.split("__")[-1]
                reportclass.attr_sql += "location.%s as location__%s, " % (t, t)
            # Adding custom supplier attributes
            for f in getAttributeFields(
                Supplier, related_name_prefix="supplier", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                t = f.name.split("__")[-1]
                reportclass.attr_sql += "supplier.%s as supplier__%s, " % (t, t)

    @staticmethod
    def basequeryset(request, *args, **kwargs):
        current, start, end = getHorizon(request)
        return (
            PurchaseOrder.objects.all()
            .filter(startdate__lte=end, enddate__gte=start)
            .annotate(
                key=RawSQL(
                    "coalesce(item_id,'') || coalesce(location_id,'') || coalesce(supplier_id,'')",
                    (),
                )
            )
            .distinct("key")
            .order_by()
        )  # Ordering isn't compatible with the distinct

    @classmethod
    def _apply_sort(reportclass, request, query):
        """
        Applies a sort to the query.
        """
        sortname = None
        if request.GET.get("sidx", ""):
            # 1) Sorting order specified on the request
            sortname = "%s %s" % (request.GET["sidx"], request.GET.get("sord", "asc"))
        elif request.prefs:
            # 2) Sorting order from the preferences
            sortname = "%s %s" % (
                request.prefs.get("sidx", ""),
                request.GET.get("sord", "asc"),
            )
        if not sortname or sortname == " asc":
            # 3) Default sort order
            return query.order_by("key")
        else:
            # Validate the field does exist.
            # We only validate the first level field, and not the fields
            # on related models.
            sortargs = []
            for s in sortname.split(","):
                stripped = s.strip()
                if not stripped:
                    continue
                try:
                    sortfield, direction = stripped.split(" ", 1)
                except ValueError:
                    continue
                try:
                    query.order_by(sortfield).query.__str__()
                    if direction.strip() != "desc":
                        sortargs.append(sortfield)
                    else:
                        sortargs.append("-%s" % sortfield)
                except Exception:
                    for r in reportclass.rows:
                        if r.name == sortfield:
                            try:
                                query.order_by(r.field_name).query.__str__()
                                if direction.strip() != "desc":
                                    sortargs.append(r.field_name)
                                else:
                                    sortargs.append("-%s" % r.field_name)
                            except Exception:
                                # Can't sort on this field
                                pass
                            break
            if sortargs:
                return query.order_by(
                    "key", *sortargs
                )  # The extra ordering by the 'key' is only change with the default method
            else:
                return query.order_by(
                    "key"
                )  # The extra ordering by the 'key' is only change with the default method

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )
        # Build the query
        query = """
      with combinations as (%s)
      select row_to_json(data)
      from (
      select
        -- Key field
        combinations.key as key,
        -- Attribute fields of item, location and supplier
        combinations.item_id as item,
        item.description as item__description,
        item.category as item__category,
        item.subcategory as item__subcategory,
        item.cost as item__cost,
        item.volume as item__volume,
        item.weight as item__weight,
        item.uom as item__uom,
        item.periodofcover as item__periodofcover,
        item.owner_id as item__owner,
        item.source as item__source,
        item.lastmodified as item__lastmodified,
        combinations.location_id as location,
        location.description as location__description,
        location.category as location__category,
        location.subcategory as location__subcategory,
        location.available_id as location__available,
        location.lastmodified as location__lastmodified,
        (
          select extract(epoch from leadtime)
          from itemsupplier
          where itemsupplier.item_id = combinations.item_id
            and (itemsupplier.location_id is null or itemsupplier.location_id = combinations.location_id)
            and itemsupplier.supplier_id = combinations.supplier_id
          order by '%s' < itemsupplier.effective_end desc nulls first,
             '%s' >= itemsupplier.effective_start desc nulls first,
             itemsupplier.priority <> 0,
             itemsupplier.priority
          limit 1
        ) as leadtime,
        (
          select extract(epoch from batchwindow)
          from itemsupplier
          where itemsupplier.item_id = combinations.item_id
            and (itemsupplier.location_id is null or itemsupplier.location_id = combinations.location_id)
            and itemsupplier.supplier_id = combinations.supplier_id
          order by '%s' < itemsupplier.effective_end desc nulls first,
             '%s' >= itemsupplier.effective_start desc nulls first,
             itemsupplier.priority <> 0,
             itemsupplier.priority
          limit 1
        ) as batchwindow,
        combinations.supplier_id as supplier,
        supplier.description as supplier__description,
        supplier.category as supplier__category,
        supplier.subcategory as supplier__subcategory,
        supplier.owner_id as supplier__owner,
        supplier.source as supplier__source,
        supplier.lastmodified as supplier__lastmodified,
        %s
        -- Buckets
        res.bucket as bucket,
        to_char(res.startdate, 'YYYY-MM-DD') as startdate,
        to_char(res.enddate, 'YYYY-MM-DD') as enddate,
        -- Values
        res.proposed_start as proposed_start,
        res.total_start as total_start,
        res.proposed_end as proposed_end,
        res.total_end as total_end,
        res.proposed_on_order as proposed_on_order,
        res.total_on_order as total_on_order
      from combinations
      inner join item on combinations.item_id = item.name
      left outer join location on combinations.location_id = location.name
      left outer join supplier on combinations.supplier_id = supplier.name
      inner join (
        select
          operationplan.item_id, operationplan.location_id, operationplan.supplier_id,
          d.bucket, d.startdate, d.enddate,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity
            else 0 end
            ), 0) proposed_start,
          coalesce(sum(
            case when d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity else 0 end
            ), 0) total_start,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_end,
          coalesce(sum(
            case when d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_end,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_on_order,
          coalesce(sum(
            case when d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_on_order
        from operationplan
        inner join  combinations
        on operationplan.item_id = combinations.item_id
          and operationplan.location_id = combinations.location_id
          and operationplan.supplier_id = combinations.supplier_id
        cross join (
          select name as bucket, startdate, enddate
          from common_bucketdetail
          where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
          ) d
        where operationplan.type = 'PO'
        group by operationplan.item_id, operationplan.location_id, operationplan.supplier_id,
          d.bucket, d.startdate, d.enddate
        ) res
      on res.item_id = combinations.item_id
        and res.location_id = combinations.location_id
        and res.supplier_id = combinations.supplier_id
      order by %s, res.startdate
      ) data
      """ % (
            basesql,
            request.report_startdate,
            request.report_startdate,
            request.report_startdate,
            request.report_startdate,
            reportclass.attr_sql,
            request.report_bucket,
            request.report_startdate,
            request.report_enddate,
            sortsql,
        )

        # Convert the SQL results to Python
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(query, baseparams)
                for row in cursor_chunked:
                    yield row[0]


class DistributionReport(GridPivot):
    """
    A report summarizing all distribution orders.
    """

    template = "output/distribution_order_summary.html"
    title = _("Distribution order summary")
    model = DistributionOrder
    permissions = (("view_distributionorder", "Can view distribution order"),)
    help_url = "user-interface/plan-analysis/distribution-order-summary.html"

    rows = (
        GridFieldText(
            "key",
            key=True,
            search=False,
            initially_hidden=True,
            hidden=True,
            field_name="item__name",
            editable=False,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            editable=False,
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "item__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("description")),
        ),
        GridFieldText(
            "item__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("category")),
        ),
        GridFieldText(
            "item__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
        ),
        GridFieldCurrency(
            "item__cost",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("cost")),
            field_name="item__cost",
        ),
        GridFieldNumber(
            "item__volume",
            title=format_lazy("{} - {}", _("item"), _("volume")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "item__weight",
            title=format_lazy("{} - {}", _("item"), _("weight")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__uom",
            title=format_lazy("{} - {}", _("item"), _("unit of measure")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "item__periodofcover",
            title=format_lazy("{} - {}", _("item"), _("period of cover")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
        ),
        GridFieldText(
            "item__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("source")),
        ),
        GridFieldLastModified(
            "item__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("last modified")),
        ),
        GridFieldText(
            "origin",
            title=_("origin"),
            editable=False,
            field_name="origin__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "origin__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("origin"), _("description")),
        ),
        GridFieldText(
            "origin__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("origin"), _("category")),
        ),
        GridFieldText(
            "origin__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("origin"), _("subcategory")),
        ),
        GridFieldText(
            "origin__available",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("origin"), _("available")),
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldLastModified(
            "origin__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("origin"), _("last modified")),
        ),
        GridFieldText(
            "destination",
            title=_("destination"),
            editable=False,
            field_name="destination__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "destination__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("destination"), _("description")),
        ),
        GridFieldText(
            "destination__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("destination"), _("category")),
        ),
        GridFieldText(
            "destination__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("destination"), _("subcategory")),
        ),
        GridFieldText(
            "destination__available",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("destination"), _("available")),
            field_name="destination__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldLastModified(
            "destination__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("destination"), _("last modified")),
        ),
    )

    crosses = (
        ("proposed_start", {"title": _("proposed shipping"), "initially_hidden": True}),
        ("total_start", {"title": _("total shipping")}),
        ("proposed_end", {"title": _("proposed receiving"), "initially_hidden": True}),
        ("total_end", {"title": _("total receiving")}),
        (
            "proposed_in_transit",
            {"title": _("proposed in transit"), "initially_hidden": True},
        ),
        ("total_in_transit", {"title": _("total in transit")}),
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                t = f.name.split("__")[-1]
                reportclass.attr_sql += "item.%s as item__%s, " % (t, t)
            # Adding custom origin attributes
            for f in getAttributeFields(
                Location, related_name_prefix="origin", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                t = f.name.split("__")[-1]
                reportclass.attr_sql += "origin.%s as origin__%s, " % (t, t)
            # Adding custom destination attributes
            for f in getAttributeFields(
                Location, related_name_prefix="destination", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                t = f.name.split("__")[-1]
                reportclass.attr_sql += "destination.%s as destination__%s, " % (t, t)

    @staticmethod
    def basequeryset(request, *args, **kwargs):
        current, start, end = getHorizon(request)
        return (
            DistributionOrder.objects.all()
            .filter(startdate__lte=end, enddate__gte=start)
            .annotate(
                key=RawSQL(
                    "coalesce(item_id,'') || coalesce(origin_id,'') || coalesce(destination_id,'')",
                    (),
                )
            )
            .distinct("key")
            .order_by()
        )  # Ordering isn't compatible with the distinct

    @classmethod
    def _apply_sort(reportclass, request, query):
        """
        Applies a sort to the query.
        """
        sortname = None
        if request.GET.get("sidx", ""):
            # 1) Sorting order specified on the request
            sortname = "%s %s" % (request.GET["sidx"], request.GET.get("sord", "asc"))
        elif request.prefs:
            # 2) Sorting order from the preferences
            sortname = "%s %s" % (
                request.prefs.get("sidx", ""),
                request.GET.get("sord", "asc"),
            )
        if not sortname or sortname == " asc":
            # 3) Default sort order
            return query.order_by("key")
        else:
            # Validate the field does exist.
            # We only validate the first level field, and not the fields
            # on related models.
            sortargs = []
            for s in sortname.split(","):
                stripped = s.strip()
                if not stripped:
                    continue
                try:
                    sortfield, direction = stripped.split(" ", 1)
                except ValueError:
                    continue
                try:
                    query.order_by(sortfield).query.__str__()
                    if direction.strip() != "desc":
                        sortargs.append(sortfield)
                    else:
                        sortargs.append("-%s" % sortfield)
                except Exception:
                    for r in reportclass.rows:
                        if r.name == sortfield:
                            try:
                                query.order_by(r.field_name).query.__str__()
                                if direction.strip() != "desc":
                                    sortargs.append(r.field_name)
                                else:
                                    sortargs.append("-%s" % r.field_name)
                            except Exception:
                                # Can't sort on this field
                                pass
                            break
            if sortargs:
                return query.order_by(
                    "key", *sortargs
                )  # The extra ordering by the 'key' is only change with the default method
            else:
                return query.order_by(
                    "key"
                )  # The extra ordering by the 'key' is only change with the default method

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )
        # Build the query
        query = """
      with combinations as (%s)
      select row_to_json(data)
      from (
      select
        -- Key field
        combinations.key as key,
        -- Attribute fields of item, location and supplier
        combinations.item_id as item,
        item.description as item__description,
        item.category as item__category,
        item.subcategory as item__subcategory,
        item.cost as item__cost,
        item.volume as item__volume,
        item.weight as item__weight,
        item.uom as item__uom,
        item.periodofcover as item__periodofcover,
        item.owner_id as item__owner,
        item.source as item__source,
        item.lastmodified as item__lastmodified,
        combinations.origin_id as origin,
        origin.description as origin__description,
        origin.category as origin__category,
        origin.subcategory as origin__subcategory,
        origin.available_id as origin__available,
        origin.lastmodified as origin__lastmodified,
        combinations.destination_id as destination,
        destination.description as destination__description,
        destination.category as destination__category,
        destination.subcategory as destination__subcategory,
        destination.available_id as destination__available,
        destination.lastmodified as destination__lastmodified,
        %s
        -- Buckets
        res.bucket as bucket,
        to_char(res.startdate, 'YYYY-MM-DD') as startdate,
        to_char(res.enddate, 'YYYY-MM-DD') as enddate,
        -- Values
        res.proposed_start as proposed_start,
        res.total_start as total_start,
        res.proposed_end as proposed_end,
        res.total_end as total_end,
        res.proposed_in_transit as proposed_in_transit,
        res.total_in_transit as total_in_transit
      from combinations
      inner join item on combinations.item_id = item.name
      left outer join location origin on combinations.origin_id = origin.name
      left outer join location destination on combinations.destination_id = destination.name
      inner join (
        select
          operationplan.item_id, operationplan.origin_id, operationplan.destination_id,
          d.bucket, d.startdate, d.enddate,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity
            else 0 end
            ), 0) proposed_start,
          coalesce(sum(
            case when d.startdate <= operationplan.startdate and d.enddate > operationplan.startdate
            then operationplan.quantity else 0 end
            ), 0) total_start,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_end,
          coalesce(sum(
            case when d.startdate <= operationplan.enddate and d.enddate > operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_end,
          coalesce(sum(
            case when operationplan.status = 'proposed'
              and d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
             then operationplan.quantity else 0 end
            ), 0) proposed_in_transit,
          coalesce(sum(
            case when d.enddate > operationplan.startdate and d.enddate <= operationplan.enddate
            then operationplan.quantity else 0 end
            ), 0) total_in_transit
        from operationplan
        inner join combinations
        on operationplan.item_id = combinations.item_id
          and operationplan.origin_id = combinations.origin_id
          and operationplan.destination_id = combinations.destination_id
        cross join (
          select name as bucket, startdate, enddate
          from common_bucketdetail
          where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
          ) d
        where operationplan.type = 'DO'
        group by operationplan.item_id, operationplan.origin_id, operationplan.destination_id,
          d.bucket, d.startdate, d.enddate
        ) res
      on res.item_id = combinations.item_id
        and res.origin_id = combinations.origin_id
        and res.destination_id = combinations.destination_id
      order by %s, res.startdate
      ) data
      """ % (
            basesql,
            reportclass.attr_sql,
            request.report_bucket,
            request.report_startdate,
            request.report_enddate,
            sortsql,
        )

        # Convert the SQL results to Python
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(query, baseparams)
                for row in cursor_chunked:
                    yield row[0]
