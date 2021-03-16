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
from django.conf import settings
from django.contrib.admin.utils import unquote, quote
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import Cast
from django.db.models import F, Q, FloatField
from django.db.models.expressions import RawSQL
from django.shortcuts import redirect
from django.template import Template
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_text
from django.utils.text import format_lazy

from freppledb.boot import getAttributeFields
from freppledb.input.models import (
    Location,
    Buffer,
    Item,
    ItemDistribution,
    DistributionOrder,
    OperationPlanMaterial,
)
from freppledb.common.report import (
    GridReport,
    GridFieldBool,
    GridFieldLastModified,
    GridFieldDateTime,
    GridFieldText,
    GridFieldHierarchicalText,
    GridFieldNumber,
    GridFieldInteger,
    GridFieldCurrency,
    GridFieldChoice,
    GridFieldDuration,
    GridFieldJSON,
)
from .utils import OperationPlanMixin

import logging

logger = logging.getLogger(__name__)


@staff_member_required
def CreateOrEditBuffer(request, buffer_id):
    try:
        i = int(buffer_id)
        if Buffer.objects.all().using(request.database).filter(id=i).exists():
            return redirect(
                "%s/data/input/buffer/%s/change/" % (request.prefix, quote(buffer_id))
            )
    except Exception:
        pass
    i_l_b = unquote(buffer_id).split(" @ ")
    if len(i_l_b) == 0:
        return redirect("%s/data/input/buffer/add/" % request.prefix)
    elif len(i_l_b) == 1:
        return redirect(
            "%s/data/input/buffer/add/?item=%s" % (request.prefix, quote(i_l_b[0]))
        )
    elif len(i_l_b) == 2:
        try:
            buf = (
                Buffer.objects.all()
                .using(request.database)
                .get(item=i_l_b[0], location=i_l_b[1], batch__isnull=True)
            )
            return redirect(
                "%s/data/input/buffer/%s/change/" % (request.prefix, buf.id)
            )
        except Exception:
            return redirect(
                "%s/data/input/buffer/add/?item=%s&location=%s"
                % (request.prefix, quote(i_l_b[0]), quote(i_l_b[1]))
            )
    else:
        try:
            buf = (
                Buffer.objects.all()
                .using(request.database)
                .get(item=i_l_b[0], location=i_l_b[1], batch=i_l_b[2])
            )
            return redirect(
                "%s/data/input/buffer/%s/change/" % (request.prefix, buf.id)
            )
        except Exception:
            return redirect(
                "%s/data/input/buffer/add/?item=%s&location=%s&batch=%s"
                % (request.prefix, quote(i_l_b[0]), quote(i_l_b[1]), quote(i_l_b[2]))
            )


