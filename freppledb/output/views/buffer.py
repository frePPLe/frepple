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
from datetime import timedelta, datetime
import json

from django.conf import settings
from django.db import connections, transaction
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils.encoding import force_str
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from freppledb.boot import getAttributeFields
from freppledb.input.models import Buffer, Item, Location, OperationPlanMaterial
from freppledb.common.report import (
    GridPivot,
    GridFieldText,
    GridFieldNumber,
    GridFieldInteger,
    GridFieldLastModified,
    GridFieldCurrency,
)


class OverviewReport(GridPivot):
    """
    A report showing the inventory profile of buffers.
    """

    template = "output/buffer.html"
    title = _("Inventory report")
    new_arg_logic = True

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if hasattr(request, "basequeryset"):
            return request.basequeryset

        item = None
        location = None
        batch = None

        if len(args) and args[0]:
            if request.path_info.startswith(
                "/buffer/item/"
            ) or request.path_info.startswith("/detail/input/item/"):
                item = args[0]
            else:
                i_b_l = args[0].split(" @ ")
                if len(i_b_l) == 1:
                    b = Buffer.objects.values("item", "location").get(id=args[0])
                    item = b["item"]
                    location = b["location"]
                elif len(i_b_l) == 2:
                    item = i_b_l[0]
                    location = i_b_l[1]
                else:
                    item = i_b_l[0]
                    location = i_b_l[2]
                    batch = i_b_l[1]

        request.basequeryset = OperationPlanMaterial.objects.values(
            "item", "location", "item__type"
        ).filter(
            ((Q(item__type="make to stock") | Q(item__type__isnull=True)))
            | (Q(item__type="make to order") & Q(operationplan__batch__isnull=False))
        )

        if item:
            request.basequeryset = request.basequeryset.filter(item=item)

        if location:
            request.basequeryset = request.basequeryset.filter(location=location)

        if batch:
            request.basequeryset = request.basequeryset.filter(
                operationplan__batch=batch
            )

        request.basequeryset = request.basequeryset.annotate(
            buffer=RawSQL(
                "operationplanmaterial.item_id || "
                "(case when item.type is distinct from 'make to order' then '' else ' @ ' || operationplan.batch end) "
                "|| ' @ ' || operationplanmaterial.location_id",
                (),
            ),
            opplan_batch=RawSQL(
                "case when item.type is distinct from 'make to order' then '' else operationplan.batch end",
                (),
            ),
        ).distinct()

        return request.basequeryset

    model = OperationPlanMaterial
    default_sort = (1, "asc", 2, "asc")
    permissions = (("view_inventory_report", "Can view inventory report"),)
    help_url = "user-interface/plan-analysis/inventory-report.html"

    rows = (
        GridFieldText(
            "buffer", title=_("buffer"), editable=False, key=True, initially_hidden=True
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
            "location",
            title=_("location"),
            editable=False,
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
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
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "batch",
            title=_("batch"),
            field_name="opplan_batch",
            editable=False,
            initially_hidden=True,
        ),
        GridFieldNumber("is_ip_buffer", title="is_ip_buffer", hidden=True),
    )

    crosses = (
        ("startoh", {"title": _("start inventory")}),
        (
            "startohdoc",
            {"title": _("start inventory days of cover"), "initially_hidden": True},
        ),
        ("safetystock", {"title": _("safety stock")}),
        (
            "produced",
            {
                "title": _("total produced"),
                "expand": ["produced_confirmed", "produced_proposed"],
            },
        ),
        (
            "consumed",
            {
                "title": _("total consumed"),
                "expand": ["consumed_confirmed", "consumed_proposed"],
            },
        ),
        (
            "consumed_confirmed",
            {
                "title": _("total consumed confirmed"),
                "expand": ["consumedMO_confirmed", "consumedDO_confirmed"],
                "initially_hidden": True,
            },
        ),
        (
            "consumed_proposed",
            {
                "title": _("total consumed proposed"),
                "expand": [
                    "consumedMO_proposed",
                    "consumedDO_proposed",
                    "consumedSO",
                    "consumedFcst",
                ],
                "initially_hidden": True,
            },
        ),
        (
            "consumedMO",
            {
                "title": _("consumed by MO"),
                "expand": ["consumedMO_proposed", "consumedMO_confirmed"],
                "initially_hidden": True,
            },
        ),
        (
            "consumedMO_confirmed",
            {"title": _("consumed by MO confirmed"), "initially_hidden": True},
        ),
        (
            "consumedMO_proposed",
            {"title": _("consumed by MO proposed"), "initially_hidden": True},
        ),
        (
            "consumedDO",
            {
                "title": _("consumed by DO"),
                "expand": ["consumedDO_confirmed", "consumedDO_proposed"],
                "initially_hidden": True,
            },
        ),
        (
            "consumedDO_confirmed",
            {"title": _("consumed by DO confirmed"), "initially_hidden": True},
        ),
        (
            "consumedDO_proposed",
            {"title": _("consumed by DO proposed"), "initially_hidden": True},
        ),
        ("consumedSO", {"title": _("consumed by SO"), "initially_hidden": True}),
        (
            "produced_confirmed",
            {
                "title": _("total produced confirmed"),
                "expand": [
                    "producedMO_confirmed",
                    "producedPO_confirmed",
                    "producedDO_confirmed",
                ],
                "initially_hidden": True,
            },
        ),
        (
            "produced_proposed",
            {
                "title": _("total produced proposed"),
                "expand": [
                    "producedMO_proposed",
                    "producedPO_proposed",
                    "producedDO_proposed",
                ],
                "initially_hidden": True,
            },
        ),
        (
            "producedMO",
            {
                "title": _("produced by MO"),
                "initially_hidden": True,
                "expand": ["producedMO_confirmed", "producedMO_proposed"],
            },
        ),
        (
            "producedMO_confirmed",
            {"title": _("produced by MO confirmed"), "initially_hidden": True},
        ),
        (
            "producedMO_proposed",
            {"title": _("produced by MO proposed"), "initially_hidden": True},
        ),
        (
            "producedDO",
            {
                "title": _("produced by DO"),
                "expand": ["producedDO_confirmed", "producedDO_proposed"],
                "initially_hidden": True,
            },
        ),
        (
            "producedDO_confirmed",
            {"title": _("produced by DO confirmed"), "initially_hidden": True},
        ),
        (
            "producedDO_proposed",
            {"title": _("produced by DO proposed"), "initially_hidden": True},
        ),
        (
            "producedPO",
            {
                "title": _("produced by PO"),
                "expand": ["producedPO_confirmed", "producedPO_proposed"],
                "initially_hidden": True,
            },
        ),
        (
            "producedPO_confirmed",
            {"title": _("produced by PO confirmed"), "initially_hidden": True},
        ),
        (
            "producedPO_proposed",
            {"title": _("produced by PO proposed"), "initially_hidden": True},
        ),
        ("endoh", {"title": _("end inventory")}),
        (
            "total_in_progress",
            {
                "title": _("total in progress"),
                "expand": ["total_in_progress_confirmed", "total_in_progress_proposed"],
                "initially_hidden": True,
            },
        ),
        (
            "total_in_progress_confirmed",
            {
                "title": _("total in progress confirmed"),
                "expand": [
                    "work_in_progress_mo_confirmed",
                    "in_transit_do_confirmed",
                    "on_order_po_confirmed",
                ],
                "initially_hidden": True,
            },
        ),
        (
            "total_in_progress_proposed",
            {
                "title": _("total in progress proposed"),
                "expand": [
                    "work_in_progress_mo_proposed",
                    "in_transit_do_proposed",
                    "on_order_po_proposed",
                ],
                "initially_hidden": True,
            },
        ),
        (
            "work_in_progress_mo",
            {
                "title": _("work in progress MO"),
                "expand": [
                    "total_in_progress_mo_confirmed",
                    "total_in_progress_mo_proposed",
                ],
                "initially_hidden": True,
            },
        ),
        (
            "work_in_progress_mo_confirmed",
            {"title": _("work in progress MO confirmed"), "initially_hidden": True},
        ),
        (
            "work_in_progress_mo_proposed",
            {"title": _("work in progress MO proposed"), "initially_hidden": True},
        ),
        (
            "on_order_po",
            {
                "title": _("on order PO"),
                "expand": ["on_order_po_confirmed", "on_order_po_proposed"],
                "initially_hidden": True,
            },
        ),
        (
            "on_order_po_confirmed",
            {"title": _("on order PO confirmed"), "initially_hidden": True},
        ),
        (
            "proposed_ordering",
            {"title": _("proposed ordering"), "initially_hidden": True},
        ),
        (
            "on_order_po_proposed",
            {"title": _("on order PO proposed"), "initially_hidden": True},
        ),
        (
            "in_transit_do",
            {
                "title": _("in transit DO"),
                "expand": ["in_transit_do_confirmed", "in_transit_do_proposed"],
                "initially_hidden": True,
            },
        ),
        (
            "in_transit_do_confirmed",
            {"title": _("in transit DO confirmed"), "initially_hidden": True},
        ),
        (
            "in_transit_do_proposed",
            {"title": _("in transit DO proposed"), "initially_hidden": True},
        ),
        ("consumedFcst", {"title": _("consumed by Fcst"), "initially_hidden": True}),
        ("open_orders", {"title": _("open sales orders"), "initially_hidden": True}),
        ("net_forecast", {"title": _("net forecast"), "initially_hidden": True}),
        (
            "total_demand",
            {
                "title": _("total demand"),
                "expand": ["open_orders", "net_forecast"],
                "initially_hidden": True,
            },
        ),
        ("order_backlog", {"title": _("order backlog"), "initially_hidden": True}),
        (
            "forecast_backlog",
            {"title": _("forecast backlog"), "initially_hidden": True},
        ),
        (
            "total_backlog",
            {
                "title": _("total backlog"),
                "expand": ["forecast_backlog", "order_backlog"],
                "initially_hidden": False,
            },
        ),
        ("color", {"title": _("inventory status"), "initially_hidden": True}),
        ("reasons", {"title": _("reasons"), "initially_hidden": True, "hidden": True}),
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
                reportclass.rows += (f,)
                reportclass.attr_sql += "item.%s, " % f.name.split("__")[-1]
            # Adding custom location attributes
            for f in getAttributeFields(
                Location, related_name_prefix="location", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "location.%s, " % f.name.split("__")[-1]

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if not hasattr(request, "basequeryset"):
            reportclass.basequeryset(request, *args, **kwargs)
        if args and args[0]:
            if request.path_info.startswith(
                "/buffer/item/"
            ) or request.path_info.startswith("/detail/input/item/"):
                request.session["lasttab"] = "inventory"
                r = {
                    "title": force_str(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("inventory"),
                    "active_tab": "inventory",
                    "model": Item,
                    "withforecast": "freppledb.forecast" in settings.INSTALLED_APPS,
                }
                if request.basequeryset.using(request.database).count() <= 1:
                    r["args"] = args
                    r["mode"] = "table"
                else:
                    r["args"] = None
                return r
            else:
                request.session["lasttab"] = "plan"
                index = args[0].find(" @ ")
                if index == -1:
                    buffer = Buffer.objects.get(id=args[0])
                return {
                    "title": force_str(Buffer._meta.verbose_name)
                    + " "
                    + (
                        args[0]
                        if index != -1
                        else buffer.item.name + " @ " + buffer.location.name
                    ),
                    "post_title": _("plan"),
                    "active_tab": "plan",
                    "mode": "table",
                    "model": Buffer,
                    "withforecast": "freppledb.forecast" in settings.INSTALLED_APPS,
                }
        else:
            return {"withforecast": "freppledb.forecast" in settings.INSTALLED_APPS}

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Execute a query to get the backlog at the start of the horizon
        startbacklogdict = {}

        # code assumes no max lateness is set to calculate the backlog
        # forecast knows nothing about batch so all is counted as backlog

        backlog_fcst = """
            union all
          select opm.item_id, opm.location_id, '' as batch, 0::numeric qty_orders, coalesce(sum(forecastplan.forecastnet),0) qty_forecast
          from forecastplan
          left outer join common_parameter cp on cp.name = 'forecast.DueWithinBucket'
          inner join (%s) opm on forecastplan.item_id = opm.item_id
          and forecastplan.location_id = opm.location_id
          where forecastplan.customer_id = (select name from customer where lvl=0)
          and case when coalesce(cp.value, 'start') = 'start' then forecastplan.startdate
                   when coalesce(cp.value, 'start') = 'end' then forecastplan.enddate - interval '1 second'
                   when coalesce(cp.value, 'start') = 'middle' then forecastplan.startdate + age(forecastplan.enddate, forecastplan.startdate)/2 end < %%s
          group by opm.item_id, opm.location_id
        """ % (
            basesql,
        )

        deliveries_no_fcst = """
            select opm.item_id,
            opm.location_id,
            case when item.type is distinct from 'make to order' then ''
            else operationplan.batch
            end as batch,
            sum(case when operationplan.demand_id is not null then opm.quantity end) qty_orders,
            0 qty_forecast
            from (%s) opm2
            inner join operationplanmaterial opm on opm.item_id = opm2.item_id and opm.location_id = opm2.location_id
            inner join item on item.name = opm.item_id
            inner join operationplan on operationplan.reference = opm.operationplan_id
                and operationplan.demand_id is not null
                and operationplan.enddate < %%s
                and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opm2.opplan_batch)
            group by opm.item_id, opm.location_id, case when item.type is distinct from 'make to order' then ''
            else operationplan.batch
            end
        """ % (
            basesql,
        )

        deliveries_fcst = """
            select opm.item_id, opm.location_id,
            case when item.type is distinct from 'make to order' then ''
            else operationplan.batch
            end as batch,
            sum(case when operationplan.demand_id is not null then opm.quantity end) qty_orders,
            sum(case when operationplan.forecast is not null then opm.quantity end) qty_forecast
          from (%s) opm2
          inner join operationplanmaterial opm on opm.item_id = opm2.item_id and opm.location_id = opm2.location_id
          inner join item on item.name = opm.item_id
          inner join operationplan on operationplan.reference = opm.operationplan_id
          and (operationplan.demand_id is not null or operationplan.forecast is not null)
          and operationplan.enddate < %%s
          and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opm2.opplan_batch)
          group by opm.item_id, opm.location_id,
            case when item.type is distinct from 'make to order' then ''
            else operationplan.batch
            end
        """ % (
            basesql,
        )

        query = """
          select item_id, location_id, batch, sum(qty_orders), sum(qty_forecast) from
          (
          select opm.item_id, opm.location_id,
          case when item.type is distinct from 'make to order' then ''
          else demand.batch
          end as batch,
          sum(demand.quantity) qty_orders, 0::numeric qty_forecast
          from (%s) opm
          inner join demand on demand.item_id = opm.item_id
          inner join item on item.name = demand.item_id
          and demand.location_id = opm.location_id
          and demand.status in ('open','quote') and demand.due < %%s
          and (item.type is distinct from 'make to order' or demand.batch = opm.opplan_batch)
          group by opm.item_id, opm.location_id, case when item.type is distinct from 'make to order' then ''
          else demand.batch
          end
          %s
          union all
          -- deliveries
          %s
          ) t
          group by item_id, location_id, batch
        """ % (
            basesql,
            backlog_fcst if "freppledb.forecast" in settings.INSTALLED_APPS else "",
            (
                deliveries_fcst
                if "freppledb.forecast" in settings.INSTALLED_APPS
                else deliveries_no_fcst
            ),
        )

        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                current_date = datetime.strptime(
                    request.current_date, "%Y-%m-%d %H:%M:%S"
                )
                cursor_chunked.execute(
                    query,
                    baseparams
                    + (max(request.report_startdate, current_date),)
                    + baseparams
                    + (max(request.report_startdate, current_date),)
                    + (
                        baseparams
                        if "freppledb.forecast" in settings.INSTALLED_APPS
                        else ()
                    )
                    + (
                        (max(request.report_startdate, current_date),)
                        if "freppledb.forecast" in settings.INSTALLED_APPS
                        else ()
                    ),
                )

                for row in cursor_chunked:
                    if row[0]:
                        startbacklogdict[(row[0], row[1], row[2])] = (
                            max(float(row[3] or 0), 0),
                            max(float(row[4] or 0), 0),
                        )
        # Execute the actual query
        reasons_forecast = """
                union all
                select distinct out_constraint.name, out_constraint.owner
                from out_constraint
                inner join operationplan on operationplan.forecast = out_constraint.forecast
                and operationplan.item_id = item.name and operationplan.location_id = location.name
                and operationplan.enddate >= greatest(arguments.report_startdate,d.startdate)
                and operationplan.due < d.enddate
                """
        net_forecast = """
        (select sum(forecastplan.forecastnet)
            from forecastplan
            left outer join common_parameter cp on cp.name = 'forecast.DueWithinBucket'
            where forecastplan.item_id = item.name and forecastplan.location_id = location.name
            and forecastplan.customer_id = (select name from customer where lvl=0)
            and case when coalesce(cp.value, 'start') = 'start' then forecastplan.startdate
                   when coalesce(cp.value, 'start') = 'end' then forecastplan.enddate - interval '1 second'
                   when coalesce(cp.value, 'start') = 'middle' then forecastplan.startdate
                   + age(forecastplan.enddate, forecastplan.startdate)/2 end between d.startdate
                   and d.enddate - interval '1 ms')
        """

        with_ip = "freppledb.inventoryplanning" in settings.INSTALLED_APPS

        if with_ip:
            is_ip_buffer = """
                exists (select 1 from inventoryplanning where item_id = item.name and location_id = location.name)
            """
        else:
            is_ip_buffer = "false"

        query = """
        with arguments as (
                select %%s::timestamp report_startdate,
                %%s::timestamp report_enddate,
                %%s::timestamp report_currentdate,
                %%s report_bucket
           )
           select
           opplanmat.buffer,
           item.name item_id,
           location.name location_id,
           item.description,
           item.type,
           item.category,
           item.subcategory,
           item.cost,
           item.volume,
           item.weight,
           item.uom,
           item.periodofcover,
           item.owner_id,
           item.source,
           item.lastmodified,
           location.description,
           location.category,
           location.subcategory,
           location.available_id,
           location.owner_id,
           location.source,
           location.lastmodified,
           opplanmat.opplan_batch,
           %s is_ip_buffer,
           %s
           (select sum(quantity) from demand where status in ('open','quote')
           and item_id = item.name and location_id = location.name
           and due >= greatest(d.startdate, arguments.report_currentdate)
           and due < d.enddate
           and (item.type is distinct from 'make to order'
           or coalesce(demand.batch,'') is not distinct from opplanmat.opplan_batch)) open_orders,
           %s net_forecast,
		   'not implemented' expiring,
           (select json_agg(json_build_array(t.name, t.owner))
           from (
               select distinct out_constraint.name, out_constraint.owner
                from out_constraint
                inner join operationplan on operationplan.item_id = item.name
                and operationplan.location_id = location.name
                and operationplan.demand_id = out_constraint.demand
                and operationplan.enddate >= greatest(arguments.report_startdate,d.startdate)
                and operationplan.due < d.enddate
                %s
                order by name limit 20
           )t ) reasons,
           case
             when d.history then min(ax_buffer.onhand)
           else
             (
             select onhand
             from operationplanmaterial
             inner join operationplan
               on operationplanmaterial.operationplan_id = operationplan.reference
             where operationplanmaterial.item_id = item.name
               and operationplanmaterial.location_id = location.name
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opplanmat.opplan_batch)
               and flowdate < greatest(d.startdate,arguments.report_startdate)
             order by flowdate desc, id desc limit 1
             )
           end as startoh,
           d.bucket,
           d.startdate,
           d.enddate,
           d.history,
           case when d.history then min(ax_buffer.safetystock)
           else
           coalesce(
              -- 1 calendar bucket of SS calendar
              (select value from calendarbucket
               where calendar_id = 'SS for ' || opplanmat.buffer
               and greatest(d.startdate,arguments.report_startdate) >= coalesce(startdate, '1971-01-01'::timestamp)
               and greatest(d.startdate,arguments.report_startdate) < coalesce(enddate, '2030-12-31'::timestamp)
               order by priority limit 1),
              -- 2 default value of SS calendar
              (select defaultvalue from calendar where name = 'SS for ' || opplanmat.buffer),
			  -- 3 calendar bucket of minimum calendar
              (select value
               from calendarbucket
               where calendar_id = (
                 select minimum_calendar_id
                 from buffer
                 where item_id = item.name
                 and location_id = location.name
                 and (item.type is distinct from 'make to order' or buffer.batch is not distinct from opplanmat.opplan_batch)
                 )
               and greatest(d.startdate,arguments.report_startdate) >= coalesce(startdate, '1971-01-01'::timestamp)
               and greatest(d.startdate,arguments.report_startdate) < coalesce(enddate, '2030-12-31'::timestamp)
               order by priority limit 1),
              -- 4 default value of minimum calendar
              (select defaultvalue
               from calendar
               where name = (
                 select minimum_calendar_id
                 from buffer
                 where item_id = item.name
                 and location_id = location.name
                 and (item.type is distinct from 'make to order' or buffer.batch is not distinct from opplanmat.opplan_batch)
                 )
              ),
              -- 5 buffer minimum
			 (select minimum
            from buffer
            where item_id = item.name
            and location_id = location.name
            and (item.type is distinct from 'make to order' or buffer.batch is not distinct from opplanmat.opplan_batch)))
            end as safetystock,
            case when d.history then json_build_object()
            else (
             with cte as (select greatest(d.startdate,arguments.report_startdate) as bucketstart),
				opm as (
			 select opm.quantity,
					opm.flowdate,
					operationplan.status in ('approved','confirmed','completed') as confirmed_opplan,
					operationplan.status = 'proposed' as proposed_opplan,
					operationplan.startdate,
					operationplan.enddate,
					operationplan.type,
					operationplan.demand_id,
					operationplan.delay,
					(opm.flowdate >= bucketstart and opm.flowdate < d.enddate) flow_in_bucket,
					(startdate < d.enddate and enddate >= d.enddate) flow_in_progress
			 from operationplanmaterial opm
			 cross join cte
             inner join operationplan
             on operationplan.reference = opm.operationplan_id
               and ((startdate < d.enddate and enddate >= d.enddate)
               or (opm.flowdate >= bucketstart and opm.flowdate < d.enddate)
               or (operationplan.type = 'DLVR' and due < d.enddate and due >= case when arguments.report_currentdate >= d.startdate and arguments.report_currentdate < d.enddate then '1970-01-01'::timestamp else d.startdate end))
             where opm.item_id = item.name
               and opm.location_id = location.name
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opplanmat.opplan_batch))
             select json_build_object(
               'work_in_progress_mo', sum(case when flow_in_progress and opm.quantity > 0 and opm.type = 'MO' then opm.quantity else 0 end),
               'work_in_progress_mo_confirmed', sum(case when opm.confirmed_opplan and flow_in_progress and opm.quantity > 0 and opm.type = 'MO' then opm.quantity else 0 end),
               'work_in_progress_mo_proposed', sum(case when opm.proposed_opplan and opm.proposed_opplan and flow_in_progress and opm.quantity > 0 and opm.type = 'MO' then opm.quantity else 0 end),
               'on_order_po', sum(case when flow_in_progress and opm.quantity > 0 and opm.type = 'PO' then opm.quantity else 0 end),
               'on_order_po_confirmed', sum(case when opm.confirmed_opplan and flow_in_progress and opm.quantity > 0 and opm.type = 'PO' then opm.quantity else 0 end),
               'on_order_po_proposed', sum(case when opm.proposed_opplan and flow_in_progress and opm.quantity > 0 and opm.type = 'PO' then opm.quantity else 0 end),
               'proposed_ordering', sum(case when opm.proposed_opplan and opm.type = 'PO' and (opm.startdate >= bucketstart and opm.startdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'in_transit_do', sum(case when flow_in_progress and opm.quantity > 0 and opm.type = 'DO' then opm.quantity else 0 end),
               'in_transit_do_confirmed', sum(case when opm.confirmed_opplan and flow_in_progress and opm.quantity > 0 and opm.type = 'DO' then opm.quantity else 0 end),
               'in_transit_do_proposed', sum(case when opm.proposed_opplan and flow_in_progress and opm.quantity > 0 and opm.type = 'DO' then opm.quantity else 0 end),
               'total_in_progress', sum(case when flow_in_progress and opm.quantity > 0 then opm.quantity else 0 end),
               'total_in_progress_confirmed', sum(case when opm.confirmed_opplan and flow_in_progress and opm.quantity > 0 then opm.quantity else 0 end),
               'total_in_progress_proposed', sum(case when opm.proposed_opplan and flow_in_progress and opm.quantity > 0 then opm.quantity else 0 end),
               'consumed', sum(case when flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumed_confirmed', sum(case when opm.confirmed_opplan and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumed_proposed', sum(case when opm.proposed_opplan and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedMO', sum(case when opm.type = 'MO' and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedMO_confirmed', sum(case when opm.confirmed_opplan and opm.type = 'MO' and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedMO_proposed', sum(case when opm.proposed_opplan and opm.type = 'MO' and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedDO', sum(case when opm.type = 'DO' and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedFcst', sum(case when opm.type = 'DLVR' and opm.demand_id is null and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedDO_confirmed', sum(case when opm.confirmed_opplan and opm.type = 'DO' and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedDO_proposed', sum(case when opm.proposed_opplan and opm.type = 'DO' and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedSO', sum(case when opm.demand_id is not null and flow_in_bucket and opm.quantity < 0 then -opm.quantity else 0 end),
               'produced', sum(case when flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'produced_confirmed', sum(case when opm.confirmed_opplan and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'produced_proposed', sum(case when opm.proposed_opplan and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedMO', sum(case when opm.type = 'MO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedMO_confirmed', sum(case when opm.confirmed_opplan and opm.type = 'MO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedMO_proposed', sum(case when opm.proposed_opplan and opm.type = 'MO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedDO', sum(case when opm.type = 'DO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedDO_confirmed', sum(case when opm.confirmed_opplan and opm.type = 'DO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedDO_proposed', sum(case when opm.proposed_opplan and opm.type = 'DO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedPO', sum(case when opm.type = 'PO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedPO_confirmed', sum(case when opm.confirmed_opplan and opm.type = 'PO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'producedPO_proposed', sum(case when opm.proposed_opplan and opm.type = 'PO' and flow_in_bucket and opm.quantity > 0 then opm.quantity else 0 end),
               'max_delay', max(extract(epoch from case when opm.flowdate >= bucketstart and opm.flowdate < d.enddate then opm.delay else interval '0 second' end) / 86400)
               )
             from opm
             cross join cte
             )
           end as ongoing,
           floor(extract(epoch from coalesce(
                  -- Normal case
                  (
                  select case
                    when periodofcover = 999 * 24 * 3600
                      then '999 days'::interval
                    else date_trunc('day', least( periodofcover * '1 sec'::interval + flowdate - greatest(d.startdate,arguments.report_currentdate), '999 days'::interval))
                    end
                  from operationplanmaterial
                  where flowdate < greatest(d.startdate,arguments.report_currentdate)
                    and operationplanmaterial.item_id = item.name and operationplanmaterial.location_id = location.name
                  order by flowdate desc, id desc
                  limit 1
                 ),
                 '999 days'::interval
                 ))/86400) periodofcover
           from
           (%s) opplanmat
           cross join arguments
           inner join item on item.name = opplanmat.item_id
           inner join location on location.name = opplanmat.location_id
           -- Multiply with buckets
           cross join (
             select name as bucket, startdate, enddate,
               min(snapshot_date) as snapshot_date,
               enddate < arguments.report_currentdate as history
             from common_bucketdetail
             cross join arguments
             left outer join ax_manager
               on snapshot_date >= common_bucketdetail.startdate
               and snapshot_date < common_bucketdetail.enddate
             where common_bucketdetail.bucket_id = arguments.report_bucket
               and common_bucketdetail.enddate > arguments.report_startdate
               and common_bucketdetail.startdate < arguments.report_enddate
             group by common_bucketdetail.name, common_bucketdetail.startdate,
                      common_bucketdetail.enddate, arguments.report_currentdate
             ) d
           -- join with the archive data
           left outer join ax_buffer
             on ax_buffer.snapshot_date_id = d.snapshot_date
             and ax_buffer.item =  opplanmat.item_id
             and ax_buffer.location =  opplanmat.location_id
             and (ax_buffer.batch = opplanmat.opplan_batch or ax_buffer.batch is null or ax_buffer.batch = '')
          group by
           opplanmat.buffer,
           item.name,
           location.name,
           item.description,
           item.type,
           item.category,
           item.subcategory,
           item.cost,
           item.volume,
           item.weight,
           item.uom,
           item.periodofcover,
           item.owner_id,
           item.source,
           item.lastmodified,
           location.description,
           location.category,
           location.subcategory,
           location.available_id,
           location.owner_id,
           location.source,
           location.lastmodified,
           opplanmat.opplan_batch,
           d.bucket,
           d.startdate,
           d.enddate,
           d.history,
           arguments.report_startdate,
           arguments.report_currentdate
           order by %s, d.startdate
        """ % (
            is_ip_buffer,
            reportclass.attr_sql,
            net_forecast if "freppledb.forecast" in settings.INSTALLED_APPS else "0",
            reasons_forecast if "freppledb.forecast" in settings.INSTALLED_APPS else "",
            basesql,
            sortsql,
        )

        # Build the python result
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    (
                        request.report_startdate,
                        request.report_enddate,
                        request.current_date,
                        request.report_bucket,
                    )
                    + baseparams,
                )
                itemattributefields = getAttributeFields(
                    Item, related_name_prefix="item"
                )
                locationattributefields = getAttributeFields(
                    Location, related_name_prefix="location"
                )

                prev_buffer = None
                for row in cursor_chunked:
                    numfields = len(row)
                    history = row[numfields - 4]
                    if prev_buffer != row[0] and not history:
                        order_backlog, forecast_backlog = startbacklogdict.get(
                            (row[1], row[2], row[22]), (0, 0)
                        )
                        prev_buffer = row[0]
                    if history:
                        order_backlog = None
                    else:
                        order_backlog += (float(row[numfields - 12] or 0)) - (
                            row[numfields - 2]["consumedSO"] or 0
                        )
                    if history:
                        forecast_backlog = None
                    else:
                        forecast_backlog += (float(row[numfields - 11] or 0)) - (
                            row[numfields - 2]["consumedFcst"] or 0
                        )

                    res = {
                        "buffer": row[0],
                        "item": row[1],
                        "location": row[2],
                        "item__description": row[3],
                        "item__type": row[4],
                        "item__category": row[5],
                        "item__subcategory": row[6],
                        "item__cost": row[7],
                        "item__volume": row[8],
                        "item__weight": row[9],
                        "item__uom": row[10],
                        "item__periodofcover": row[11],
                        "item__owner": row[12],
                        "item__source": row[13],
                        "item__lastmodified": row[14],
                        "location__description": row[15],
                        "location__category": row[16],
                        "location__subcategory": row[17],
                        "location__available": row[18],
                        "location__owner": row[19],
                        "location__source": row[20],
                        "location__lastmodified": row[21],
                        "batch": row[22],
                        "is_ip_buffer": row[23],
                        "color": (
                            None
                            if history
                            else (
                                round(
                                    (row[numfields - 8] or 0)
                                    * 100
                                    / float(row[numfields - 3])
                                )
                                if row[23]
                                and row[numfields - 3]
                                and float(row[numfields - 3]) > 0
                                else (
                                    round(row[numfields - 2]["max_delay"])
                                    if not row[23] and row[numfields - 2]["max_delay"]
                                    else 0
                                )
                            )
                        ),
                        "startoh": (row[numfields - 8] or 0),
                        "startohdoc": None if history else row[numfields - 1],
                        "bucket": row[numfields - 7],
                        "startdate": row[numfields - 6],
                        "enddate": row[numfields - 5],
                        "history": history,
                        "safetystock": (
                            row[numfields - 3] if history else row[numfields - 3] or 0
                        ),
                        "consumed": (
                            None if history else row[numfields - 2]["consumed"] or 0
                        ),
                        "consumed_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["consumed_confirmed"] or 0
                        ),
                        "consumed_proposed": (
                            None
                            if history
                            else row[numfields - 2]["consumed_proposed"] or 0
                        ),
                        "consumedMO": (
                            None if history else row[numfields - 2]["consumedMO"] or 0
                        ),
                        "consumedMO_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["consumedMO_confirmed"] or 0
                        ),
                        "consumedMO_proposed": (
                            None
                            if history
                            else row[numfields - 2]["consumedMO_proposed"] or 0
                        ),
                        "consumedDO": (
                            None if history else row[numfields - 2]["consumedDO"] or 0
                        ),
                        "consumedDO_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["consumedDO_confirmed"] or 0
                        ),
                        "consumedDO_proposed": (
                            None
                            if history
                            else row[numfields - 2]["consumedDO_proposed"] or 0
                        ),
                        "consumedSO": (
                            None if history else row[numfields - 2]["consumedSO"] or 0
                        ),
                        "consumedFcst": (
                            None if history else row[numfields - 2]["consumedFcst"] or 0
                        ),
                        "produced": (
                            None if history else row[numfields - 2]["produced"] or 0
                        ),
                        "produced_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["produced_confirmed"] or 0
                        ),
                        "produced_proposed": (
                            None
                            if history
                            else row[numfields - 2]["produced_proposed"] or 0
                        ),
                        "producedMO": (
                            None if history else row[numfields - 2]["producedMO"] or 0
                        ),
                        "producedMO_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["producedMO_confirmed"] or 0
                        ),
                        "producedMO_proposed": (
                            None
                            if history
                            else row[numfields - 2]["producedMO_proposed"] or 0
                        ),
                        "producedDO": (
                            None if history else row[numfields - 2]["producedDO"] or 0
                        ),
                        "producedDO_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["producedDO_confirmed"] or 0
                        ),
                        "producedDO_proposed": (
                            None
                            if history
                            else row[numfields - 2]["producedDO_proposed"] or 0
                        ),
                        "producedPO": (
                            None if history else row[numfields - 2]["producedPO"] or 0
                        ),
                        "producedPO_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["producedPO_confirmed"] or 0
                        ),
                        "producedPO_proposed": (
                            None
                            if history
                            else row[numfields - 2]["producedPO_proposed"] or 0
                        ),
                        "total_in_progress": (
                            None
                            if history
                            else row[numfields - 2]["total_in_progress"] or 0
                        ),
                        "total_in_progress_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["total_in_progress_confirmed"] or 0
                        ),
                        "total_in_progress_proposed": (
                            None
                            if history
                            else row[numfields - 2]["total_in_progress_proposed"] or 0
                        ),
                        "work_in_progress_mo": (
                            None
                            if history
                            else row[numfields - 2]["work_in_progress_mo"] or 0
                        ),
                        "work_in_progress_mo_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["work_in_progress_mo_confirmed"]
                            or 0
                        ),
                        "work_in_progress_mo_proposed": (
                            None
                            if history
                            else row[numfields - 2]["work_in_progress_mo_proposed"] or 0
                        ),
                        "on_order_po": (
                            None if history else row[numfields - 2]["on_order_po"] or 0
                        ),
                        "on_order_po_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["on_order_po_confirmed"] or 0
                        ),
                        "on_order_po_proposed": (
                            None
                            if history
                            else row[numfields - 2]["on_order_po_proposed"] or 0
                        ),
                        "proposed_ordering": (
                            None
                            if history
                            else row[numfields - 2]["proposed_ordering"] or 0
                        ),
                        "in_transit_do": (
                            None
                            if history
                            else row[numfields - 2]["in_transit_do"] or 0
                        ),
                        "in_transit_do_confirmed": (
                            None
                            if history
                            else row[numfields - 2]["in_transit_do_confirmed"] or 0
                        ),
                        "in_transit_do_proposed": (
                            None
                            if history
                            else row[numfields - 2]["in_transit_do_proposed"] or 0
                        ),
                        "total_demand": (
                            None
                            if history
                            else (row[numfields - 12] or 0) + (row[numfields - 11] or 0)
                        ),
                        "order_backlog": None if history else max(0, order_backlog),
                        "forecast_backlog": (
                            None if history else max(0, forecast_backlog)
                        ),
                        "total_backlog": (
                            None
                            if history
                            else max(0, forecast_backlog) + max(0, order_backlog)
                        ),
                        "endoh": (
                            None
                            if history
                            else (
                                float(row[numfields - 8] or 0)
                                + float(row[numfields - 2]["produced"] or 0)
                                - float(row[numfields - 2]["consumed"] or 0)
                            )
                        ),
                        "reasons": None if history else json.dumps(row[numfields - 9]),
                        "open_orders": None if history else row[numfields - 12] or 0,
                        "net_forecast": None if history else row[numfields - 11] or 0,
                    }

                    # Add attribute fields
                    idx = 24
                    for f in itemattributefields:
                        res[f.field_name] = row[idx]
                        idx += 1
                    for f in locationattributefields:
                        res[f.field_name] = row[idx]
                        idx += 1
                    yield res
