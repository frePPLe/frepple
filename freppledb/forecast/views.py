#
# Copyright (C) 2023 by frePPLe bv
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

import itertools
import json

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.admin.utils import unquote
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.db import connections, transaction
from django.db.models import Q, F
from django.db.models.expressions import RawSQL
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseNotAllowed,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.utils.encoding import force_str
from django.utils.text import capfirst, format_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from freppledb.boot import getAttributeFields, getAttributes
from freppledb.forecast.models import Forecast, ForecastPlan, Measure, ForecastPlanView
from freppledb.common.models import Parameter, Comment, Bucket
from freppledb.common.report import (
    GridPivot,
    GridFieldText,
    GridFieldInteger,
    getCurrency,
    GridFieldHierarchicalText,
    getCurrentDate,
)
from freppledb.common.report import (
    GridReport,
    GridFieldBool,
    GridFieldLastModified,
    GridFieldChoice,
    GridFieldNumber,
    GridFieldDuration,
    GridFieldCurrency,
    GridFieldDateTime,
)
from freppledb.input.views import PathReport, DemandList
from freppledb.input.models import Demand, Item, Location, Customer, Buffer
from freppledb.output.models import Constraint
from freppledb.output.views import constraint, pegging
from freppledb.webservice.utils import getWebServiceContext

import logging

logger = logging.getLogger(__name__)