class BufferList(GridReport):
    title = _("buffers")
    basequeryset = Buffer.objects.all()
    model = Buffer
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/buffers.html"
    message_when_empty = Template(
        """
        <h3>Define buffers</h3>
        <br>
        A buffer is a (logical of physical) inventory point for an item at a certain location.<br><br>
        Use this table to define the on hand inventory or safety stocks.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/buffer/add/" class="btn btn-primary">Create a single buffer<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=7" class="btn btn-primary">Wizard to upload buffers<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/buffer"',
            initially_hidden=True,
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldHierarchicalText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "batch", title=_("batch"), field_name="batch", initially_hidden=True
        ),
        GridFieldNumber("onhand", title=_("onhand")),
        GridFieldChoice("type", title=_("type"), choices=Buffer.types),
        GridFieldNumber("minimum", title=_("minimum")),
        GridFieldText(
            "minimum_calendar",
            title=_("minimum calendar"),
            field_name="minimum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
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
    )


class ItemDistributionList(GridReport):
    title = _("item distributions")
    basequeryset = ItemDistribution.objects.all()
    model = ItemDistribution
    frozenColumns = 1
    help_url = "modeling-wizard/distribution/item-distributions.html"
    message_when_empty = Template(
        """
        <h3>Define item distributions</h3>
        <br>
        This table defines the possibility to transfer an item from one location to another.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/itemdistribution/add/" class="btn btn-primary">Create a single item distribution<br>in a form</a>
        </div>
        <br>
        """
    )

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/itemdistribution"',
            initially_hidden=True,
        ),
        GridFieldHierarchicalText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
            model=Item,
        ),
        GridFieldHierarchicalText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
        ),
        GridFieldHierarchicalText(
            "origin",
            title=_("origin"),
            field_name="origin__name",
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
        ),
        GridFieldDuration("leadtime", title=_("lead time")),
        GridFieldNumber("sizeminimum", title=_("size minimum")),
        GridFieldNumber("sizemultiple", title=_("size multiple")),
        GridFieldNumber("sizemaximum", title=_("size maximum"), initially_hidden=True),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldDuration("fence", title=_("fence"), initially_hidden=True),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
        GridFieldNumber(
            "resource_qty", title=_("resource quantity"), initially_hidden=True
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
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
        # Optional fields referencing the origin location
        GridFieldText(
            "origin__description",
            title=format_lazy("{} - {}", _("origin"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__category",
            title=format_lazy("{} - {}", _("origin"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__subcategory",
            title=format_lazy("{} - {}", _("origin"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__available",
            title=format_lazy("{} - {}", _("origin"), _("available")),
            initially_hidden=True,
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "origin__owner",
            title=format_lazy("{} - {}", _("origin"), _("owner")),
            initially_hidden=True,
            field_name="origin__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "origin__source",
            title=format_lazy("{} - {}", _("origin"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "origin__lastmodified",
            title=format_lazy("{} - {}", _("origin"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class DistributionOrderList(OperationPlanMixin, GridReport):
    template = "input/operationplanreport.html"
    title = _("distribution orders")
    default_sort = (1, "desc")
    model = DistributionOrder
    frozenColumns = 1
    multiselect = True
    editable = True
    height = 250
    help_url = "modeling-wizard/distribution/distribution-orders.html"
    message_when_empty = Template(
        """
        <h3>Define distribution orders</h3>
        <br>
        This table defines ongoing and proposed stock transfers between locations.<br><br>
        Use this table to load ongoing or frozen transfers in the status "confirmed".<br><br>
        The planning algorithm will further populate this table with additional "proposed" transfers for the future.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/distributionorder/add/" onclick="window.location = $(event.target).attr('href'); event.preventDefault();" class="btn btn-primary">Create a single distribution order<br>in a form</a>
        </div>
        <br>
        """
    )

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            paths = request.path.split("/")
            if paths[4] == "operationplanmaterial":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("in transit in %(loc)s at %(date)s")
                        % {"loc": args[1], "date": args[2]}
                    ),
                }
            elif paths[4] == "produced":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("received in %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            elif paths[4] == "consumed":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("shipped from %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            elif paths[4] == "item":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("distribution orders"),
                }
            elif paths[4] == "location":
                path = paths[-2]
                if path == "in":
                    return {
                        "active_tab": "inboundorders",
                        "model": Location,
                        "title": force_text(Location._meta.verbose_name)
                        + " "
                        + args[0],
                        "post_title": _("inbound distribution"),
                    }
                elif path == "out":
                    return {
                        "active_tab": "outboundorders",
                        "model": Location,
                        "title": force_text(Location._meta.verbose_name)
                        + " "
                        + args[0],
                        "post_title": _("outbound distribution"),
                    }
            else:
                return {"active_tab": "edit", "model": Item}
        else:
            return {"active_tab": "edit"}

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = DistributionOrder.objects.all()
        if args and args[0]:
            paths = request.path.split("/")
            if paths[4] == "operationplanmaterial":
                q = q.filter(Q(origin=args[1]) | Q(destination=args[1])).filter(
                    item__name=args[0], startdate__lt=args[2], enddate__gte=args[2]
                )
            elif paths[4] == "item":
                q = q.filter(item__name=args[0])
            elif paths[4] == "produced":
                q = q.filter(
                    destination__name=args[1],
                    item__name=args[0],
                    enddate__gte=args[2],
                    enddate__lt=args[3],
                )
            elif paths[4] == "consumed":
                q = q.filter(
                    origin__name=args[1],
                    item__name=args[0],
                    startdate__gte=args[2],
                    startdate__lt=args[3],
                )
            elif paths[4] == "location":
                path = paths[-2]
                if path == "out":
                    q = q.filter(origin_id=args[0])
                elif path == "in":
                    q = q.filter(destination_id=args[0])
        q = reportclass.operationplanExtraBasequery(q, request)
        return q.annotate(
            total_cost=Cast(F("item__cost") * F("quantity"), output_field=FloatField()),
            total_volume=Cast(
                F("item__volume") * F("quantity"), output_field=FloatField()
            ),
            total_weight=Cast(
                F("item__weight") * F("quantity"), output_field=FloatField()
            ),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
            computed_color=RawSQL(
                """
                case when operationplan.color >= 999999 and operationplan.plan ? 'item' then
                999999
                - extract(epoch from operationplan.delay)/86400.0
                + 1000000
                when operationplan.color >= 999999 and not(operationplan.plan ? 'item') then
                999999
                - extract(epoch from operationplan.delay)/86400.0
                else operationplan.color
                end
                """,
                [],
            ),
        )

    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra='role:"input/distributionorder"',
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldNumber(
            "computed_color",
            title=_("inventory status"),
            formatter="color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldNumber("color", hidden=True),
        GridFieldHierarchicalText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
            model=Item,
        ),
        GridFieldText(
            "origin",
            title=_("origin"),
            field_name="origin__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "destination",
            title=_("destination"),
            field_name="destination__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldDateTime(
            "startdate",
            title=_("shipping date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "enddate",
            title=_("receipt date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=DistributionOrder.orderstatus,
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldCurrency(
            "item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "item__volume",
            title=format_lazy("{} - {}", _("item"), _("volume")),
            initially_hidden=True,
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "item__weight",
            title=format_lazy("{} - {}", _("item"), _("weight")),
            initially_hidden=True,
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldCurrency(
            "total_cost",
            title=_("total cost"),
            editable=False,
            search=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "total_volume",
            title=_("total volume"),
            editable=False,
            search=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "total_weight",
            title=_("total weight"),
            editable=False,
            search=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
        ),
        GridFieldNumber(
            "criticality",
            title=_("criticality"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldJSON(
            "demands",
            title=_("demands"),
            editable=False,
            search=True,
            sortable=False,
            formatter="demanddetail",
            extra='"role":"input/demand"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=False,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
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
        # Optional fields referencing the origin location
        GridFieldText(
            "origin__description",
            title=format_lazy("{} - {}", _("origin"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__category",
            title=format_lazy("{} - {}", _("origin"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__subcategory",
            title=format_lazy("{} - {}", _("origin"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__available",
            title=format_lazy("{} - {}", _("origin"), _("available")),
            initially_hidden=True,
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "origin__owner",
            title=format_lazy("{} - {}", _("origin"), _("owner")),
            initially_hidden=True,
            field_name="origin__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "origin__source",
            title=format_lazy("{} - {}", _("origin"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "origin__lastmodified",
            title=format_lazy("{} - {}", _("origin"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the destination location
        GridFieldText(
            "destination__description",
            title=format_lazy("{} - {}", _("destination"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "destination__category",
            title=format_lazy("{} - {}", _("destination"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "destination__subcategory",
            title=format_lazy("{} - {}", _("destination"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "destination__available",
            title=format_lazy("{} - {}", _("destination"), _("available")),
            initially_hidden=True,
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "destination__owner",
            title=format_lazy("{} - {}", _("destination"), _("owner")),
            initially_hidden=True,
            field_name="origin__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "destination__source",
            title=format_lazy("{} - {}", _("destination"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "destination__lastmodified",
            title=format_lazy("{} - {}", _("destination"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "end_items",
            title=_("end items"),
            editable=False,
            search=False,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
    )

    if settings.ERP_CONNECTOR:
        actions = [
            {
                "name": "erp_incr_export",
                "label": format_lazy("export to {erp}", erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'DO')",
            }
        ]

    else:
        actions = [
            {
                "name": "proposed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("proposed")
                ),
                "function": "grid.setStatus('proposed')",
            },
            {
                "name": "approved",
                "label": format_lazy(
                    _("change status to {status}"), status=_("approved")
                ),
                "function": "grid.setStatus('approved')",
            },
            {
                "name": "confirmed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("confirmed")
                ),
                "function": "grid.setStatus('confirmed')",
            },
            {
                "name": "completed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("completed")
                ),
                "function": "grid.setStatus('completed')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed')",
            },
        ]

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            for f in getAttributeFields(DistributionOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="origin"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="destination"):
                f.editable = False
                reportclass.rows += (f,)


class InventoryDetail(OperationPlanMixin, GridReport):
    """
    A list report to show OperationPlanMaterial.
    """

    template = "input/operationplanreport.html"
    title = _("Inventory detail")
    model = OperationPlanMaterial
    permissions = (("view_inventory_report", "Can view inventory report"),)
    frozenColumns = 0
    editable = True
    multiselect = True
    height = 250
    help_url = "user-interface/plan-analysis/inventory-detail-report.html"
    message_when_empty = Template(
        """
        <h3>Inventory detail</h3>
        <br>
        This table has a list of all stock changes.<br><br>
        The planning algorithm will populate this table, and as a user you normally don't need to create records in this table.<br>
        <br>
        """
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if len(args) and args[0]:
            if request.path_info.startswith(
                "/data/input/operationplanmaterial/item/"
            ) or request.path_info.startswith("/detail/input/item/"):
                base = OperationPlanMaterial.objects.filter(item=args[0])

            elif request.path_info.startswith(
                "/data/input/operationplanmaterial/buffer/"
            ):
                i_b_l = args[0].split(" @ ")
                if len(i_b_l) == 1:
                    buffer = Buffer.objects.get(id=args[0])
                    base = OperationPlanMaterial.objects.filter(
                        item=buffer.item.name, location=buffer.location.name
                    )
                elif len(i_b_l) == 2:
                    base = OperationPlanMaterial.objects.filter(
                        item=i_b_l[0], location=i_b_l[1]
                    )
                else:
                    base = OperationPlanMaterial.objects.filter(
                        item=i_b_l[0], location=i_b_l[2], operationplan__batch=i_b_l[1]
                    )
        else:
            base = OperationPlanMaterial.objects
        base = reportclass.operationplanExtraBasequery(base, request)
        return base.select_related().annotate(
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            )
        )

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            if request.path_info.startswith(
                "/data/input/operationplanmaterial/item/"
            ) or request.path_info.startswith("/detail/input/item/"):
                request.session["lasttab"] = "inventorydetail"
                return {
                    "active_tab": "inventorydetail",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("inventory detail"),
                }
            elif request.path_info.startswith(
                "/data/input/operationplanmaterial/buffer/"
            ):
                request.session["lasttab"] = "plandetail"
                dlmtr = args[0].find(" @ ")
                if dlmtr != -1:
                    item = args[0][:dlmtr]
                    location = args[0][dlmtr + 3 :]
                else:
                    buffer = Buffer.objects.get(id=args[0])
                    item = buffer.item.name
                    location = buffer.location.name
                return {
                    "active_tab": "plandetail",
                    "model": Buffer,
                    "title": force_text(Buffer._meta.verbose_name)
                    + " "
                    + item
                    + " @ "
                    + location,
                    "post_title": _("plan detail"),
                }
        else:
            return {"active_tab": "plandetail", "model": OperationPlanMaterial}

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            editable=False,
            formatter="detail",
            extra='"role":"input/operationplanmaterial"',
            initially_hidden=True,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            editable=False,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            editable=False,
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText("operationplan__reference", title=_("reference"), editable=False),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="operationplan__owner__reference",
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__batch",
            title=_("batch"),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "color",
            title=_("inventory status"),
            formatter="color",
            field_name="operationplan__color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldText(
            "operationplan__type",
            title=_("type"),
            field_name="operationplan__type",
            editable=False,
        ),
        GridFieldText(
            "operationplan__name",
            title=_("operation"),
            editable=False,
            field_name="operationplan__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "operationplan__operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
        ),
        GridFieldInteger(
            "operationplan__operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "operationplan__operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
        ),
        GridFieldLastModified(
            "operationplan__operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "flowdate",
            title=_("date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "onhand",
            title=_("expected onhand"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "periodofcover",
            title=_("period of cover"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDateTime(
            "operationplan__startdate",
            title=_("start date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "operationplan__enddate",
            title=_("end date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldText(
            "operationplan__status",
            title=_("status"),
            editable=False,
            field_name="operationplan__status",
        ),
        GridFieldNumber(
            "operationplan__criticality",
            title=_("criticality"),
            field_name="operationplan__criticality",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            field_name="operationplan__delay",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "operationplan__quantity",
            title=_("operationplan quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText(
            "demands",
            title=_("demands"),
            formatter="demanddetail",
            extra='"role":"input/demand"',
            width=300,
            editable=False,
            sortable=False,
        ),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=False,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
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
        GridFieldChoice(
            "status",
            title=_("material status"),
            choices=OperationPlanMaterial.OPMstatus,
        ),
        GridFieldLastModified("lastmodified", initially_hidden=True),
    )
