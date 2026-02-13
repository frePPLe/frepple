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

from collections import OrderedDict
from sys import maxsize

from django.conf import settings
from django.db.models import F, Q, DateTimeField, DurationField, FloatField
from django.db.models.functions import Cast
from django.db.models.expressions import RawSQL
from django.template import Template
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.utils.text import format_lazy

from freppledb.boot import getAttributeFields
from freppledb.input.models import (
    Resource,
    Location,
    Item,
    Operation,
    OperationDependency,
    OperationResource,
    OperationMaterial,
    Calendar,
    CalendarBucket,
    ManufacturingOrder,
    WorkOrder,
    SubOperation,
    searchmode,
    OperationPlan,
)
from freppledb.common.report import (
    GridReport,
    GridFieldBool,
    GridFieldLastModified,
    GridFieldDateTime,
    GridFieldDateTimeFull,
    GridFieldTime,
    GridFieldText,
    GridFieldHierarchicalText,
    GridFieldNumber,
    GridFieldInteger,
    GridFieldCurrency,
    GridFieldChoice,
    GridFieldDuration,
    GridFieldJSON,
    getCurrentDate,
)
from .utils import OperationPlanMixin

import logging

logger = logging.getLogger(__name__)


class OperationResourceList(GridReport):
    title = _("operation resources")
    basequeryset = OperationResource.objects.all()
    model = OperationResource
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-capacity/operation-resources.html"
    message_when_empty = Template(
        """
        <h3>Define operation resources</h3>
        <br>
        This table defines which resources are required to perfrom an operation.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/operationresource/add/" class="btn btn-primary">Create a single operation resource<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=8" class="btn btn-primary">Wizard to upload operation resources<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom operation attributes
            for f in getAttributeFields(
                Operation,
                related_name_prefix="operation",
                initially_hidden=True,
                editable=False,
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "operation.%s, " % f.name.split("__")[-1]
            # Adding custom resource attributes
            for f in getAttributeFields(
                Resource,
                related_name_prefix="resource",
                initially_hidden=True,
                editable=False,
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "resource.%s, " % f.name.split("__")[-1]

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/operationresource"',
            initially_hidden=True,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldHierarchicalText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
            model=Resource,
        ),
        GridFieldText(
            "skill",
            title=_("skill"),
            field_name="skill__name",
            formatter="detail",
            extra='"role":"input/skill"',
            initially_hidden=True,
        ),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldNumber(
            "quantity_fixed", title=_("quantity fixed"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText("name", title=_("name"), initially_hidden=True),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldText("setup", title=_("setup"), initially_hidden=True),
        GridFieldChoice(
            "search", title=_("search mode"), choices=searchmode, initially_hidden=True
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__name",
            title=format_lazy("{} - {}", _("operation"), _("item")),
            initially_hidden=True,
            editable=False,
            extra='"role":"input/item"',
            formatter="detail",
        ),
        GridFieldText(
            "operation__location__name",
            title=format_lazy("{} - {}", _("operation"), _("location")),
            initially_hidden=True,
            editable=False,
            extra='"role":"input/location"',
            formatter="detail",
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the resource
        GridFieldText(
            "resource__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("description")),
        ),
        GridFieldText(
            "resource__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("category")),
        ),
        GridFieldText(
            "resource__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("subcategory")),
        ),
        GridFieldText(
            "resource__type",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("type")),
        ),
        GridFieldNumber(
            "resource__maximum",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maximum")),
        ),
        GridFieldText(
            "resource__maximum_calendar",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maximum calendar")),
            field_name="resource__maximum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldCurrency(
            "resource__cost",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("cost")),
        ),
        GridFieldDuration(
            "resource__maxearly",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maxearly")),
        ),
        GridFieldText(
            "resource__setupmatrix",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("setupmatrix")),
            field_name="resource__setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldText(
            "resource__setup",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("setup")),
        ),
        GridFieldText(
            "resource__location",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("location")),
            field_name="resource__location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "resource__available",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("available")),
            field_name="resource__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "resource__owner__name",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("owner")),
            field_name="resource__owner__name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
    )


class OperationMaterialList(GridReport):
    title = _("operation materials")
    basequeryset = OperationMaterial.objects.all()
    model = OperationMaterial
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-bom/operation-materials.html"
    message_when_empty = Template(
        """
        <h3>Define operation materials</h3>
        <br>
        This table defines what item(s) an operation is consuming and producing.<br>
        Here you define the bill of material.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/operationmaterial/add/" class="btn btn-primary">Create a single operation material<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=3" class="btn btn-primary">Wizard to upload operation materials<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom operation attributes
            for f in getAttributeFields(
                Operation,
                related_name_prefix="operation",
                initially_hidden=True,
                editable=False,
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "operation.%s, " % f.name.split("__")[-1]
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True, editable=False
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "item.%s, " % f.name.split("__")[-1]

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/operationmaterial"',
            initially_hidden=True,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldHierarchicalText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
            model=Item,
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
            model=Location,
            initially_hidden=True,
        ),
        GridFieldChoice("type", title=_("type"), choices=OperationMaterial.types),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldNumber(
            "quantity_fixed", title=_("fixed quantity"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText("name", title=_("name"), initially_hidden=True),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldChoice(
            "search", title=_("search mode"), choices=searchmode, initially_hidden=True
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        GridFieldNumber(
            "transferbatch", title=_("transfer batch quantity"), initially_hidden=True
        ),
        GridFieldDuration("offset", title=_("offset"), initially_hidden=True),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__name",
            title=format_lazy("{} - {}", _("operation"), _("item")),
            initially_hidden=True,
            editable=False,
            extra='"role":"input/item"',
            formatter="detail",
        ),
        GridFieldText(
            "operation__location__name",
            title=format_lazy("{} - {}", _("operation"), _("location")),
            initially_hidden=True,
            editable=False,
            extra='"role":"input/location"',
            formatter="detail",
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
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
    )


class CalendarList(GridReport):
    title = _("calendars")
    basequeryset = Calendar.objects.all()
    model = Calendar
    frozenColumns = 1
    help_url = "model-reference/calendars.html"
    message_when_empty = Template(
        """
        <h3>Define calendars</h3>
        <br>
        A calendar represents a numeric value that is varying over time.<br><br>
        Different other models refer to calendars:<br>
        - A location refers to a calendar to define the working hours and holidays.<br>
        - A resource refers to a calendar to define the working hours and holidays.<br>
        - A supplier refers to a calendar to define the working hours and holidays.<br>
        - An operation refers to a calendar to define the working hours and holidays.<br>
        - A resource refers to a calendar to define the efficiency varying over time.<br>
        - A resource refers to a calendar to define the resource size varying over time.<br>
        - A buffer refers to a calendar to define the safety stock varying over time.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/calendar/add/" class="btn btn-primary">Create a single calendar<br>in a form</a>
        </div>
        <br>
        """
    )

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldNumber("defaultvalue", title=_("default value")),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class CalendarDetail(GridReport):
    model = CalendarBucket
    frozenColumns = 1
    hasTimeBuckets = True
    template = "input/calendardetail.html"
    help_url = "user-interface/plan-analysis/calendar-detail.html"
    title = _("calendar buckets")

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if not args:
            raise Exception("Expecting calendar argument")
        return CalendarBucket.objects.all().filter(calendar__name=args[0])

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if not args:
            raise Exception("Expecting calendar argument")
        request.session["lasttab"] = "plan"
        cal = Calendar.objects.all().using(request.database).get(name=args[0])
        events = cal.getEvents(request.report_startdate, request.report_enddate)
        minpriority = maxsize
        for b in cal.getBuckets():
            if b.priority < minpriority:
                minpriority = b.priority
        if minpriority == maxsize:
            minpriority = 0
        return {
            "active_tab": "plan",
            "title": force_str(Calendar._meta.verbose_name) + " " + args[0],
            "post_title": _("detail"),
            "model": CalendarBucket,
            "events": [
                (
                    x[0].strftime("%Y-%m-%d %H:%M:%S"),
                    x[1].strftime("%Y-%m-%d %H:%M:%S"),
                    x[2],
                    x[3],
                    x[4],
                    x[5],
                )
                for x in events
            ],
            "minpriority": minpriority - 1,
            "calendar": args[0],
        }

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            formatter="detail",
            extra='"role":"input/calendarbucket"',
            editable=False,
        ),
        GridFieldText(
            "calendar",
            title=_("calendar"),
            field_name="calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldDateTimeFull("startdate", title=_("start date")),
        GridFieldDateTimeFull("enddate", title=_("end date")),
        GridFieldNumber("value", title=_("value")),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldBool("monday", title=_("Monday")),
        GridFieldBool("tuesday", title=_("Tuesday")),
        GridFieldBool("wednesday", title=_("Wednesday")),
        GridFieldBool("thursday", title=_("Thursday")),
        GridFieldBool("friday", title=_("Friday")),
        GridFieldBool("saturday", title=_("Saturday")),
        GridFieldBool("sunday", title=_("Sunday")),
        GridFieldTime("starttime", title=_("start time")),
        GridFieldTime("endtime", title=_("end time")),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class CalendarBucketList(GridReport):
    title = _("calendar buckets")
    basequeryset = CalendarBucket.objects.all()
    model = CalendarBucket
    frozenColumns = 1
    help_url = "model-reference/calendar-buckets.html"
    message_when_empty = Template(
        """
        <h3>Define calendar buckets</h3>
        <br>
        A calendar represents a numeric value that is varying over time.<br><br>
        A calendar bucket represents a time period on a calendar during which a certain numeric value is effective.<br><br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/calendarbucket/add/" class="btn btn-primary">Create a single calendar bucket</a>
        </div>
        <br>
        """
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom calendar bucket attributes
            for f in getAttributeFields(CalendarBucket):
                reportclass.rows += (f,)
            # Adding custom calendar attributes
            for f in getAttributeFields(
                Calendar,
                related_name_prefix="calendar",
                editable=False,
                initially_hidden=True,
            ):
                reportclass.rows += (f,)

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            formatter="detail",
            extra='"role":"input/calendarbucket"',
            initially_hidden=True,
        ),
        GridFieldText(
            "calendar",
            title=_("calendar"),
            field_name="calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldDateTimeFull("startdate", title=_("start date")),
        GridFieldDateTimeFull("enddate", title=_("end date")),
        GridFieldNumber("value", title=_("value")),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldBool("monday", title=_("Monday")),
        GridFieldBool("tuesday", title=_("Tuesday")),
        GridFieldBool("wednesday", title=_("Wednesday")),
        GridFieldBool("thursday", title=_("Thursday")),
        GridFieldBool("friday", title=_("Friday")),
        GridFieldBool("saturday", title=_("Saturday")),
        GridFieldBool("sunday", title=_("Sunday")),
        GridFieldTime("starttime", title=_("start time")),
        GridFieldTime("endtime", title=_("end time")),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldText(
            "calendar__description",
            title=format_lazy("{} - {}", _("calendar"), _("description")),
            field_name="calendar__description",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "calendar__source",
            title=format_lazy("{} - {}", _("calendar"), _("source")),
            field_name="calendar__source",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "calendar__defaultvalue", title=_("default value"), initially_hidden=True
        ),
        GridFieldLastModified("lastmodified"),
    )


class OperationList(GridReport):
    title = _("operations")
    basequeryset = Operation.objects.all()
    model = Operation
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-bom/operations.html"
    message_when_empty = Template(
        """
        <h3>Define operations</h3>
        <br>
        An operation is a manufacturing operation consuming some items (a bill of material) to produce a
        new item. It also loads a number of resources during this process.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/operation/add/" class="btn btn-primary">Create a single operation<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=3" class="btn btn-primary">Wizard to upload operations<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom operation attributes
            for f in getAttributeFields(Operation):
                reportclass.rows += (f,)
                reportclass.attr_sql += "operation.%s, " % f.name.split("__")[-1]
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True, editable=False
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "item.%s, " % f.name.split("__")[-1]
            # Adding custom location attributes
            for f in getAttributeFields(
                Location,
                related_name_prefix="location",
                initially_hidden=True,
                editable=False,
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "location.%s, " % f.name.split("__")[-1]

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldChoice("type", title=_("type"), choices=Operation.types),
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
        GridFieldDuration("duration", title=_("duration")),
        GridFieldDuration("duration_per", title=_("duration per unit")),
        GridFieldDuration("fence", title=_("release fence"), initially_hidden=True),
        GridFieldDuration("posttime", title=_("post-op time"), initially_hidden=True),
        GridFieldNumber("sizeminimum", title=_("size minimum"), initially_hidden=True),
        GridFieldNumber(
            "sizemultiple", title=_("size multiple"), initially_hidden=True
        ),
        GridFieldNumber("sizemaximum", title=_("size maximum"), initially_hidden=True),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldChoice(
            "search", title=_("search mode"), choices=searchmode, initially_hidden=True
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
    )


class SubOperationList(GridReport):
    title = _("suboperations")
    basequeryset = SubOperation.objects.all()
    model = SubOperation
    frozenColumns = 1
    help_url = "model-reference/suboperations.html"
    message_when_empty = Template(
        """
        <h3>Define suboperations</h3>
        <br>
        This table is DEPRECATED.<br><br>
        Instead, use the field "owner" in the operation table to define steps in a routing operation.<br>
        <br>
        """
    )
    rows = (
        GridFieldInteger("id", title=_("identifier"), key=True, initially_hidden=True),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "suboperation",
            title=_("suboperation"),
            field_name="suboperation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Suboperation fields
        GridFieldText(
            "suboperation__description",
            title=format_lazy("{} - {}", _("suboperation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "suboperation__category",
            title=format_lazy("{} - {}", _("suboperation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "suboperation__subcategory",
            title=format_lazy("{} - {}", _("suboperation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "suboperation__type",
            title=format_lazy("{} - {}", _("suboperation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__duration",
            title=format_lazy("{} - {}", _("suboperation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__duration_per",
            title=format_lazy("{} - {}", _("suboperation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__fence",
            title=format_lazy("{} - {}", _("suboperation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__posttime",
            title=format_lazy("{} - {}", _("suboperation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "suboperation__sizeminimum",
            title=format_lazy("{} - {}", _("suboperation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "suboperation__sizemultiple",
            title=format_lazy("{} - {}", _("suboperation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "suboperation__sizemaximum",
            title=format_lazy("{} - {}", _("suboperation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "suboperation__priority",
            title=format_lazy("{} - {}", _("suboperation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "suboperation__effective_start",
            title=format_lazy("{} - {}", _("suboperation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "suboperation__effective_end",
            title=format_lazy("{} - {}", _("suboperation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "suboperation__cost",
            title=format_lazy("{} - {}", _("suboperation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "suboperation__search",
            title=format_lazy("{} - {}", _("suboperation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "suboperation__source",
            title=format_lazy("{} - {}", _("suboperation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "suboperation__lastmodified",
            title=format_lazy("{} - {}", _("suboperation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class OperationDependencyList(GridReport):
    title = _("operation dependencies")
    basequeryset = OperationDependency.objects.all()
    model = OperationDependency
    frozenColumns = 1
    help_url = "model-reference/operation-dependencies.html"
    message_when_empty = Template(
        """
        <h3>Define operation dependencies</h3>
        <br>
        This table defines relations between operations.<br>
        Use this table for:<br>
        <br>
        <br>1.<br>
        Define which <b>steps in a routing operation can be executed in parallel</b>.<br>
        You use the dependencies to define which operation(s) is a prerequisite for another.<br>
        <br>
        <br>2.<br>
        Define relations between <b>different steps in a project-oriented business</b>.<br>
        In most manufacturing oriented business, a bill-of-material is used to define
        different levels in the product structure.<br>
        In a project-oriented business you can directly link subprojects without
        defining intermediate items.<br>
        <br>
        <br>
        """
    )
    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/operationdependency"',
            initially_hidden=True,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "blockedby",
            title=_("blocked by operation"),
            field_name="blockedby__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldDuration(
            "safety_leadtime", title=_("soft safety lead time"), initially_hidden=True
        ),
        GridFieldDuration(
            "hard_safety_leadtime",
            title=_("hard safety lead time"),
            initially_hidden=True,
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # blockedby fields
        GridFieldText(
            "blockedby__description",
            title=format_lazy("{} - {}", _("blocked by"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "blockedby__category",
            title=format_lazy("{} - {}", _("blocked by"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "blockedby__subcategory",
            title=format_lazy("{} - {}", _("blocked by"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "blockedby__type",
            title=format_lazy("{} - {}", _("blocked by"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "blockedby__duration",
            title=format_lazy("{} - {}", _("blocked by"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "blockedby__duration_per",
            title=format_lazy("{} - {}", _("blocked by"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "blockedby__fence",
            title=format_lazy("{} - {}", _("blocked by"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "blockedby__posttime",
            title=format_lazy("{} - {}", _("blocked by"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "blockedby__sizeminimum",
            title=format_lazy("{} - {}", _("blocked by"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "blockedby__sizemultiple",
            title=format_lazy("{} - {}", _("blocked by"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "blockedby__sizemaximum",
            title=format_lazy("{} - {}", _("blocked by"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "blockedby__priority",
            title=format_lazy("{} - {}", _("blocked by"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "blockedby__effective_start",
            title=format_lazy("{} - {}", _("blocked by"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "blockedby__effective_end",
            title=format_lazy("{} - {}", _("blocked by"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "blockedby__cost",
            title=format_lazy("{} - {}", _("blocked by"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "blockedby__search",
            title=format_lazy("{} - {}", _("blocked by"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "blockedby__source",
            title=format_lazy("{} - {}", _("blocked by"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "blockedby__lastmodified",
            title=format_lazy("{} - {}", _("blocked by"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class ManufacturingOrderList(OperationPlanMixin):
    template = "input/operationplanreport.html"
    title = _("manufacturing orders")
    default_sort = (1, "desc")
    model = ManufacturingOrder
    frozenColumns = 1
    multiselect = True
    editable = True
    height = 250
    help_url = "modeling-wizard/manufacturing-bom/manufacturing-orders.html"
    message_when_empty = Template(
        """
        <h3>Define manufacturing orders</h3>
        <br>
        This table contains the "confirmed" manufacturing orders.<br><br>
        When generating a plan frepple will add new "proposed" manufacturing orders to this table.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/manufacturingorder/add/" onclick="window.location = $(event.target).attr('href'); event.preventDefault();" class="btn btn-primary">Create a single manufacturing order<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=7" onclick="window.location = $(event.target).attr('href'); event.preventDefault();" class="btn btn-primary">Wizard to upload manufacturing orders<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )
    calendarmode = "duration"

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        groupingcfg = OrderedDict()
        groupingcfg["operation__location__name"] = force_str(_("location"))
        groupingcfg["operation__category"] = force_str(
            format_lazy("{} - {}", _("operation"), _("category"))
        )
        groupingcfg["operation__subcategory"] = force_str(
            format_lazy("{} - {}", _("operation"), _("subcategory"))
        )
        groupingcfg["item__category"] = force_str(
            format_lazy("{} - {}", _("item"), _("category"))
        )
        groupingcfg["item__subcategory"] = force_str(
            format_lazy("{} - {}", _("item"), _("subcategory"))
        )
        ctx = super().extra_context(request, *args, **kwargs)
        ctx["noautofilter"] = "noautofilter" in request.GET
        if args and args[0]:
            request.session["lasttab"] = "plandetail"
            paths = request.path.split("/")
            path = paths[4]
            if path == "location" or request.path.startswith("/detail/input/location/"):
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Location,
                        "title": force_str(Location._meta.verbose_name) + " " + args[0],
                        "post_title": _("manufacturing orders"),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "operation" or request.path.startswith(
                "/detail/input/operation/"
            ):
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Operation,
                        "title": force_str(Operation._meta.verbose_name)
                        + " "
                        + args[0],
                        "post_title": _("manufacturing orders"),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": _("manufacturing orders"),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "operationplanmaterial":
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": force_str(
                            _("work in progress in %(loc)s at %(date)s")
                            % {"loc": args[1], "date": args[2]}
                        ),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "produced":
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": force_str(
                            _("produced in %(loc)s between %(date1)s and %(date2)s")
                            % {"loc": args[1], "date1": args[2], "date2": args[3]}
                        ),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "consumed":
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": force_str(
                            _("consumed in %(loc)s between %(date1)s and %(date2)s")
                            % {"loc": args[1], "date1": args[2], "date2": args[3]}
                        ),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            else:
                ctx.update(
                    {
                        "default_operationplan_type": "MO",
                        "groupBy": "status",
                        "active_tab": "edit",
                        "model": Item,
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
        elif "parentreference" in request.GET:
            ctx.update(
                {
                    "default_operationplan_type": "MO",
                    "groupBy": "status",
                    "active_tab": "plandetail",
                    "title": force_str(ManufacturingOrder._meta.verbose_name)
                    + " "
                    + request.GET["parentreference"],
                    "groupingcfg": groupingcfg,
                    "currentdate": getCurrentDate(
                        database=request.database, lastplan=True
                    ),
                }
            )
        else:
            ctx.update(
                {
                    "default_operationplan_type": "MO",
                    "groupBy": "status",
                    "active_tab": "plandetail",
                    "groupingcfg": groupingcfg,
                    "currentdate": getCurrentDate(
                        database=request.database, lastplan=True
                    ),
                }
            )
        return ctx

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = ManufacturingOrder.objects.all()
        if "calendarstart" in request.GET:
            q = q.filter(
                Q(enddate__gte=request.GET["calendarstart"])
                | (
                    Q(enddate__isnull=True)
                    & Q(startdate__gte=request.GET["calendarstart"])
                )
            )
        if "calendarend" in request.GET:
            q = q.filter(
                Q(startdate__lte=request.GET["calendarend"])
                | (
                    Q(startdate__isnull=True)
                    & Q(enddate__lte=request.GET["calendarend"])
                )
            )

        if args and args[0]:
            path = request.path.split("/")[4]
            if path == "location" or request.path.startswith("/detail/input/location/"):
                q = q.filter(location=args[0])
            elif path == "operation" or request.path.startswith(
                "/detail/input/operation/"
            ):
                q = q.filter(operation=args[0])
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s
                          and operationplanmaterial.quantity > 0
                        where operationplan.type = 'MO'
                        """,
                        (args[0],),
                    )
                )
            elif path == "operationplanmaterial":
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
                          and operationplan.startdate < %s and operationplan.enddate >= %s
                        where operationplan.type = 'MO'
                        """,
                        (args[0], args[1], args[2], args[2]),
                    )
                )
            elif path == "produced":
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
                          and operationplanmaterial.flowdate >= %s and operationplanmaterial.flowdate < %s
                          and operationplanmaterial.quantity > 0
                        where operationplan.type = 'MO'
                        """,
                        (args[0], args[1], args[2], args[3]),
                    )
                )
            elif path == "consumed":
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
                          and operationplanmaterial.flowdate >= %s and operationplanmaterial.flowdate < %s
                          and operationplanmaterial.quantity < 0
                        where operationplan.type = 'MO'
                        """,
                        (args[0], args[1], args[2], args[3]),
                    )
                )

        q = reportclass.operationplanExtraBasequery(q, request)

        if request.prefs and "noautofilter" not in request.GET:
            if not request.prefs.get("showTop", True):
                q = q.exclude(owner__isnull=True)
            if not request.prefs.get("showChildren", True):
                q = q.exclude(owner__isnull=False)

        return q.annotate(
            material=RawSQL(
                "(select json_agg(json_build_array(item_id, quantity, operationplan_id)) from (select operationplanmaterial.item_id, round(operationplanmaterial.quantity,2) quantity, operationplanmaterial.operationplan_id from operationplanmaterial inner join operationplan opplan2 on opplan2.reference = operationplanmaterial.operationplan_id where operationplan.reference = opplan2.reference or operationplan.reference = opplan2.owner_id order by quantity limit 10) mat)",
                [],
            ),
            resource=RawSQL(
                "(select json_agg(json_build_array(resource_id, quantity, operationplan_id)) from (select operationplanresource.resource_id, round(operationplanresource.quantity,2) quantity, operationplanresource.operationplan_id from operationplanresource inner join operationplan opplan2 on opplan2.reference = operationplanresource.operationplan_id where operationplan.reference = opplan2.reference or operationplan.reference = opplan2.owner_id order by quantity desc limit 10) res)",
                [],
            ),
            setup=RawSQL(
                "(select json_agg(json_build_array(resource_id, setup)) from (select resource_id, setup from operationplanresource where setup is not null and operationplan.reference = operationplanresource.operationplan_id order by resource_id limit 10) res)",
                [],
            ),
            setup_duration=Cast(
                RawSQL(
                    "(operationplan.plan->>'setup')::numeric * '1 second'::interval", []
                ),
                DurationField(),
            ),
            setup_end=Cast(
                RawSQL("(operationplan.plan->>'setupend')", []), DateTimeField()
            ),
            setup_override=Cast(
                RawSQL(
                    "(operationplan.plan->>'setupoverride')::numeric * '1 second'::interval",
                    [],
                ),
                DurationField(),
            ),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
            opplan_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate)", []
            ),
            opplan_net_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate - coalesce((operationplan.plan->>'unavailable')::int * interval '1 second', interval '0 second'))",
                [],
            ),
            inventory_item=RawSQL("operationplan.plan->'item'", []),
            inventory_location=RawSQL("operationplan.plan->'location'", []),
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
            total_cost=Cast(
                F("operation__cost") * F("quantity"), output_field=FloatField()
            ),
            total_volume=Cast(
                F("item__volume") * F("quantity"), output_field=FloatField()
            ),
            total_weight=Cast(
                F("item__weight") * F("quantity"), output_field=FloatField()
            ),
        )

    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
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
            "item__name",
            title=_("item"),
            formatter="detail",
            extra='"role":"input/item"',
            editable=False,
            model=Item,
        ),
        GridFieldHierarchicalText(
            "operation__location__name",
            title=_("location"),
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
            model=Location,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldDateTime(
            "startdate",
            title=_("start date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"%s", "defaultValue":""}, "summaryType":"min"'
            % settings.DATETIME_FORMAT,
        ),
        GridFieldDateTime(
            "enddate",
            title=_("end date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"%s", "defaultValue":""}, "summaryType":"max"'
            % settings.DATETIME_FORMAT,
        ),
        GridFieldDuration(
            "opplan_duration",
            title=_("duration"),
            formatter="duration",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "opplan_net_duration",
            title=_("net duration"),
            formatter="duration",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "quantity_completed",
            title=_("completed quantity"),
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText("remark", title=_("remark"), editable="true"),
        GridFieldCurrency(
            "total_cost",
            title=_("total cost"),
            editable=False,
            search=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "total_volume",
            title=_("total volume"),
            editable=False,
            search=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "total_weight",
            title=_("total weight"),
            editable=False,
            search=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=OperationPlan.orderstatus,
            editable=not settings.ERP_CONNECTOR,
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
        GridFieldText(
            "demand",
            title=_("demand"),
            field_name="demand__name",
            formatter="detail",
            initially_hidden=True,
            extra='"role":"input/demand"',
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
        GridFieldJSON(
            "material",
            title=_("materials"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
        GridFieldJSON(
            "resource",
            title=_("resources"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "setup",
            title=_("setups"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__owner",
            title=format_lazy("{} - {}", _("operation"), _("owner")),
            field_name="operation__owner__name",
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "setup_duration",
            title=_("setup duration"),
            initially_hidden=True,
            search=False,
            editable=False,
        ),
        GridFieldDateTime(
            "setup_end",
            title=_("setup end date"),
            initially_hidden=True,
            search=True,
            editable=False,
        ),
        GridFieldDuration(
            "setup_override",
            title=_("setup duration override"),
            initially_hidden=True,
            search=True,
            editable=False,
        ),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=True,
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
            field_name="operation__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="operation__location__owner__name",
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
            "end_items",
            title=_("end items"),
            editable=False,
            search=True,
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
                "label": format_lazy(_("export to {erp}"), erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'MO')",
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
            for f in getAttributeFields(ManufacturingOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Operation, related_name_prefix="operation"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="location"):
                f.editable = False
                reportclass.rows += (f,)


class WorkOrderList(OperationPlanMixin):
    template = "input/operationplanreport.html"
    title = _("work orders")
    default_sort = (1, "desc")
    model = WorkOrder
    frozenColumns = 1
    multiselect = True
    editable = True
    height = 250
    help_url = "modeling-wizard/manufacturing-bom/work-orders.html"
    message_when_empty = Template(
        """
        <h3>Define work orders</h3>
        <br>
        This table contains the "confirmed" work orders.<br><br>
        When generating a plan frepple will add new "proposed" work orders to this table.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/workorder/add/" onclick="window.location = $(event.target).attr('href'); event.preventDefault();" class="btn btn-primary">Create a single manufacturing order<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=7" onclick="window.location = $(event.target).attr('href'); event.preventDefault();" class="btn btn-primary">Wizard to upload manufacturing orders<br>from a spreadsheet</a>
        </div>
        <br>
        """
    )
    calendarmode = "duration"

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        groupingcfg = OrderedDict()
        groupingcfg["operation__location__name"] = force_str(_("location"))
        groupingcfg["operation__category"] = force_str(
            format_lazy("{} - {}", _("operation"), _("category"))
        )
        groupingcfg["operation__subcategory"] = force_str(
            format_lazy("{} - {}", _("operation"), _("subcategory"))
        )
        groupingcfg["item__category"] = force_str(
            format_lazy("{} - {}", _("item"), _("category"))
        )
        groupingcfg["item__subcategory"] = force_str(
            format_lazy("{} - {}", _("item"), _("subcategory"))
        )
        ctx = super().extra_context(request, *args, **kwargs)
        ctx["noautofilter"] = "noautofilter" in request.GET
        if args and args[0]:
            request.session["lasttab"] = "plandetail"
            paths = request.path.split("/")
            path = paths[4]
            if path == "location" or request.path.startswith("/detail/input/location/"):
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Location,
                        "title": force_str(Location._meta.verbose_name) + " " + args[0],
                        "post_title": _("work orders"),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "operation" or request.path.startswith(
                "/detail/input/operation/"
            ):
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Operation,
                        "title": force_str(Operation._meta.verbose_name)
                        + " "
                        + args[0],
                        "post_title": _("work orders"),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": _("work orders"),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "operationplanmaterial":
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": force_str(
                            _("work in progress in %(loc)s at %(date)s")
                            % {"loc": args[1], "date": args[2]}
                        ),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "produced":
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": force_str(
                            _("produced in %(loc)s between %(date1)s and %(date2)s")
                            % {"loc": args[1], "date1": args[2], "date2": args[3]}
                        ),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            elif path == "consumed":
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "plandetail",
                        "model": Item,
                        "title": force_str(Item._meta.verbose_name) + " " + args[0],
                        "post_title": force_str(
                            _("consumed in %(loc)s between %(date1)s and %(date2)s")
                            % {"loc": args[1], "date1": args[2], "date2": args[3]}
                        ),
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
            else:
                ctx.update(
                    {
                        "default_operationplan_type": "WO",
                        "groupBy": "status",
                        "active_tab": "edit",
                        "model": Item,
                        "groupingcfg": groupingcfg,
                        "currentdate": getCurrentDate(
                            database=request.database, lastplan=True
                        ),
                    }
                )
        elif "parentreference" in request.GET:
            ctx.update(
                {
                    "default_operationplan_type": "WO",
                    "groupBy": "status",
                    "active_tab": "plandetail",
                    "title": force_str(WorkOrder._meta.verbose_name)
                    + " "
                    + request.GET["parentreference"],
                    "groupingcfg": groupingcfg,
                    "currentdate": getCurrentDate(
                        database=request.database, lastplan=True
                    ),
                }
            )
        else:
            ctx.update(
                {
                    "default_operationplan_type": "WO",
                    "groupBy": "status",
                    "active_tab": "plandetail",
                    "groupingcfg": groupingcfg,
                    "currentdate": getCurrentDate(
                        database=request.database, lastplan=True
                    ),
                }
            )
        return ctx

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = WorkOrder.objects.all()
        if "calendarstart" in request.GET:
            q = q.filter(
                Q(enddate__gte=request.GET["calendarstart"])
                | (
                    Q(enddate__isnull=True)
                    & Q(startdate__gte=request.GET["calendarstart"])
                )
            )
        if "calendarend" in request.GET:
            q = q.filter(
                Q(startdate__lte=request.GET["calendarend"])
                | (
                    Q(startdate__isnull=True)
                    & Q(enddate__lte=request.GET["calendarend"])
                )
            )

        if args and args[0]:
            path = request.path.split("/")[4]
            if path == "location" or request.path.startswith("/detail/input/location/"):
                q = q.filter(location=args[0])
            elif path == "operation" or request.path.startswith(
                "/detail/input/operation/"
            ):
                q = q.filter(operation=args[0])
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s
                          and operationplanmaterial.quantity > 0
                        where operationplan.type = 'WO'
                        """,
                        (args[0],),
                    )
                )
            elif path == "operationplanmaterial":
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
                          and operationplan.startdate < %s and operationplan.enddate >= %s
                        where operationplan.type = 'WO'
                        """,
                        (args[0], args[1], args[2], args[2]),
                    )
                )
            elif path == "produced":
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
                          and operationplanmaterial.flowdate >= %s and operationplanmaterial.flowdate < %s
                          and operationplanmaterial.quantity > 0
                        where operationplan.type = 'WO'
                        """,
                        (args[0], args[1], args[2], args[3]),
                    )
                )
            elif path == "consumed":
                q = q.filter(
                    reference__in=RawSQL(
                        """
                        select operationplan_id
                        from operationplan
                        inner join operationplanmaterial
                          on operationplanmaterial.operationplan_id = operationplan.reference
                          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
                          and operationplanmaterial.flowdate >= %s and operationplanmaterial.flowdate < %s
                          and operationplanmaterial.quantity < 0
                        where operationplan.type = 'WO'
                        """,
                        (args[0], args[1], args[2], args[3]),
                    )
                )

        q = reportclass.operationplanExtraBasequery(q, request)

        return q.annotate(
            material=RawSQL(
                "(select json_agg(json_build_array(item_id, quantity, operationplan_id)) from (select operationplanmaterial.item_id, round(operationplanmaterial.quantity,2) quantity, operationplanmaterial.operationplan_id from operationplanmaterial inner join operationplan opplan2 on opplan2.reference = operationplanmaterial.operationplan_id where operationplan.reference = opplan2.reference or operationplan.reference = opplan2.owner_id order by quantity limit 10) mat)",
                [],
            ),
            resource=RawSQL(
                "(select json_agg(json_build_array(resource_id, quantity, operationplan_id)) from (select operationplanresource.resource_id, round(operationplanresource.quantity,2) quantity, operationplanresource.operationplan_id from operationplanresource inner join operationplan opplan2 on opplan2.reference = operationplanresource.operationplan_id where operationplan.reference = opplan2.reference or operationplan.reference = opplan2.owner_id order by quantity desc limit 10) res)",
                [],
            ),
            setup=RawSQL(
                "(select json_agg(json_build_array(resource_id, setup)) from (select resource_id, setup from operationplanresource where setup is not null and operationplan.reference = operationplanresource.operationplan_id order by resource_id limit 10) res)",
                [],
            ),
            setup_duration=Cast(
                RawSQL(
                    "(operationplan.plan->>'setup')::numeric * '1 second'::interval", []
                ),
                DurationField(),
            ),
            setup_end=Cast(
                RawSQL("(operationplan.plan->>'setupend')", []), DateTimeField()
            ),
            setup_override=Cast(
                RawSQL(
                    "(operationplan.plan->>'setupoverride')::numeric * '1 second'::interval",
                    [],
                ),
                DurationField(),
            ),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
            opplan_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate)", []
            ),
            opplan_net_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate - coalesce((operationplan.plan->>'unavailable')::int * interval '1 second', interval '0 second'))",
                [],
            ),
            inventory_item=RawSQL("operationplan.plan->'item'", []),
            inventory_location=RawSQL("operationplan.plan->'location'", []),
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
            total_cost=Cast(
                F("operation__cost") * F("quantity"), output_field=FloatField()
            ),
            total_volume=Cast(
                F("item__volume") * F("quantity"), output_field=FloatField()
            ),
            total_weight=Cast(
                F("item__weight") * F("quantity"), output_field=FloatField()
            ),
        )

    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra="role:'input/workorder'",
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__reference",
            formatter="detail",
            extra="role:'input/manufacturingorder'",
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
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
            "item__name",
            title=_("item"),
            formatter="detail",
            extra='"role":"input/item"',
            editable=False,
            model=Item,
        ),
        GridFieldHierarchicalText(
            "operation__location__name",
            title=_("location"),
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
            model=Location,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldDateTime(
            "startdate",
            title=_("start date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"%s", "defaultValue":""}, "summaryType":"min"'
            % settings.DATETIME_FORMAT,
        ),
        GridFieldDateTime(
            "enddate",
            title=_("end date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"%s", "defaultValue":""}, "summaryType":"max"'
            % settings.DATETIME_FORMAT,
        ),
        GridFieldDuration(
            "opplan_duration",
            title=_("duration"),
            formatter="duration",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "opplan_net_duration",
            title=_("net duration"),
            formatter="duration",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "quantity_completed",
            title=_("completed quantity"),
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText("remark", title=_("remark"), editable="true"),
        GridFieldCurrency(
            "total_cost",
            title=_("total cost"),
            editable=False,
            search=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "total_volume",
            title=_("total volume"),
            editable=False,
            search=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "total_weight",
            title=_("total weight"),
            editable=False,
            search=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=OperationPlan.orderstatus,
            editable=not settings.ERP_CONNECTOR,
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
        GridFieldText(
            "demand",
            title=_("demand"),
            field_name="demand__name",
            formatter="detail",
            initially_hidden=True,
            extra='"role":"input/demand"',
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
        GridFieldJSON(
            "material",
            title=_("materials"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
        GridFieldJSON(
            "resource",
            title=_("resources"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "setup",
            title=_("setups"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__owner",
            title=format_lazy("{} - {}", _("operation"), _("owner")),
            field_name="operation__owner__name",
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "setup_duration",
            title=_("setup duration"),
            initially_hidden=True,
            search=False,
            editable=False,
        ),
        GridFieldDateTime(
            "setup_end",
            title=_("setup end date"),
            initially_hidden=True,
            search=True,
            editable=False,
        ),
        GridFieldDuration(
            "setup_override",
            title=_("setup duration override"),
            initially_hidden=True,
            search=True,
            editable=False,
        ),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=True,
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
            field_name="operation__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="operation__location__owner__name",
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
            "end_items",
            title=_("end items"),
            editable=False,
            search=True,
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
                "label": format_lazy(_("export to {erp}"), erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'MO')",
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
            for f in getAttributeFields(ManufacturingOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Operation, related_name_prefix="operation"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="location"):
                f.editable = False
                reportclass.rows += (f,)