class ForecastList(GridReport):
    """
    A list report to show forecasts.
    """

    template = "admin/base_site_grid.html"
    title = _("forecast")
    basequeryset = Forecast.objects.all()
    model = Forecast
    frozenColumns = 1
    help_url = "model-reference/forecast.html"

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

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"forecast/forecast"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "customer",
            title=_("customer"),
            field_name="customer__name",
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldText("batch", title=_("batch"), initially_hidden=True),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldChoice("method", title=_("method"), choices=Forecast.methods),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldDuration(
            "maxlateness", title=_("maximum lateness"), initially_hidden=True
        ),
        GridFieldNumber(
            "minshipment", title=_("minimum shipment"), initially_hidden=True
        ),
        GridFieldBool("discrete", title=_("discrete")),
        GridFieldBool("planned", title=_("planned")),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
            initially_hidden=True,
        ),
        GridFieldNumber(
            "out_smape",
            title=_("estimated forecast error"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "out_method",
            title=_("calculated forecast method"),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "out_deviation",
            title=_("standard deviation of forecast error"),
            initially_hidden=True,
            editable=True,
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
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


class MeasureList(GridReport):
    template = "admin/base_site_grid.html"
    title = _("measures")
    basequeryset = Measure.objects.all()
    model = Measure
    help_url = "model-reference/forecast-measures.html"
    frozenColumns = 1
    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"forecast/measure"',
        ),
        GridFieldText("label", title=_("label")),
        GridFieldText("description", title=_("description")),
        GridFieldChoice("type", title=_("type"), choices=Measure.types),
        GridFieldChoice(
            "mode_past", title=_("mode in past periods"), choices=Measure.modes
        ),
        GridFieldChoice(
            "mode_future", title=_("mode in future periods"), choices=Measure.modes
        ),
        GridFieldBool("initially_hidden", title=_("initially hidden")),
        GridFieldChoice("formatter", title=_("format"), choices=Measure.formatters),
        GridFieldBool("discrete", title=_("discrete")),
        GridFieldNumber("defaultvalue", title=_("default value")),
        GridFieldText("compute_expression", title=_("compute expression")),
        GridFieldText("update_expression", title=_("update expression")),
        GridFieldText("overrides", title=_("override measure")),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class OverviewReport(GridPivot):
    """
    A report allowing easy editing of forecast numbers.
    """

    template = "forecast/forecast.html"
    title = _("forecast report")
    model = ForecastPlan
    permissions = (("view_forecast_report", "Can view forecast report"),)
    editable = True
    help_url = "user-interface/plan-analysis/forecast-report.html"
    default_sort = (1, "asc")

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if "name" in kwargs:
            fcst = Forecast.objects.filter(name=unquote(kwargs["name"])).annotate(
                forecast_id=F("name")
            )
            return fcst
        else:
            # All attributes need to be explicitly added since django doesn't see a foreign key relation
            attr = {
                "method": RawSQL(
                    """
                    coalesce((select method from forecast where item_id=forecastreport_view.item_id
                      and location_id = forecastreport_view.location_id and customer_id =
                      forecastreport_view.customer_id), 'aggregate')
                      """,
                    (),
                ),
                "out_method": RawSQL(
                    """
                    coalesce((select out_method from forecast where item_id=forecastreport_view.item_id
                      and location_id = forecastreport_view.location_id and customer_id =
                      forecastreport_view.customer_id), 'aggregate')
                      """,
                    (),
                ),
                "out_smape": RawSQL(
                    """
                    (select out_smape from forecast where item_id=forecastreport_view.item_id
                      and location_id = forecastreport_view.location_id and customer_id =
                      forecastreport_view.customer_id)
                    """,
                    (),
                ),
                "item__description": RawSQL(
                    "(select description from item where name=forecastreport_view.item_id)",
                    (),
                ),
                "item__lft": RawSQL(
                    "(select lft from item where name=forecastreport_view.item_id)", ()
                ),
                "item__category": RawSQL(
                    "(select category from item where name=forecastreport_view.item_id)",
                    (),
                ),
                "item__subcategory": RawSQL(
                    "(select subcategory from item where name=forecastreport_view.item_id)",
                    (),
                ),
                "item__owner": RawSQL(
                    "(select owner_id from item where name=forecastreport_view.item_id)",
                    (),
                ),
                "item__cost": RawSQL(
                    "(select cost from item where name=forecastreport_view.item_id)", ()
                ),
                "item__source": RawSQL(
                    "(select source from item where name=forecastreport_view.item_id)",
                    (),
                ),
                "item__lastmodified": RawSQL(
                    "(select lastmodified from item where name=forecastreport_view.item_id)",
                    (),
                ),
                "location__description": RawSQL(
                    "(select description from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__lft": RawSQL(
                    "(select lft from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__category": RawSQL(
                    "(select category from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__subcategory": RawSQL(
                    "(select subcategory from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__available": RawSQL(
                    "(select available_id from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__owner": RawSQL(
                    "(select owner_id from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__source": RawSQL(
                    "(select source from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "location__lastmodified": RawSQL(
                    "(select lastmodified from location where name=forecastreport_view.location_id)",
                    (),
                ),
                "customer__description": RawSQL(
                    "(select description from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
                "customer__lft": RawSQL(
                    "(select lft from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
                "customer__category": RawSQL(
                    "(select category from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
                "customer__subcategory": RawSQL(
                    "(select subcategory from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
                "customer__owner": RawSQL(
                    "(select owner_id from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
                "customer__source": RawSQL(
                    "(select source from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
                "customer__lastmodified": RawSQL(
                    "(select lastmodified from customer where name=forecastreport_view.customer_id)",
                    (),
                ),
            }
            for field_name, label, fieldtype, editable, hidden in getAttributes(Item):
                attr["item__%s" % field_name] = RawSQL(
                    "(select %s from item where name=forecastreport_view.item_id)"
                    % field_name,
                    (),
                )
            for field_name, label, fieldtype, editable, hidden in getAttributes(
                Location
            ):
                attr["location__%s" % field_name] = RawSQL(
                    "(select %s from location where name=forecastreport_view.location_id)"
                    % field_name,
                    (),
                )
            for field_name, label, fieldtype, editable, hidden in getAttributes(
                Customer
            ):
                attr["customer__%s" % field_name] = RawSQL(
                    "(select %s from customer where name=forecastreport_view.customer_id)"
                    % field_name,
                    (),
                )
            return ForecastPlanView.objects.order_by(
                "item_id", "location_id", "customer_id"
            ).annotate(**attr)

    @staticmethod
    def maxBucketLevel(request):
        bck = Parameter.getValue("forecast.calendar", request.database)
        try:
            x = (
                Bucket.objects.all()
                .using(request.database)
                .only("level")
                .get(name=bck)
                .level
            )
            return x
        except Exception:
            return 3  # Correspond with monthly buckets in our default bucket data

    rows = (
        GridFieldText(
            "forecast",
            title=_("forecast"),
            key=True,
            editable=False,
            field_name="name",
            formatter="forecastdetail",
            extra='"role":"forecast/forecast"',
        ),
        GridFieldHierarchicalText(
            "item",
            title=_("item"),
            field_name="item_id",
            editable=True,
            formatter="detail",
            extra='"role":"input/item"',
            model=Item,
        ),
        GridFieldHierarchicalText(
            "customer",
            title=_("customer"),
            editable=True,
            field_name="customer_id",
            formatter="detail",
            extra='"role":"input/customer"',
            model=Customer,
        ),
        GridFieldHierarchicalText(
            "location",
            title=_("location"),
            editable=True,
            field_name="location_id",
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
        ),
        GridFieldText(
            "method",
            title=_("forecast method"),
            field_name="method",
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "out_method",
            title=_("selected forecast method"),
            field_name="out_method",
            editable=False,
            initially_hidden=True,
        ),
        GridFieldNumber(
            "out_smape",
            title=_("estimated forecast error"),
            field_name="out_smape",
            editable=False,
            initially_hidden=True,
        ),
        # Optional fields referencing the item
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
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
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
        GridFieldBool("outlier", title="outlier", hidden=True, search=False),
        GridFieldBool(
            "hasForecastRecord", title="hasForecastRecord", hidden=True, search=False
        ),
        GridFieldText(
            "bucket",
            hidden=True,
            search=False,
        ),
        GridFieldDateTime(
            "startdate",
            hidden=True,
            search=False,
        ),
        GridFieldDateTime(
            "enddate",
            hidden=True,
            search=False,
        ),
    )

    @classmethod
    def crosses(reportclass, request, *args, **kwargs):
        request.measures = [
            m
            for m in itertools.chain(
                Measure.standard_measures(),
                Measure.objects.all().using(request.database),
            )
            # Forecast report doesn't have the "x-ago" measures
            if m.computed != "frontend"
        ]
        return [
            (
                m.name,
                {
                    "name": m.label or m.name,
                    "mode_future": m.mode_future,
                    "mode_past": m.mode_past,
                    "formatter": m.formatter,
                    "editable": m.mode_future == "edit" or m.mode_past == "edit",
                    "defaultvalue": (
                        float(m.defaultvalue) if m.defaultvalue is not None else 0
                    ),
                    "initially_hidden": m.initially_hidden,
                    "visible": m.mode_future != "hide" or m.mode_past != "hide",
                },
            )
            for m in request.measures
        ]

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom forecast attributes
            for f in getAttributeFields(Forecast, initially_hidden=True):
                reportclass.rows += (f,)
                reportclass.attr_sql += "forecast.%s, " % f.name.split("__")[-1]
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "item.%s,\n" % f.name.split("__")[-1]
            # Adding custom location attributes
            for f in getAttributeFields(
                Location, related_name_prefix="location", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "location.%s,\n" % f.name.split("__")[-1]
            # Adding custom customer attributes
            for f in getAttributeFields(
                Customer, related_name_prefix="customer", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "customer.%s,\n" % f.name.split("__")[-1]

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        ctx = getWebServiceContext(request)
        if args and args[0]:
            request.session["lasttab"] = "plan"
            ctx.update(
                {
                    "title": force_str(Forecast._meta.verbose_name) + " " + args[0],
                    "post_title": _("plan"),
                    "currency": json.dumps(getCurrency()),
                    "active_tab": "plan",
                }
            )
        else:
            ctx.update({"currency": json.dumps(getCurrency())})
        return ctx

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )
        cursor = connections[request.database].cursor()
        currentdate = getCurrentDate(request.database, lastplan=True)

        # Collect backlog information
        query = (
            """
            select
                fcst.name,
                coalesce(sum(forecastplan.ordersopen), 0)
                - coalesce(sum(forecastplan.ordersplanned), 0) as backlog_order,
                coalesce(sum(forecastplan.forecastnet), 0)
                - coalesce(sum(forecastplan.forecastplanned), 0) as backlog_forecast,
                coalesce(sum(forecastplan.ordersopenvalue), 0)
                - coalesce(sum(forecastplan.ordersplannedvalue), 0) as backlog_order_value,
                coalesce(sum(forecastplan.forecastnetvalue), 0)
                - coalesce(sum(forecastplan.forecastplannedvalue), 0) as backlog_forecast_value
            from (%s) fcst
            inner join forecastplan
                on fcst.item_id = forecastplan.item_id
                and fcst.location_id = forecastplan.location_id
                and fcst.customer_id = forecastplan.customer_id
            where startdate < (
                select min(startdate)
                from common_bucketdetail
                where bucket_id = %%s and enddate > %%s and startdate < %%s
                )
            group by fcst.name
            """
            % basesql
        )
        cursor.execute(
            query,
            baseparams
            + (request.report_bucket, request.report_startdate, request.report_enddate),
        )
        all_backlog = {
            row[0]: (row[1], row[2], row[3], row[4])
            for row in cursor.fetchall()
            if row[1] != 0 or row[2] != 0 or row[3] != 0 or row[4] != 0
        }

        # Collect main data
        query = """
            select
              fcstplan.name as forecast_id,
              fcstplan.item_id as item_id,
              fcstplan.customer_id as customer_id,
              fcstplan.location_id as location_id,
              fcstplan.method,
              fcstplan.out_method,
              fcstplan.out_smape,
              item.description as item_description,
              item.category as item_category,
              item.subcategory as item_subcategory,
              item.owner_id as item_owner,
              item.cost as item_cost,
              item.source as item_source,
              item.lastmodified as item_lastmodified,
              location.description as location_description,
              location.category as location_category,
              location.subcategory as location_subcategory,
              location.available_id as location_available,
              location.owner_id as location_owner,
              location.source as location_source,
              location.lastmodified as location_lastmodified,
              customer.description as customer_description,
              customer.category as customer_category,
              customer.subcategory as customer_subcategory,
              customer.owner_id as customer_owner,
              customer.source as customer_source,
              customer.lastmodified as customer_lastmodified,
              case when out_problem.description is null then 0 else 1 end outlier,
              (fcstplan.out_smape is not null) hasForecastRecord,
              d.bucket as cross1, d.startdate as cross2, d.enddate as cross3,
              %s
              %s
              from (%s) fcstplan
              cross join (
                 select name as bucket, startdate, enddate
                 from common_bucketdetail
                 where bucket_id = %%s and enddate > %%s and startdate < %%s
                 ) d
              -- Forecast plan
              left outer join forecastplan
                  on fcstplan.item_id = forecastplan.item_id
                  and fcstplan.location_id = forecastplan.location_id
                  and fcstplan.customer_id = forecastplan.customer_id
                  and forecastplan.startdate >= d.startdate
                  and forecastplan.startdate < d.enddate
              inner join item on
                  fcstplan.item_id = item.name
              inner join location on
                  fcstplan.location_id = location.name
              inner join customer on
                  fcstplan.customer_id = customer.name
            -- outliers
              left outer join out_problem on
                  out_problem.entity = 'forecast' and out_problem.name = 'outlier' and
                  out_problem.owner = fcstplan.item_id||' @ '||fcstplan.location_id||' @ '||fcstplan.customer_id||' - '||to_char(forecastplan.startdate,'YYYY-MM-DD')
              group by
              fcstplan.name,
              fcstplan.item_id,
              fcstplan.customer_id,
              fcstplan.location_id,
              fcstplan.method,
              fcstplan.out_method,
              fcstplan.out_smape,
              item.description,
              item.category,
              item.subcategory,
              item.owner_id,
              item.cost,
              item.source,
              item.lastmodified,
              location.description,
              location.category,
              location.subcategory,
              location.available_id,
              location.owner_id,
              location.source,
              location.lastmodified,
              customer.description,
              customer.category,
              customer.subcategory,
              customer.owner_id,
              customer.source,
              customer.lastmodified,
              case when out_problem.description is null then 0 else 1 end,
              d.bucket, d.startdate, d.enddate,
              %s
              order by %s, d.startdate
            """ % (
            reportclass.attr_sql,
            ",\n".join(
                [
                    (
                        "coalesce(sum(forecastplan.%s),0) as %s" % (m.name, m.name)
                        if m.defaultvalue != -1
                        else "sum(forecastplan.%s) as %s" % (m.name, m.name)
                    )
                    for m in request.measures
                    if not m.computed
                ]
            ),
            basesql,
            reportclass.attr_sql.strip()[:-1],  # need to remove the final comma
            sortsql,
        )

        # Build the python result
        fcst = None
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    baseparams
                    + (
                        request.report_bucket,
                        request.report_startdate,
                        request.report_enddate,
                    ),
                )
                for row in cursor_chunked:
                    if row[0] != fcst:
                        fcst = row[0]
                        (
                            backlogorder,
                            backlogforecast,
                            backlogordervalue,
                            backlogforecastvalue,
                        ) = all_backlog.get(fcst, (0, 0, 0, 0))
                        backlogorder = float(backlogorder)
                        backlogforecast = float(backlogforecast)
                        backlogordervalue = float(backlogordervalue)
                        backlogforecastvalue = float(backlogforecastvalue)
                        backlog = backlogorder + backlogforecast
                        backlogvalue = backlogordervalue + backlogforecastvalue
                    res = {
                        "forecast": row[0],
                        "item": row[1],
                        "customer": row[2],
                        "location": row[3],
                        "method": row[4],
                        "out_method": row[5],
                        "out_smape": row[6],
                        "item__description": row[7],
                        "item__category": row[8],
                        "item__subcategory": row[9],
                        "item__owner": row[10],
                        "item__cost": row[11],
                        "item__source": row[12],
                        "item__lastmodified": row[13],
                        "location__description": row[14],
                        "location__category": row[15],
                        "location__subcategory": row[16],
                        "location__available": row[17],
                        "location__owner": row[18],
                        "location__source": row[19],
                        "location__lastmodified": row[20],
                        "customer__description": row[21],
                        "customer__category": row[22],
                        "customer__subcategory": row[23],
                        "customer__owner": row[24],
                        "customer__source": row[25],
                        "customer__lastmodified": row[26],
                        "outlier": row[27],
                        "hasForecastRecord": row[28],
                        "bucket": row[29],
                        "startdate": row[30],
                        "enddate": row[31],
                    }

                    # Add attribute fields
                    idx = 32
                    for f in getAttributeFields(Forecast):
                        res[f.field_name] = row[idx]
                        idx += 1
                    for f in getAttributeFields(Item, related_name_prefix="item"):
                        res[f.field_name] = row[idx]
                        idx += 1
                    for f in getAttributeFields(
                        Location, related_name_prefix="location"
                    ):
                        res[f.field_name] = row[idx]
                        idx += 1
                    for f in getAttributeFields(
                        Customer, related_name_prefix="customer"
                    ):
                        res[f.field_name] = row[idx]
                        idx += 1

                    # Add all measures
                    for m in request.measures:
                        if not m.computed:
                            res[m.name] = (
                                float(row[idx])
                                if row[idx] is not None
                                else m.defaultvalue if m.defaultvalue != -1 else None
                            )
                            idx += 1

                    # Add measures computed in the backend
                    res["past"] = 1 if res["startdate"] < currentdate else 0
                    res["future"] = 1 if res["enddate"] > currentdate else 0
                    res["totaldemand"] = res["ordersopen"] + res["forecastnet"]
                    res["totaldemandvalue"] = res.get("ordersopenvalue", 0) + res.get(
                        "forecastnetvalue", 0
                    )
                    res["totalsupply"] = res["ordersplanned"] + res["forecastplanned"]
                    res["totalsupplyvalue"] = res.get(
                        "ordersplannedvalue", 0
                    ) + res.get("forecastplannedvalue", 0)
                    backlogorder += res["ordersopen"] - res["ordersplanned"]
                    res["backlogorder"] = (
                        backlogorder if abs(backlogorder) > 0.0001 else 0
                    )
                    backlogforecast += res["forecastnet"] - res["forecastplanned"]
                    res["backlogforecast"] = (
                        backlogforecast if abs(backlogforecast) > 0.0001 else 0
                    )
                    backlog = backlogorder + backlogforecast
                    res["backlog"] = backlog if abs(backlog) > 0.0001 else 0
                    backlogordervalue += res.get("ordersopenvalue", 0) - res.get(
                        "ordersplannedvalue", 0
                    )
                    res["backlogordervalue"] = (
                        backlogordervalue if abs(backlogordervalue) > 0.0001 else 0
                    )
                    backlogforecastvalue += res.get("forecastnetvalue", 0) - res.get(
                        "forecastplannedvalue", 0
                    )
                    res["backlogforecastvalue"] = (
                        backlogforecastvalue
                        if abs(backlogforecastvalue) > 0.0001
                        else 0
                    )
                    backlogvalue = backlogordervalue + backlogforecastvalue
                    res["backlogvalue"] = (
                        backlogvalue if abs(backlogvalue) > 0.0001 else 0
                    )

                    # Done
                    yield res

    @staticmethod
    def parseJSONupload(request):
        raise Exception("No longer used!!!")


class UpstreamForecastPath(PathReport):
    downstream = False
    objecttype = Forecast


class OrderReport(DemandList):
    """
    A list report to show demands.
    """

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = Demand.objects.using(request.database).all()

        if "forecast" in request.GET:
            fcst = Forecast.objects.using(request.database).get(
                name__exact=unquote(request.GET["forecast"])
            )
            q = Demand.objects.filter(
                item__lft__gte=fcst.item.lft,
                item__lft__lt=fcst.item.rght,
                customer__lft__gte=fcst.customer.lft,
                customer__lft__lt=fcst.customer.rght,
                location__lft__gte=fcst.location.lft,
                location__lft__lt=fcst.location.rght,
            )

        return q.annotate(plannedshort=RawSQL("quantity - plannedquantity", []))

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if "forecast" in request.GET:
            return {
                "title": force_str(_("sales orders"))
                + " - "
                + unquote(request.GET["forecast"])
            }
        else:
            item = None
            location = None
            customer = None
            thetitle = ""

            for i in request.GET:
                if not item and i.startswith("item"):
                    item = request.GET[i]
                elif not location and i.startswith("location"):
                    location = request.GET[i]
                elif not customer and i.startswith("customer"):
                    customer = request.GET[i]
            if item and location:
                thetitle = " - " + unquote(item) + " @ " + unquote(location)
            if customer:
                thetitle += " @ " + unquote(customer)

            return {"title": force_str(_("sales orders")) + thetitle}


class ConstraintReport(constraint.BaseReport):
    template = "forecast/constraint_forecast.html"

    detailmodel = Forecast

    detail_post_title = _("why short or late?")

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "constraint"
            return Constraint.objects.all().filter(demand__startswith=args[0])
        else:
            return Constraint.objects.all()


class PeggingReport(pegging.ReportByDemand):
    detailmodel = Forecast
    detail_post_title = _("plan detail")
    help_url = "user-interface/plan-analysis/demand-gantt-report.html"
    model = Forecast

    @classmethod
    def getBucketsQuery(reportclass, *args):
        return (
            """
            with demand as (
                select min(due) as due,
                jsonb_build_object(
                    'pegging',
                    jsonb_agg(
                    jsonb_build_object(
                        'opplan', reference,
                        'quantity', quantity
                    )
                    )
                    ) AS plan
                        FROM operationplan
                        WHERE type = 'DLVR' and forecast = %s
                        group by forecast
                ),
                cte as (
                    with recursive cte as
                        (
                            select 1 as level,
                            (coalesce(operationplan.item_id,'')||'/'||operationplan.reference)::varchar as path,
                            operationplan.reference::text as reference,
                            0::numeric as pegged_x,
                            operationplan.quantity::numeric as pegged_y
                            from operationplan
                                cross join demand
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
                        (select due from demand),
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
            (args[0],),
        )

    @classmethod
    def getQuery(reportclass, basequery):
        # Build the base query
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )
        return (
            """
          with demand as (
                select min(due) as due,
                jsonb_build_object(
                    'pegging',
                    jsonb_agg(
                    jsonb_build_object(
                        'opplan', reference,
                        'quantity', quantity
                    )
                    )
                    ) AS plan
                        FROM operationplan
                        WHERE type = 'DLVR' and forecast = %s
                        group by forecast
                ),
          cte as (
                with recursive cte as
                (
                select 1 as level,
                (coalesce(operationplan.item_id,'')||'/'||operationplan.reference)::varchar as path,
                operationplan.reference::text,
                0::numeric as pegged_x,
                operationplan.quantity::numeric as pegged_y,
                operationplan.owner_id
                from operationplan
                cross join demand
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
          """,
            baseparams,
        )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        return Forecast.objects.filter(name__exact=args[0]).values("name")

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "detail"
            return {
                "active_tab": "detail",
                "title": force_str(Forecast._meta.verbose_name) + " " + args[0],
                "post_title": _("plan detail"),
                "model": Forecast,
            }
        else:
            return {}


class ForecastEditor:
    help_url = "user-interface/plan-analysis/forecast-editor.html"

    @staticmethod
    def getMeasure(request):
        measurename = request.GET.get("measure", None)
        if not measurename:
            measurename = "forecasttotal"
        for x in Measure.standard_measures():
            if x.name == measurename:
                return measurename
        if (
            Measure.objects.all()
            .using(request.database)
            .filter(name=measurename)
            .exists()
        ):
            return measurename
        return "forecastnet"

    @staticmethod
    @staff_member_required
    def itemtree(request):
        # Check permissions
        if not request.user.has_perm("auth.view_forecast_report"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # Find requested intersection
        item = request.GET.get("item", None)
        location = request.GET.get("location", None)
        customer = request.GET.get("customer", None)
        if item:
            item = unquote(item)
        if location:
            location = unquote(location)
        if customer:
            customer = unquote(customer)

        # Measure to display in the top panels
        measurename = ForecastEditor.getMeasure(request)
        if not measurename:
            return HttpResponseForbidden("<h1>Invalid measure name</h1>")

        if item:
            if request.GET.get("first", None):
                itemfilter = "(item.name = %s or item.owner_id = %s)"
            else:
                itemfilter = "(item.owner_id = %s or item.owner_id = %s)"
        else:
            itemfilter = "(item.lvl in (%s,1) or item.lvl in (%s,1))"
            item = 0
        if location:
            locationfilter = "location.name = %s"
        else:
            locationfilter = "location.lvl = %s"
            location = 0
        if customer:
            customerfilter = "customer.name = %s"
        else:
            customerfilter = "customer.lvl = %s"
            customer = 0

        # TODO this query only returns 300 items. If there are more than 300, they are not visible from the forecast editor
        # Now that this is rendered in directive this is potentially not necessary any longer.
        query = """
            with all_recs as (
              select d.startdate, item.name as item_id, item.description, d.name,
              coalesce(sum(%s),0) val, item.rght-item.lft>1 flag, item.lvl
                from (
                  select name, startdate, enddate
                  from common_bucketdetail
                  where bucket_id = (
                    select name
                    from common_bucket
                    where level = (
                      select min(level)
                      from common_bucket
                      where name in (%%s, (select value from common_parameter where name='forecast.calendar'))
                      )
                    )
                  and enddate > %%s
                  order by startdate
                  limit 3
                  ) d
                cross join item
                cross join location
                cross join customer
                left outer join forecastplan
                  on forecastplan.startdate >= d.startdate
                  and forecastplan.startdate < d.enddate
                  and forecastplan.item_id = item.name
                  and forecastplan.location_id = location.name
                  and forecastplan.customer_id = customer.name
                where %s and %s and %s
                and exists (
                    select 1 from forecasthierarchy
                    where item_id = item.name
                    and location_id = location.name
                    and customer_id = customer.name
                )
                group by item.name, item.description, d.name, d.startdate, item.lvl, item.rght-item.lft>1
                )
                select all_recs.item_id, name, val, flag, lvl, description
                from all_recs
                inner join  (
                   select item_id, sum(val) as sum_val
                   from all_recs
                   group by item_id
                   order by sum(val) desc
                   limit 300
                   ) summary
                on all_recs.item_id = summary.item_id
                order by lvl, startdate, sum_val desc, all_recs.item_id
                """

        # Pick up the current date
        current = getCurrentDate(request.database, lastplan=True)

        # Execute the query
        cursor = connections[request.database].cursor()
        result = []
        result_idx = {}
        cursor.execute(
            query % (measurename, itemfilter, locationfilter, customerfilter),
            (
                request.user.horizonbuckets,
                current,
                item,
                item,
                location,
                customer,
            ),
        )
        for rec in cursor.fetchall():
            tmp = result_idx.get(rec[0], None)
            if tmp is not None:
                result[tmp]["values"].append(
                    {"bucketname": rec[1], "value": float(rec[2])}
                )
            else:
                result_idx[rec[0]] = len(result)
                result.append(
                    {
                        "item": rec[0],
                        "description": rec[5],
                        "values": [{"bucketname": rec[1], "value": float(rec[2])}],
                        "lvl": rec[4],
                        "children": rec[3],
                        "visible": True,
                        "expanded": 0,
                    }
                )
        return HttpResponse(
            content=json.dumps(result),
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
        )

    @staticmethod
    @staff_member_required
    def locationtree(request):
        # Check permissions
        if not request.user.has_perm("auth.view_forecast_report"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # Find requested intersection
        item = request.GET.get("item", None)
        location = request.GET.get("location", None)
        customer = request.GET.get("customer", None)
        if item:
            item = unquote(item)
        if location:
            location = unquote(location)
        if customer:
            customer = unquote(customer)

        # Measure to display in the top panels
        measurename = ForecastEditor.getMeasure(request)
        if not measurename:
            return HttpResponseForbidden("<h1>Invalid measure name</h1>")

        if item:
            itemfilter = "item.name = %s"
        else:
            itemfilter = "item.lvl = %s"
            item = 0
        if location:
            locationfilter = "location.owner_id = %s"
        else:
            locationfilter = "location.lvl in ( %s, 1 )"
            location = 0
        if customer:
            customerfilter = "customer.name = %s"
        else:
            customerfilter = "customer.lvl = %s"
            customer = 0

        query = """
          with all_recs as (
          select d.startdate, location.name lname, d.name bname,
          coalesce(sum(%s),0) val, location.rght-location.lft>1 flag, location.lvl, location.description
            from (
              select name, startdate, enddate
              from common_bucketdetail
              where bucket_id = (
                select name
                from common_bucket
                where level = (
                  select min(level)
                  from common_bucket
                  where name in (%%s, (select value from common_parameter where name='forecast.calendar'))
                  )
                )
              and enddate > %%s
              order by startdate
              limit 3
              ) d
            cross join item
            cross join location
            cross join customer
            left outer join forecastplan
              on forecastplan.startdate >= d.startdate
              and forecastplan.startdate < d.enddate
              and forecastplan.item_id = item.name
              and forecastplan.location_id = location.name
              and  forecastplan.customer_id = customer.name
            where %s and %s and %s
            and exists (
                select 1 from forecasthierarchy
                where item_id = item.name
                and location_id = location.name
                and customer_id = customer.name
                )
            group by location.name, d.name, d.startdate, location.lvl, location.rght-location.lft>1, location.description
          )
          select all_recs.lname, bname, val, flag, lvl, description
            from all_recs
            inner join  (
              select lname, sum(val) as sum_val
               from all_recs
               group by lname
               order by sum(val) desc
               limit 300
            ) summary
            on all_recs.lname = summary.lname
            order by all_recs.lvl, startdate, sum_val desc, all_recs.lname
          """

        # Pick up the current date
        current = getCurrentDate(request.database, lastplan=True)

        # Execute the query
        cursor = connections[request.database].cursor()
        result = []
        result_idx = {}
        cursor.execute(
            query % (measurename, itemfilter, locationfilter, customerfilter),
            (
                request.user.horizonbuckets,
                current,
                item,
                location,
                customer,
            ),
        )
        for rec in cursor.fetchall():
            tmp = result_idx.get(rec[0], None)
            if tmp is not None:
                result[tmp]["values"].append(
                    {"bucketname": rec[1], "value": float(rec[2])}
                )
            else:
                result_idx[rec[0]] = len(result)
                result.append(
                    {
                        "location": rec[0],
                        "values": [{"bucketname": rec[1], "value": float(rec[2])}],
                        "lvl": rec[4],
                        "children": rec[3],
                        "visible": True,
                        "expanded": 0,
                        "description": rec[5],
                    }
                )
        return HttpResponse(
            content=json.dumps(result),
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
        )

    @staticmethod
    @staff_member_required
    def customertree(request):
        # Check permissions
        if not request.user.has_perm("auth.view_forecast_report"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # Find requested intersection
        item = request.GET.get("item", None)
        location = request.GET.get("location", None)
        customer = request.GET.get("customer", None)
        if item:
            item = unquote(item)
        if location:
            location = unquote(location)
        if customer:
            customer = unquote(customer)

        # Measure to display in the top panels
        measurename = ForecastEditor.getMeasure(request)
        if not measurename:
            return HttpResponseForbidden("<h1>Invalid measure name</h1>")

        if item:
            itemfilter = "item.name = %s"
        else:
            itemfilter = "item.lvl = %s"
            item = 0
        if location:
            locationfilter = "location.name = %s"
        else:
            locationfilter = "location.lvl = %s"
            location = 0
        if customer:
            customerfilter = "customer.owner_id = %s"
        else:
            customerfilter = "customer.lvl in (%s,1)"
            customer = 0

        query = """
          with all_recs as (
          select d.startdate, customer.name cname, d.name bname,
          coalesce(sum(%s),0) val, customer.rght-customer.lft>1 flag, customer.lvl,
          customer.description
            from (
              select name, startdate, enddate
              from common_bucketdetail
              where bucket_id = (
                select name
                from common_bucket
                where level = (
                  select min(level)
                  from common_bucket
                  where name in (%%s, (select value from common_parameter where name='forecast.calendar'))
                  )
                )
              and enddate > %%s
              order by startdate
              limit 3
              ) d
            cross join item
            cross join location
            cross join customer
            left outer join forecastplan
              on forecastplan.startdate >= d.startdate
              and forecastplan.startdate < d.enddate
              and forecastplan.item_id = item.name
              and forecastplan.location_id = location.name
              and forecastplan.customer_id = customer.name
            where %s and %s and %s
            and exists (
                select 1 from forecasthierarchy
                where item_id = item.name
                and location_id = location.name
                and customer_id = customer.name
                )
            group by customer.name, d.name, d.startdate, customer.lvl, customer.rght-customer.lft>1,
            customer.description
          )
          select all_recs.cname, bname, val, flag, lvl, description
            from all_recs
            inner join  (
              select cname, sum(val) as sum_val
               from all_recs
               group by cname
               order by sum(val) desc
               limit 300
            ) summary
            on all_recs.cname = summary.cname
          order by lvl, startdate, sum_val desc, all_recs.cname
          """

        # Pick up the current date
        current = getCurrentDate(request.database, lastplan=True)

        # Execute the query
        cursor = connections[request.database].cursor()
        result = []
        result_idx = {}
        cursor.execute(
            query % (measurename, itemfilter, locationfilter, customerfilter),
            (
                request.user.horizonbuckets,
                current,
                item,
                location,
                customer,
            ),
        )
        for rec in cursor.fetchall():
            tmp = result_idx.get(rec[0], None)
            if tmp is not None:
                result[tmp]["values"].append(
                    {"bucketname": rec[1], "value": float(rec[2])}
                )
            else:
                result_idx[rec[0]] = len(result)
                result.append(
                    {
                        "customer": rec[0],
                        "values": [{"bucketname": rec[1], "value": float(rec[2])}],
                        "lvl": rec[4],
                        "children": rec[3],
                        "visible": True,
                        "expanded": 0,
                        "description": rec[5],
                    }
                )
        return HttpResponse(
            content=json.dumps(result),
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
        )

    @staticmethod
    @staff_member_required
    def detail(request):
        # Dispatch to the correct method
        if request.method == "GET":
            return ForecastEditor.getDetail(request)
        else:
            return HttpResponseNotAllowed(["get"])

    @staticmethod
    def getDetail(request):
        # Check permissions
        if not request.user.has_perm("auth.view_forecast_report"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # Find requested intersection
        item = request.GET.get("item", None)
        location = request.GET.get("location", None)
        customer = request.GET.get("customer", None)
        if item:
            item = unquote(item)
        if location:
            location = unquote(location)
        if customer:
            customer = unquote(customer)

        currency = getCurrency()

        # Use root objects when no specific node is specified.
        # If multiple root nodes exist, we pick the first one.
        if not item:
            try:
                item = (
                    Item.objects.all()
                    .using(request.database)
                    .filter(lvl=0)
                    .order_by("name")[0]
                    .name
                )
            except Exception:
                pass
        if not location:
            try:
                location = (
                    Location.objects.all()
                    .using(request.database)
                    .filter(lvl=0)
                    .order_by("name")[0]
                    .name
                )
            except Exception:
                pass
        if not customer:
            try:
                customer = (
                    Customer.objects.all()
                    .using(request.database)
                    .filter(lvl=0)
                    .order_by("name")[0]
                    .name
                )
            except Exception:
                pass

        # Verify we have an existing item, location and customer
        if not item or not customer or not location:
            return HttpResponseNotFound("Item, customer or location aren't specified")

        # Pick up the current date
        current = getCurrentDate(request.database, lastplan=True)

        request.measures = list(
            itertools.chain(
                Measure.standard_measures(),
                Measure.objects.all().using(request.database),
            )
        )
        sql_forecast = """
            with cte as (
              select d.bucket as bucket,
              forecastplan.item_id,
              forecastplan.location_id,
              forecastplan.customer_id,
              d.startdate,
              d.enddate,
              %s
              from (
                 select name as bucket, startdate, enddate, enddate > %%s as future
                 from common_bucketdetail
                 where bucket_id = %%s
                 and enddate >= %%s - interval '3.1 year'
                 and startdate <= (select max(startdate) from forecastplan)
                 ) d
              left outer join forecastplan
              on forecastplan.location_id = %%s
                and forecastplan.customer_id = %%s
                and forecastplan.item_id = %%s
                and forecastplan.startdate >= d.startdate
                and forecastplan.startdate < d.enddate
              -- Grouping
              group by d.bucket, d.startdate, d.enddate, forecastplan.item_id, forecastplan.location_id, forecastplan.customer_id
              )
              select cte.bucket,
                     cte.startdate,
                     cte.enddate,
                     case when out_problem.description is null then 0 else 1 end outlier,
                     %s
                     from cte
              left outer join out_problem on out_problem.entity = 'forecast' and out_problem.name = 'outlier' and
              lower(substr(out_problem.description,22)) = lower(cte.item_id||' @ '||cte.location_id||' @ '||cte.customer_id||' @ '||to_char(cte.startdate,'YYYY-MM-DD'))
              order by cte.startdate
              """ % (
            ",\n".join(
                [
                    (
                        "coalesce(sum(forecastplan.%s),0) as %s" % (m.name, m.name)
                        if not m.defaultvalue
                        else "sum(forecastplan.%s) as %s" % (m.name, m.name)
                    )
                    for m in request.measures
                    if not m.computed
                ]
            ),
            ", ".join(["cte.%s" % m.name for m in request.measures if not m.computed]),
        )

        result = {}

        # Get backlog info
        # Backlog is assumed to be zero.
        # We pull all buckets from the past as well, so we start from 0.
        backlogorder = 0
        backlogordervalue = 0
        backlogforecast = 0
        backlogforecastvalue = 0

        # Retrieve the forecast data
        cursor = connections[request.database].cursor()
        result_fcst = []
        cursor.execute(
            sql_forecast,
            (current, request.user.horizonbuckets, current, location, customer, item),
        )
        for rec in cursor.fetchall():
            res = {
                "bucket": rec[0],
                "startdate": rec[1].strftime("%Y-%m-%d %H:%M:%S"),
                "enddate": rec[2].strftime("%Y-%m-%d %H:%M:%S"),
                "year": int(rec[1].strftime("%Y")),
                "outlier": rec[3],
                "past": 1 if rec[1] < current else 0,
                "future": 1 if rec[2] > current else 0,
            }

            # Add all measures
            idx = 4
            for m in request.measures:
                if m.computed:
                    continue
                if m.defaultvalue == -1:
                    res[m.name] = float(rec[idx]) if rec[idx] is not None else None
                else:
                    res[m.name] = float(rec[idx])
                if res[m.name]:
                    # Limit number of significant digits, similar to the grid.formatNumber function
                    if res[m.name] > 100000:
                        res[m.name] = float("{:.0f}".format(res[m.name]))
                    elif res[m.name] > 10000:
                        res[m.name] = float("{:.1f}".format(res[m.name]))
                    elif res[m.name] > 1000:
                        res[m.name] = float("{:.2f}".format(res[m.name]))
                    elif res[m.name] > 100:
                        res[m.name] = float("{:.3f}".format(res[m.name]))
                    elif res[m.name] > 10:
                        res[m.name] = float("{:.4f}".format(res[m.name]))
                    elif res[m.name] > 1:
                        res[m.name] = float("{:.5f}".format(res[m.name]))
                    else:
                        res[m.name] = float("{:.6f}".format(res[m.name]))
                idx += 1
            result_fcst.append(res)

            # Add computed summary fields
            res["totaldemand"] = res["ordersopen"] + res["forecastnet"]
            res["totaldemandvalue"] = res.get("ordersopenvalue", 0) + res.get(
                "forecastnetvalue", 0
            )
            res["totalsupply"] = res["ordersplanned"] + res["forecastplanned"]
            res["totalsupplyvalue"] = res.get("ordersplannedvalue", 0) + res.get(
                "forecastplannedvalue", 0
            )
            backlogorder += res["ordersopen"] - res["ordersplanned"]
            res["backlogorder"] = backlogorder if abs(backlogorder) > 0.0001 else 0
            backlogforecast += res["forecastnet"] - res["forecastplanned"]
            res["backlogforecast"] = (
                backlogforecast if abs(backlogforecast) > 0.0001 else 0
            )
            backlog = backlogorder + backlogforecast
            res["backlog"] = backlog if abs(backlog) > 0.0001 else 0
            backlogordervalue += res.get("ordersopenvalue", 0) - res.get(
                "ordersplannedvalue", 0
            )
            res["backlogordervalue"] = (
                backlogordervalue if abs(backlogordervalue) > 0.0001 else 0
            )
            backlogforecastvalue += res.get("forecastnetvalue", 0) - res.get(
                "forecastplannedvalue", 0
            )
            res["backlogforecastvalue"] = (
                backlogforecastvalue if abs(backlogforecastvalue) > 0.0001 else 0
            )
            backlogvalue = backlogordervalue + backlogforecastvalue
            res["backlogvalue"] = backlogvalue if abs(backlogvalue) > 0.0001 else 0

        result["forecast"] = result_fcst

        # Retrieve the comment data
        customer_type = ContentType.objects.get_for_model(Customer)
        item_type = ContentType.objects.get_for_model(Item)
        location_type = ContentType.objects.get_for_model(Location)
        buffer_type = ContentType.objects.get_for_model(Buffer)
        item_obj = (
            Item.objects.only("lft", "rght").using(request.database).get(name=item)
        )
        location_obj = (
            Location.objects.only("lft", "rght")
            .using(request.database)
            .get(name=location)
        )
        customer_obj = (
            Customer.objects.only("lft", "rght")
            .using(request.database)
            .get(name=customer)
        )

        # No hierarchy for the itemlocation comments
        buffer_pk = "%s @ %s" % (item, location)

        comments = (
            Comment.objects.using(request.database)
            .filter(
                Q(
                    content_type=customer_type.id,
                    object_pk__in=[
                        i["name"]
                        for i in Customer.objects.using(request.database)
                        .filter(lft__gte=customer_obj.lft or 0)
                        .filter(lft__lt=customer_obj.rght or 0)
                        .values("name")
                    ],
                )
                | Q(
                    content_type=customer_type.id,
                    object_pk__in=[
                        i["name"]
                        for i in Customer.objects.using(request.database)
                        .filter(lft__lte=customer_obj.lft or 0)
                        .filter(rght__gt=customer_obj.lft or 0)
                        .values("name")
                    ],
                )
                | Q(
                    content_type=item_type.id,
                    object_pk__in=[
                        i["name"]
                        for i in Item.objects.using(request.database)
                        .filter(lft__gte=item_obj.lft or 0)
                        .filter(lft__lt=item_obj.rght or 0)
                        .values("name")
                    ],
                )
                | Q(
                    content_type=item_type.id,
                    object_pk__in=[
                        i["name"]
                        for i in Item.objects.using(request.database)
                        .filter(lft__lte=item_obj.lft or 0)
                        .filter(rght__gt=item_obj.lft or 0)
                        .values("name")
                    ],
                )
                | Q(
                    content_type=location_type.id,
                    object_pk__in=[
                        i["name"]
                        for i in Location.objects.using(request.database)
                        .filter(lft__gte=location_obj.lft or 0)
                        .filter(lft__lt=location_obj.rght or 0)
                        .values("name")
                    ],
                )
                | Q(
                    content_type=location_type.id,
                    object_pk__in=[
                        i["name"]
                        for i in Location.objects.using(request.database)
                        .filter(lft__lte=location_obj.lft or 0)
                        .filter(rght__gt=location_obj.lft or 0)
                        .values("name")
                    ],
                )
                | Q(
                    content_type=buffer_type.id,
                    object_pk=buffer_pk,
                )
            )
            .filter(type="comment")
            .order_by("-lastmodified")
        )
        result_comment = []
        for i in comments:
            if i.content_type == customer_type:
                t = "customer %s" % (i.object_pk,)
            elif i.content_type == item_type:
                t = "item %s" % (i.object_pk,)
            elif i.content_type == buffer_type:
                t = "itemlocation %s" % (i.object_pk,)
            else:
                t = "location %s" % (i.object_pk,)
            result_comment.append(
                {
                    "user": (
                        "%s (%s)" % (i.user.username, i.user.get_full_name())
                        if i.user
                        else None
                    ),
                    "lastmodified": str(i.lastmodified),
                    "comment": i.comment,
                    "type": t,
                }
            )
        result["comments"] = result_comment

        # Retrieve history
        history = (
            LogEntry.objects.using(request.database)
            .filter(
                Q(content_type=customer_type.id, object_id=customer)
                | Q(content_type=item_type.id, object_id=item)
                | Q(content_type=location_type.id, object_id=location)
            )
            .order_by("-action_time")[:20]
        )
        result_history = []
        for i in history:
            result_history.append(
                {
                    "user": (
                        "%s (%s)" % (i.user.username, i.user.get_full_name())
                        if i.user
                        else None
                    ),
                    "object_id": i.object_id,
                    "content_type": i.content_type.name,
                    "change_message": i.change_message,
                    "action_time": str(i.action_time),
                }
            )
        result["history"] = result_history

        # Auxilary function to return attributes
        def addAttributeValues(attr, obj, cls):
            for field_name, label, fieldtype, editable, hidden in getAttributes(cls):
                if fieldtype == "string" or fieldtype.startswith("foreignkey:"):
                    attr.append(
                        [capfirst(force_str(label)), getattr(obj, field_name, None)]
                    )
                elif fieldtype == "boolean":
                    attr.append(
                        [capfirst(force_str(label)), getattr(obj, field_name, False)]
                    )
                elif fieldtype == "number":
                    if label.startswith("sales value"):
                        attr.append(
                            [
                                capfirst(force_str(label)),
                                currency[0]
                                + str(float(getattr(obj, field_name, 0) or 0))
                                + currency[1],
                            ]
                        )
                    else:
                        attr.append(
                            [
                                capfirst(force_str(label)),
                                float(getattr(obj, field_name, 0) or 0),
                            ]
                        )
                elif fieldtype == "integer":
                    attr.append(
                        [
                            capfirst(force_str(label)),
                            int(getattr(obj, field_name, 0) or 0),
                        ]
                    )
                elif fieldtype == "date":
                    v = getattr(obj, field_name, None)
                    attr.append(
                        [
                            capfirst(force_str(label)),
                            v.strftime("%Y-%m-%d") if v else None,
                        ]
                    )
                elif fieldtype == "datetime":
                    v = getattr(obj, field_name, None)
                    attr.append(
                        [
                            capfirst(force_str(label)),
                            v.strftime("%Y-%m-%d %H:%M:%S") if v else None,
                        ]
                    )
                elif fieldtype == "duration":
                    v = getattr(obj, field_name, None)
                    attr.append(
                        [
                            capfirst(force_str(label)),
                            round(v.total_seconds() / 86400) if v is not None else None,
                        ]
                    )
                elif fieldtype == "time":
                    attr.append(
                        [capfirst(force_str(label)), int(getattr(obj, field_name, 0))]
                    )
                else:
                    raise Exception("Invalid attribute type '%s'." % fieldtype)

        # Retrieve attributes
        result_attr = {}
        item_obj = Item.objects.all().using(request.database).get(pk=item)
        result_attr["item"] = [
            [capfirst(force_str(_("name"))), item],
            [capfirst(force_str(_("description"))), item_obj.description],
            [capfirst(force_str(_("category"))), item_obj.category],
            [capfirst(force_str(_("subcategory"))), item_obj.subcategory],
            [
                capfirst(force_str(_("cost"))),
                currency[0] + " " + str(float(item_obj.cost or 0)) + " " + currency[1],
            ],
        ]
        addAttributeValues(result_attr["item"], item_obj, Item)
        location_obj = Location.objects.all().using(request.database).get(pk=location)
        result_attr["location"] = [
            [capfirst(force_str(_("name"))), location],
            [capfirst(force_str(_("description"))), location_obj.description],
            [capfirst(force_str(_("category"))), location_obj.category],
            [capfirst(force_str(_("subcategory"))), location_obj.subcategory],
        ]
        addAttributeValues(result_attr["location"], location_obj, Location)
        customer_obj = Customer.objects.all().using(request.database).get(pk=customer)
        result_attr["customer"] = [
            [capfirst(force_str(_("name"))), customer],
            [capfirst(force_str(_("description"))), customer_obj.description],
            [capfirst(force_str(_("category"))), customer_obj.category],
            [capfirst(force_str(_("subcategory"))), customer_obj.subcategory],
        ]
        forecast_obj = (
            Forecast.objects.using(request.database)
            .filter(item=item, location=location, customer=customer)
            .first()
        )
        if forecast_obj:
            result_attr["forecast"] = {
                "forecastmethod": forecast_obj.method,
                "forecast_out_method": forecast_obj.out_method,
                "forecast_out_smape": round(float(forecast_obj.out_smape or 0)),
            }
        else:
            result_attr["forecast"] = {
                "forecastmethod": "aggregate",
                "forecast_out_method": "aggregate",
                "forecast_out_smape": 0,
            }
        result_attr["currency"] = currency
        result["attributes"] = result_attr

        return HttpResponse(
            content=json.dumps(result),
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
        )

    @staticmethod
    @staff_member_required
    def planning(request, item=None):
        # Check permissions
        if not request.user.has_perm("auth.view_forecast_report"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # Find allowed time bucket list
        cursor = connections[request.database].cursor()
        cursor.execute(
            """
            select level from common_bucket
            inner join common_parameter
              on common_parameter.name = 'forecast.calendar'
            where common_bucket.name = common_parameter.value
            """
        )
        singleRecord = cursor.fetchone()
        minbucketLevel = singleRecord[0] if singleRecord else 4
        bucketlevels = (
            Bucket.objects.order_by("-level")
            .filter(level__lte=minbucketLevel)
            .values_list("name", flat=True)
        )

        # Find time buckets for the current view
        if request.user.horizonbuckets and request.user.horizonbuckets in bucketlevels:
            # User selected value is valid
            bucketName = request.user.horizonbuckets
        elif bucketlevels:
            # Default to the most detailed allowed view
            bucketName = bucketlevels[0]
            request.user.horizonbuckets = bucketlevels[0]
            request.user.save()
        else:
            return HttpResponseServerError(
                "No time buckets found. Please generate the forecast first."
            )

        # Find the current date and current bucket
        currentdate = getCurrentDate(request.database, lastplan=True).date()
        cursor.execute(
            """
            select name
            from common_bucketdetail
            where %s >= startdate and %s < enddate
            and bucket_id = %s
            """,
            (currentdate, currentdate, bucketName),
        )
        singleRecord = cursor.fetchone()
        currentbucket = singleRecord[0] if singleRecord else "No bucket"

        sql_bucketsperyear = """
            select EXTRACT(YEAR from date_trunc('year', enddate))::INTEGER, count(distinct name)
            from common_bucketdetail
            where bucket_id = %s
              and enddate >= date_trunc('year', %s) - interval '3 year'
              and enddate <= %s + interval '1 year'
            group by date_trunc('year', enddate)
            order by date_trunc('year', enddate)
            """

        # retrieve buckets per year
        cursor.execute(sql_bucketsperyear, (bucketName, currentdate, currentdate))
        bucketsperyear = []

        for rec in cursor.fetchall():
            bucketsperyear.append(json.dumps({"year": rec[0], "bucketcount": rec[1]}))

        # Create a list of measures
        measures = {
            m.name: {
                "name": m.name,
                "label": force_str(m.label or m.name),
                "mode_future": m.mode_future,
                "mode_past": m.mode_past,
                "formatter": m.formatter,
                "editable": m.mode_future == "edit" or m.mode_past == "edit",
                "initially_hidden": m.initially_hidden,
                "computed": m.computed,
                "defaultvalue": float(m.defaultvalue),
                "discrete": m.discrete or False,
            }
            for m in itertools.chain(
                Measure.standard_measures(),
                Measure.objects.all().using(request.database),
            )
        }

        ctx = getWebServiceContext(request)
        ctx.update(
            {
                "bucketnames": bucketlevels,
                "bucketsperyear": "[" + ",".join(bucketsperyear) + "]",
                "title": "%s%s"
                % (_("Forecast editor"), ((" %s" % (unquote(item),)) if item else "")),
                "preferences": request.user.getPreference(
                    "freppledb.forecast.planning", database=request.database
                ),
                "currentbucket": currentbucket,
                "currentdate": currentdate.strftime("%Y-%m-%d"),
                "measures": json.dumps(measures),
                "reportclass": ForecastEditor,
            }
        )
        return render(
            request,
            "forecast.html",
            context=ctx,
        )


class ForecastWizard(View):
    title = _("forecast wizard")

    help_url = "modeling-wizard/master-data/sales-orders.html"  # TODO

    @classmethod
    def has_permission(cls, user):
        return user.has_perm("auth.view_forecast_report")

    @staticmethod
    @staff_member_required
    def get(request):
        # Check permissions
        if not request.user.has_perm("auth.view_forecast_report"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))
        return render(
            request,
            "forecast/wizard.html",
            context={
                "title": _("forecast wizard"),
                "reportkey": "freppledb.forecast.wizard",
                "preferences": request.user.getPreference(
                    "freppledb.forecast.wizard", database=request.database
                ),
            },
        )

    @staticmethod
    def post(request):
        # Check permissions
        if not request.user.has_perm("forecast.add_forecastplan"):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        return HttpResponse(content="OK")
