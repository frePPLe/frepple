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
from django.contrib.admin.utils import unquote
from django.db.models.expressions import RawSQL
from django.template import Template
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_text
from django.utils.text import format_lazy

from freppledb.boot import getAttributeFields
from freppledb.input.models import (
    Location,
    Customer,
    Demand,
    DeliveryOrder,
    Item,
    OperationPlan,
)
from freppledb.common.report import (
    GridReport,
    GridFieldLastModified,
    GridFieldDateTime,
    GridFieldText,
    GridFieldHierarchicalText,
    GridFieldNumber,
    GridFieldInteger,
    GridFieldCurrency,
    GridFieldChoice,
    GridFieldDuration,
)

import logging

logger = logging.getLogger(__name__)


class LocationList(GridReport):
    title = _("locations")
    basequeryset = Location.objects.all()
    model = Location
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/locations.html"
    message_when_empty = Template(
        """
        <h3>Define locations</h3>
        <br>
        A basic piece of master data is the list of locations where production is happening or inventory is kept.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/location/add/" class="btn btn-primary">Create a single location<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=1" class="btn btn-primary">Wizard to upload locations<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    rows = (
        GridFieldHierarchicalText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class CustomerList(GridReport):
    title = _("customers")
    basequeryset = Customer.objects.all()
    model = Customer
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/customers.html"
    message_when_empty = Template(
        """
        <h3>Define customers</h3>
        <br>
        A basic piece of master data is the customers buying items from us.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/customer/add/" class="btn btn-primary">Create a single customer<br> in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=1" class="btn btn-primary">Wizard to upload customers<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    rows = (
        GridFieldHierarchicalText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/customer"',
            model=Customer,
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class ItemList(GridReport):
    title = _("items")
    basequeryset = Item.objects.all()
    model = Item
    frozenColumns = 1
    editable = True
    help_url = "modeling-wizard/master-data/items.html"
    message_when_empty = Template(
        """
        <h3>Define items</h3>
        <br>
        A basic piece of master data is the list of items to plan.<br>
        End products, intermediate products and raw materials all need to be defined.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/item/add/" class="btn btn-primary">Create a single item<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=1" class="btn btn-primary">Wizard to upload items<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    rows = (
        GridFieldHierarchicalText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/item"',
            model=Item,
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldCurrency("cost", title=_("cost")),
        GridFieldNumber("weight", title=_("weight"), initially_hidden=True),
        GridFieldNumber("volume", title=_("volume"), initially_hidden=True),
        GridFieldChoice(
            "type", title=_("type"), choices=Item.types, initially_hidden=True
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class DemandList(GridReport):
    template = "input/demand.html"
    title = _("sales orders")
    model = Demand
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/sales-orders.html"
    message_when_empty = Template(
        """
        <h3>Define sales orders</h3>
        <br>
        The sales orders table contains all the orders placed by your customers.<br><br>
        Orders in the status "open" are still be delivered and will be planned.<br><br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/demand/add/" class="btn btn-primary">Create a single sales order<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=2" class="btn btn-primary">Wizard to upload sale orders<br>from a spreadsheet</a>
        </div>
        <br>
        """
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
            # Adding custom customer attributes
            for f in getAttributeFields(
                Customer, related_name_prefix="customer", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "customer.%s, " % f.name.split("__")[-1]
            # Adding custom demand attributes
            for f in getAttributeFields(Demand, initially_hidden=True):
                reportclass.rows += (f,)
                reportclass.attr_sql += "demand.%s, " % f.name.split("__")[-1]

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):

        q = Demand.objects.all()

        if "item" in request.GET:
            item = Item.objects.using(request.database).get(
                name__exact=unquote(request.GET["item"])
            )
            q = q.filter(item__lft__gte=item.lft, item__lft__lt=item.rght)
        if "location" in request.GET:
            location = Location.objects.using(request.database).get(
                name__exact=unquote(request.GET["location"])
            )
            q = q.filter(
                location__lft__gte=location.lft, location__lft__lt=location.rght
            )
        if "customer" in request.GET:
            customer = Customer.objects.using(request.database).get(
                name__exact=unquote(request.GET["customer"])
            )
            q = q.filter(customer_lft__gte=customer.lft, customer_lft__lt=customer.rght)
        if "status_in" in request.GET:
            status = unquote(request.GET["status_in"])
            q = q.filter(status__in=status.split(","))

        return q.annotate(plannedshort=RawSQL("quantity - plannedquantity", []))

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/demand"',
        ),
        GridFieldHierarchicalText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
            model=Item,
        ),
        GridFieldText("batch", title=_("batch"), initially_hidden=True),
        GridFieldHierarchicalText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
        ),
        GridFieldHierarchicalText(
            "customer",
            title=_("customer"),
            field_name="customer__name",
            formatter="detail",
            extra='"role":"input/customer"',
            model=Customer,
        ),
        GridFieldChoice("status", title=_("status"), choices=Demand.demandstatus),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldDateTime("due", title=_("due")),
        GridFieldDuration(
            "delay", title=_("delay"), editable=False, extra='"formatter":delayfmt'
        ),
        GridFieldNumber(
            "plannedquantity",
            title=_("planned quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "cellattr":plannedquantitycellattr',
        ),
        GridFieldNumber(
            "plannedshort",
            title=_("quantity planned short"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "cellattr":plannedquantitycellattr',
        ),
        GridFieldDateTime("deliverydate", title=_("delivery date"), editable=False),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "operation",
            title=_("delivery operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
            initially_hidden=True,
        ),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/demand"',
            initially_hidden=True,
        ),
        GridFieldDuration(
            "maxlateness", title=_("maximum lateness"), initially_hidden=True
        ),
        GridFieldNumber(
            "minshipment", title=_("minimum shipment"), initially_hidden=True
        ),
        GridFieldText(
            "batch", title=_("batch"), field_name="batch", initially_hidden=True
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
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
            formatter="detail",
            extra='"role":"input/item"',
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
        # Optional fields referencing the customer
        GridFieldText(
            "customer__description",
            title=format_lazy("{} - {}", _("customer"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "customer__category",
            title=format_lazy("{} - {}", _("customer"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "customer__subcategory",
            title=format_lazy("{} - {}", _("customer"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "customer__owner",
            title=format_lazy("{} - {}", _("customer"), _("owner")),
            initially_hidden=True,
            field_name="customer__owner__name",
            formatter="detail",
            extra='"role":"input/customer"',
            editable=False,
        ),
        GridFieldText(
            "customer__source",
            title=format_lazy("{} - {}", _("customer"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "customer__lastmodified",
            title=format_lazy("{} - {}", _("customer"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )

    if settings.ERP_CONNECTOR:
        actions = [
            {
                "name": "erp_incr_export",
                "label": format_lazy("export to {erp}", erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.SODepExport(jQuery('#grid'),'SO')",
            }
        ]
    else:
        actions = [
            {
                "name": "inquiry",
                "label": format_lazy(
                    _("change status to {status}"), status=_("inquiry")
                ),
                "function": "grid.setStatus('inquiry')",
            },
            {
                "name": "quote",
                "label": format_lazy(_("change status to {status}"), status=_("quote")),
                "function": "grid.setStatus('quote')",
            },
            {
                "name": "open",
                "label": format_lazy(_("change status to {status}"), status=_("open")),
                "function": "grid.setStatus('open')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed')",
            },
            {
                "name": "canceled",
                "label": format_lazy(
                    _("change status to {status}"), status=_("canceled")
                ),
                "function": "grid.setStatus('canceled')",
            },
        ]


class DeliveryOrderList(GridReport):
    template = "input/deliveryorder.html"
    title = _("delivery orders")
    model = DeliveryOrder
    frozenColumns = 0
    editable = True
    multiselect = True
    help_url = "model-reference/delivery-orders.html"
    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra='role:"input/deliveryorder"',
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
        ),
        GridFieldText(
            "demand",
            title=_("demand"),
            field_name="demand__name",
            formatter="detail",
            extra='"role":"input/demand"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "customer",
            title=_("customer"),
            field_name="demand__customer__name",
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldNumber("demand__quantity", title=_("demand quantity"), editable=False),
        GridFieldDateTime("startdate", title=_("start date")),
        GridFieldDateTime(
            "enddate",
            title=_("end date"),
            extra=GridFieldDateTime.extra + ',"cellattr":enddatecellattr',
        ),
        GridFieldDateTime(
            "due", field_name="demand__due", title=_("due date"), editable=False
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=OperationPlan.orderstatus,
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
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
        # Optional fields referencing the customer
        GridFieldText(
            "demand__customer__description",
            title=format_lazy("{} - {}", _("customer"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "demand__customer__category",
            title=format_lazy("{} - {}", _("customer"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "demand__customer__subcategory",
            title=format_lazy("{} - {}", _("customer"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "demand__customer__owner",
            title=format_lazy("{} - {}", _("customer"), _("owner")),
            initially_hidden=True,
            field_name="supplier__owner__name",
            formatter="detail",
            extra='"role":"input/supplier"',
            editable=False,
        ),
        GridFieldText(
            "demand__customer__source",
            title=format_lazy("{} - {}", _("customer"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "demand__customer__lastmodified",
            title=format_lazy("{} - {}", _("customer"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):

        q = DeliveryOrder.objects.all()

        # special keyword superop used for search field of operationplan
        if "parentreference" in request.GET:
            parentreference = request.GET["parentreference"]
            q = q.filter(reference=parentreference)

        if args and args[0]:
            path = request.path.split("/")[4]
            if path == "consumed":
                return q.filter(
                    item__name=args[0],
                    location__name=args[1],
                    enddate__gte=args[2],
                    enddate__lt=args[3],
                )
            else:
                try:
                    itm = Item.objects.all().using(request.database).get(name=args[0])
                    lft = itm.lft
                    rght = itm.rght
                except Item.DoesNotExist:
                    lft = 1
                    rght = 1
                q = q.filter(item__lft__gte=lft, item__rght__lte=rght)

        return q

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "deliveryorders"
            path = request.path.split("/")[4]
            if path == "consumed":
                return {
                    "active_tab": "deliveryorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("delivered from %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            else:
                return {
                    "active_tab": "deliveryorders",
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("delivery orders"),
                }
        else:
            return {"active_tab": "deliveryorders"}

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            for f in getAttributeFields(DeliveryOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                f.initially_hidden = True
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="location"):
                f.editable = False
                f.initially_hidden = True
                reportclass.rows += (f,)
            for f in getAttributeFields(
                Customer, related_name_prefix="demand__customer"
            ):
                f.editable = False
                f.initially_hidden = True
                reportclass.rows += (f,)
