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
from datetime import timedelta, datetime
import json

from django.conf import settings
from django.db import connections, transaction
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils.encoding import force_text
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
        GridFieldNumber("is_ip_buffer", title=_("is_ip_buffer"), hidden=True),
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
                "expand": ["consumedMO_proposed", "consumedDO_proposed", "consumedSO"],
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
                "initially_hidden": True,
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
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
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
                    "title": force_text(Buffer._meta.verbose_name)
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

        # Execute the actual query
        reasons_forecast = """
                union all
                select operationplan.item_id, operationplan.location_id, operationplan.due, operationplan.enddate, out_constraint.name, out_constraint.owner
                from out_constraint
                inner join operationplan on operationplan.forecast = out_constraint.forecast
                and operationplan.item_id = item.name and operationplan.location_id = location.name
                and operationplan.due < operationplan.enddate
        """
        query = """
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
           (item.name, location.name) in 
           (select plan->>'item', plan->>'location' 
           from operationplan 
           where item_id = item.name
           and coalesce(location_id, destination_id) = location.name) is_ip_buffer,
           %s
           (select json_agg(json_build_array(reasons.name, reasons.owner)) 
           from (
               select operationplan.item_id, operationplan.location_id, operationplan.due, operationplan.enddate, out_constraint.name, out_constraint.owner
                from out_constraint
                inner join operationplan on operationplan.item_id = item.name
                and operationplan.location_id = location.name
                and operationplan.demand_id = out_constraint.demand
                and operationplan.due < operationplan.enddate
                %s
                order by name limit 20
           ) reasons
           where (reasons.due , reasons.enddate) overlaps (d.startdate, d.enddate)) reasons,
           case
             when d.history then jsonb_build_object(
               'onhand', min(ax_buffer.onhand)
               )
           else coalesce(
             (
             select jsonb_build_object(
               'onhand', onhand,
               'flowdate', to_char(flowdate,'YYYY-MM-DD HH24:MI:SS'),
               'periodofcover', periodofcover
               )
             from operationplanmaterial
             inner join operationplan
               on operationplanmaterial.operationplan_id = operationplan.reference
             where operationplanmaterial.item_id = item.name
               and operationplanmaterial.location_id = location.name
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opplanmat.opplan_batch)
               and flowdate < greatest(d.startdate,%%s)
             order by flowdate desc, id desc limit 1
             ),
             (
             select jsonb_build_object(
               'onhand', 0.0,
               'flowdate', to_char(flowdate,'YYYY-MM-DD HH24:MI:SS'),
               'periodofcover', 1
               )
             from operationplanmaterial
             inner join operationplan
               on operationplanmaterial.operationplan_id = operationplan.reference
             where operationplanmaterial.item_id = item.name
               and operationplanmaterial.location_id = location.name
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opplanmat.opplan_batch)
               and flowdate >= greatest(d.startdate,%%s)
               and operationplanmaterial.quantity < 0
             order by flowdate asc, id asc limit 1
             ),
             (
             select jsonb_build_object(
               'onhand', 0.0,
               'flowdate', to_char(flowdate,'YYYY-MM-DD HH24:MI:SS'),
               'periodofcover', 1
               )
             from operationplanmaterial
             inner join operationplan
               on operationplanmaterial.operationplan_id = operationplan.reference
             where operationplanmaterial.item_id = item.name
               and operationplanmaterial.location_id = location.name
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opplanmat.opplan_batch)
               and flowdate >= greatest(d.startdate,%%s)
               and operationplanmaterial.quantity >= 0
             order by flowdate asc, id asc limit 1
             )
             )
           end as startoh,
           d.bucket,
           d.startdate,
           d.enddate,
           d.history,
           case when d.history then min(ax_buffer.safetystock)
           else
           (select safetystock from
            (
            select 1 as priority, coalesce(
              (select value from calendarbucket
               where calendar_id = 'SS for ' || opplanmat.buffer
               and greatest(d.startdate,%%s) >= startdate and greatest(d.startdate,%%s) < enddate
               order by priority limit 1),
              (select defaultvalue from calendar where name = 'SS for ' || opplanmat.buffer)
              ) as safetystock
            union all
            select 2 as priority, coalesce(
              (select value
               from calendarbucket
               where calendar_id = (
                 select minimum_calendar_id
                 from buffer
                 where item_id = item.name
                 and location_id = location.name
                 and (item.type is distinct from 'make to order' or buffer.batch is not distinct from opplanmat.opplan_batch)
                 )
               and greatest(d.startdate,%%s) >= startdate
               and greatest(d.startdate,%%s) < enddate
               order by priority limit 1),
              (select defaultvalue
               from calendar
               where name = (
                 select minimum_calendar_id
                 from buffer
                 where item_id = item.name
                 and location_id = location.name
                 and (item.type is distinct from 'make to order' or buffer.batch is not distinct from opplanmat.opplan_batch)
                 )
              )
            ) as safetystock
            union all
            select 3 as priority, minimum as safetystock
            from buffer
            where item_id = item.name
            and location_id = location.name
            and (item.type is distinct from 'make to order' or buffer.batch is not distinct from opplanmat.opplan_batch)
            ) t
            where t.safetystock is not null
            order by priority
            limit 1)
            end as safetystock,
            case when d.history then jsonb_build_object()
            else (
             select jsonb_build_object(
               'work_in_progress_mo', sum(case when (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'MO' then opm.quantity else 0 end),
               'work_in_progress_mo_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'MO' then opm.quantity else 0 end),
               'work_in_progress_mo_proposed', sum(case when operationplan.status = 'proposed' and operationplan.status = 'proposed' and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'MO' then opm.quantity else 0 end),
               'on_order_po', sum(case when (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'PO' then opm.quantity else 0 end),
               'on_order_po_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'PO' then opm.quantity else 0 end),
               'on_order_po_proposed', sum(case when operationplan.status = 'proposed' and operationplan.status = 'proposed' and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'PO' then opm.quantity else 0 end),
               'proposed_ordering', sum(case when operationplan.status = 'proposed' and operationplan.type = 'PO' and (operationplan.startdate >= greatest(d.startdate,%%s) and operationplan.startdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'in_transit_do', sum(case when (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'DO' then opm.quantity else 0 end),
               'in_transit_do_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'DO' then opm.quantity else 0 end),
               'in_transit_do_proposed', sum(case when operationplan.status = 'proposed' and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 and operationplan.type = 'DO' then opm.quantity else 0 end),
               'total_in_progress', sum(case when (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'total_in_progress_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'total_in_progress_proposed', sum(case when operationplan.status = 'proposed' and (startdate < d.enddate and enddate >= d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'consumed', sum(case when (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumed_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumed_proposed', sum(case when operationplan.status = 'proposed' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedMO', sum(case when operationplan.type = 'MO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedMO_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and operationplan.type = 'MO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedMO_proposed', sum(case when operationplan.status = 'proposed' and operationplan.type = 'MO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedDO', sum(case when operationplan.type = 'DO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedFcst', sum(case when operationplan.type = 'DLVR' and operationplan.demand_id is null and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedDO_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and operationplan.type = 'DO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedDO_proposed', sum(case when operationplan.status = 'proposed' and operationplan.type = 'DO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'consumedSO', sum(case when operationplan.type = 'DLVR' and operationplan.demand_id is not null and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end),
               'produced', sum(case when (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'produced_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'produced_proposed', sum(case when operationplan.status = 'proposed' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedMO', sum(case when operationplan.type = 'MO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedMO_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and operationplan.type = 'MO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedMO_proposed', sum(case when operationplan.status = 'proposed' and operationplan.type = 'MO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedDO', sum(case when operationplan.type = 'DO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedDO_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and operationplan.type = 'DO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedDO_proposed', sum(case when operationplan.status = 'proposed' and operationplan.type = 'DO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedPO', sum(case when operationplan.type = 'PO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedPO_confirmed', sum(case when operationplan.status in ('approved','confirmed','completed') and operationplan.status in ('approved','confirmed','completed') and operationplan.type = 'PO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'producedPO_proposed', sum(case when operationplan.status = 'proposed' and operationplan.type = 'PO' and (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end),
               'open_orders', sum(case when operationplan.type = 'DLVR' and operationplan.demand_id is not null and ((operationplan.due >= greatest(d.startdate,%%s) or (%%s >= d.startdate and %%s < d.enddate)) and operationplan.due < d.enddate) then -opm.quantity else 0 end),
               'net_forecast', sum(case when operationplan.type = 'DLVR' and operationplan.demand_id is null and ((operationplan.due >= greatest(d.startdate,%%s) or (%%s >= d.startdate and %%s < d.enddate)) and operationplan.due < d.enddate) then -opm.quantity else 0 end),
               'order_backlog', case when %%s >= d.startdate and %%s < d.enddate then sum(case when operationplan.type = 'DLVR' and operationplan.demand_id is not null and operationplan.due < %%s then -opm.quantity else 0 end) else -1 end,
               'forecast_backlog', case when %%s >= d.startdate and %%s < d.enddate then sum(case when operationplan.type = 'DLVR' and operationplan.demand_id is null and operationplan.due < %%s then -opm.quantity else 0 end) else -1 end,
               'max_delay', max(extract(epoch from case when opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate then operationplan.delay else interval '0 second' end) / 86400)
               )
             from operationplanmaterial opm
             inner join operationplan
             on operationplan.reference = opm.operationplan_id
               and ((startdate < d.enddate and enddate >= d.enddate)
               or (opm.flowdate >= greatest(d.startdate,%%s) and opm.flowdate < d.enddate)
               or (operationplan.type = 'DLVR' and due < d.enddate and due >= case when %%s >= d.startdate and %%s < d.enddate then '1970-01-01'::timestamp else d.startdate end))
             where opm.item_id = item.name
               and opm.location_id = location.name
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from opplanmat.opplan_batch)
             )
           end as ongoing,
           floor(extract(epoch from coalesce(
                  -- backlogged demand exceeds the inventory: 0 days of inventory
                  (
                  select '0 days'::interval
                  from operationplanmaterial
                  inner join operationplan on operationplanmaterial.operationplan_id = operationplan.reference
                  where operationplanmaterial.item_id = item.name and operationplanmaterial.location_id = location.name and
                    (
                      (operationplanmaterial.flowdate >= greatest(d.startdate,%%s) and operationplanmaterial.quantity < 0 and operationplan.type = 'DLVR' and operationplan.due < greatest(d.startdate,%%s))
                      or ( operationplanmaterial.quantity > 0 and operationplan.status = 'closed' and operationplan.type = 'STCK')
                      or ( operationplanmaterial.quantity > 0 and operationplan.status in ('approved','confirmed','completed') and flowdate <= greatest(d.startdate,%%s) + interval '1 second')
                    )
                  having sum(operationplanmaterial.quantity) <0
                  limit 1
                  ),
                  -- Normal case
                  (
                  select case
                    when periodofcover = 999 * 24 * 3600
                      then '999 days'::interval
                    when onhand > 0.00001
                      then date_trunc('day', least( periodofcover * '1 sec'::interval + flowdate - greatest(d.startdate,%%s), '999 days'::interval))
                    else null
                    end
                  from operationplanmaterial
                  where flowdate < greatest(d.startdate,%%s)
                    and operationplanmaterial.item_id = item.name and operationplanmaterial.location_id = location.name
                  order by flowdate desc, id desc
                  limit 1
                 ),
                 -- No inventory and no backlog: use the date of next consumer
                 (
                 select greatest('0 days'::interval, least( 
                     date_trunc('day', justify_interval(flowdate - greatest(d.startdate,%%s) - coalesce(operationplan.delay, '0 day'::interval))),
                     '999 days'::interval
                     ))
                  from operationplanmaterial
                  inner join operationplan on operationplanmaterial.operationplan_id = operationplan.reference
                  where operationplanmaterial.quantity < 0
                    and operationplanmaterial.item_id = item.name and operationplanmaterial.location_id = location.name
                  order by flowdate asc, id asc
                  limit 1
                 ),
                 '999 days'::interval
                 ))/86400) periodofcover
           from
           (%s) opplanmat
           inner join item on item.name = opplanmat.item_id
           inner join location on location.name = opplanmat.location_id
           -- Multiply with buckets
           cross join (
             select name as bucket, startdate, enddate,
               min(snapshot_date) as snapshot_date,
               enddate < %%s as history
             from common_bucketdetail
             left outer join ax_manager
               on snapshot_date >= common_bucketdetail.startdate
               and snapshot_date < common_bucketdetail.enddate
             where common_bucketdetail.bucket_id = %%s
               and common_bucketdetail.enddate > %%s
               and common_bucketdetail.startdate < %%s
             group by common_bucketdetail.name, common_bucketdetail.startdate, common_bucketdetail.enddate
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
           d.history
           order by %s, d.startdate
        """ % (
            reportclass.attr_sql,
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
                        request.report_startdate,  # startoh
                        request.report_startdate,
                        request.report_startdate,
                        request.report_startdate,
                        request.report_startdate,
                        request.report_startdate,  # safetystock
                    )
                    + (request.report_startdate,) * 27
                    + (request.current_date,) * 2
                    + (request.report_startdate,) * 1  # net forecast
                    + (request.current_date,) * 2  # net forecast
                    + (request.current_date,) * 3  # order_backlog
                    + (request.current_date,) * 3  # forecast_backlog
                    + (request.report_startdate,) * 1
                    + (request.current_date,) * 2  # ongoing
                    + (request.current_date,) * 6  # period of cover
                    + baseparams
                    + (  # opplanmat
                        request.current_date,
                        request.report_bucket,
                        request.report_startdate,
                        request.report_enddate,
                    ),  # bucket d
                )
                itemattributefields = getAttributeFields(
                    Item, related_name_prefix="item"
                )
                locationattributefields = getAttributeFields(
                    Location, related_name_prefix="location"
                )

                prev_buffer = None
                for row in cursor_chunked:
                    if prev_buffer != row[0]:
                        order_backlog = None
                        forecast_backlog = None
                        prev_buffer = row[0]
                    numfields = len(row)
                    history = row[numfields - 4]
                    if (
                        not history
                        and datetime.strptime(request.current_date, "%Y-%m-%d %H:%M:%S")
                        >= row[numfields - 6]
                        and datetime.strptime(request.current_date, "%Y-%m-%d %H:%M:%S")
                        < row[numfields - 5]
                    ):
                        order_backlog = (
                            (row[numfields - 2]["order_backlog"] or 0)
                            if order_backlog is None
                            else order_backlog
                        )
                        forecast_backlog = (
                            (row[numfields - 2]["forecast_backlog"] or 0)
                            if forecast_backlog is None
                            else forecast_backlog
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
                        "color": None
                        if history
                        else (
                            round(
                                (
                                    row[numfields - 8]["onhand"]
                                    if row[numfields - 8]
                                    else 0
                                )
                                * 100
                                / float(row[numfields - 3])
                            )
                            if row[23]
                            and row[numfields - 3]
                            and float(row[numfields - 3]) > 0
                            else round(row[numfields - 2]["max_delay"])
                            if not row[23] and row[numfields - 2]["max_delay"]
                            else 0
                        ),
                        "startoh": row[numfields - 8]["onhand"]
                        if row[numfields - 8]
                        else 0,
                        "startohdoc": None if history else row[numfields - 1],
                        "bucket": row[numfields - 7],
                        "startdate": row[numfields - 6],
                        "enddate": row[numfields - 5],
                        "history": history,
                        "safetystock": row[numfields - 3]
                        if history
                        else row[numfields - 3] or 0,
                        "consumed": None
                        if history
                        else row[numfields - 2]["consumed"] or 0,
                        "consumed_confirmed": None
                        if history
                        else row[numfields - 2]["consumed_confirmed"] or 0,
                        "consumed_proposed": None
                        if history
                        else row[numfields - 2]["consumed_proposed"] or 0,
                        "consumedMO": None
                        if history
                        else row[numfields - 2]["consumedMO"] or 0,
                        "consumedMO_confirmed": None
                        if history
                        else row[numfields - 2]["consumedMO_confirmed"] or 0,
                        "consumedMO_proposed": None
                        if history
                        else row[numfields - 2]["consumedMO_proposed"] or 0,
                        "consumedDO": None
                        if history
                        else row[numfields - 2]["consumedDO"] or 0,
                        "consumedDO_confirmed": None
                        if history
                        else row[numfields - 2]["consumedDO_confirmed"] or 0,
                        "consumedDO_proposed": None
                        if history
                        else row[numfields - 2]["consumedDO_proposed"] or 0,
                        "consumedSO": None
                        if history
                        else row[numfields - 2]["consumedSO"] or 0,
                        "consumedFcst": None
                        if history
                        else row[numfields - 2]["consumedFcst"] or 0,
                        "produced": None
                        if history
                        else row[numfields - 2]["produced"] or 0,
                        "produced_confirmed": None
                        if history
                        else row[numfields - 2]["produced_confirmed"] or 0,
                        "produced_proposed": None
                        if history
                        else row[numfields - 2]["produced_proposed"] or 0,
                        "producedMO": None
                        if history
                        else row[numfields - 2]["producedMO"] or 0,
                        "producedMO_confirmed": None
                        if history
                        else row[numfields - 2]["producedMO_confirmed"] or 0,
                        "producedMO_proposed": None
                        if history
                        else row[numfields - 2]["producedMO_proposed"] or 0,
                        "producedDO": None
                        if history
                        else row[numfields - 2]["producedDO"] or 0,
                        "producedDO_confirmed": None
                        if history
                        else row[numfields - 2]["producedDO_confirmed"] or 0,
                        "producedDO_proposed": None
                        if history
                        else row[numfields - 2]["producedDO_proposed"] or 0,
                        "producedPO": None
                        if history
                        else row[numfields - 2]["producedPO"] or 0,
                        "producedPO_confirmed": None
                        if history
                        else row[numfields - 2]["producedPO_confirmed"] or 0,
                        "producedPO_proposed": None
                        if history
                        else row[numfields - 2]["producedPO_proposed"] or 0,
                        "total_in_progress": None
                        if history
                        else row[numfields - 2]["total_in_progress"] or 0,
                        "total_in_progress_confirmed": None
                        if history
                        else row[numfields - 2]["total_in_progress_confirmed"] or 0,
                        "total_in_progress_proposed": None
                        if history
                        else row[numfields - 2]["total_in_progress_proposed"] or 0,
                        "work_in_progress_mo": None
                        if history
                        else row[numfields - 2]["work_in_progress_mo"] or 0,
                        "work_in_progress_mo_confirmed": None
                        if history
                        else row[numfields - 2]["work_in_progress_mo_confirmed"] or 0,
                        "work_in_progress_mo_proposed": None
                        if history
                        else row[numfields - 2]["work_in_progress_mo_proposed"] or 0,
                        "on_order_po": None
                        if history
                        else row[numfields - 2]["on_order_po"] or 0,
                        "on_order_po_confirmed": None
                        if history
                        else row[numfields - 2]["on_order_po_confirmed"] or 0,
                        "on_order_po_proposed": None
                        if history
                        else row[numfields - 2]["on_order_po_proposed"] or 0,
                        "proposed_ordering": None
                        if history
                        else row[numfields - 2]["proposed_ordering"] or 0,
                        "in_transit_do": None
                        if history
                        else row[numfields - 2]["in_transit_do"] or 0,
                        "in_transit_do_confirmed": None
                        if history
                        else row[numfields - 2]["in_transit_do_confirmed"] or 0,
                        "in_transit_do_proposed": None
                        if history
                        else row[numfields - 2]["in_transit_do_proposed"] or 0,
                        "open_orders": None
                        if history
                        else row[numfields - 2]["open_orders"] or 0,
                        "net_forecast": None
                        if history
                        else row[numfields - 2]["net_forecast"] or 0,
                        "total_demand": None
                        if history
                        else (row[numfields - 2]["net_forecast"] or 0)
                        + (row[numfields - 2]["open_orders"] or 0),
                        "order_backlog": 0
                        if order_backlog and order_backlog < 0
                        else order_backlog,
                        "forecast_backlog": 0
                        if forecast_backlog and forecast_backlog < 0
                        else forecast_backlog,
                        "total_backlog": (
                            (
                                0
                                if order_backlog and order_backlog < 0
                                else order_backlog
                            )
                            or 0
                        )
                        + (
                            (
                                0
                                if forecast_backlog and forecast_backlog < 0
                                else forecast_backlog
                            )
                            or 0
                        ),
                        "endoh": None
                        if history
                        else (
                            float(
                                row[numfields - 8]["onhand"]
                                if row[numfields - 8]
                                else 0
                            )
                            + float(row[numfields - 2]["produced"] or 0)
                            - float(row[numfields - 2]["consumed"] or 0)
                        ),
                        "reasons": None if history else json.dumps(row[numfields - 8]),
                    }

                    if order_backlog is not None:
                        order_backlog += (
                            (row[numfields - 2]["open_orders"] or 0)
                            - (
                                order_backlog
                                if datetime.strptime(
                                    request.current_date, "%Y-%m-%d %H:%M:%S"
                                )
                                >= row[numfields - 6]
                                and datetime.strptime(
                                    request.current_date, "%Y-%m-%d %H:%M:%S"
                                )
                                < row[numfields - 5]
                                else 0
                            )
                            - (row[numfields - 2]["consumedSO"] or 0)
                        )
                    if forecast_backlog is not None:
                        forecast_backlog += (
                            (row[numfields - 2]["net_forecast"] or 0)
                            - (
                                forecast_backlog
                                if datetime.strptime(
                                    request.current_date, "%Y-%m-%d %H:%M:%S"
                                )
                                >= row[numfields - 6]
                                and datetime.strptime(
                                    request.current_date, "%Y-%m-%d %H:%M:%S"
                                )
                                < row[numfields - 5]
                                else 0
                            )
                            - (
                                (row[numfields - 2]["consumed"] or 0)
                                - (row[numfields - 2]["consumedSO"] or 0)
                            )
                        )

                    # Add attribute fields
                    idx = 23
                    for f in itemattributefields:
                        res[f.field_name] = row[idx]
                        idx += 1
                    for f in locationattributefields:
                        res[f.field_name] = row[idx]
                        idx += 1
                    yield res
