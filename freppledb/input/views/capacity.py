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
from datetime import datetime

from django.conf import settings
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.template import Template
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.utils.text import format_lazy

from freppledb.boot import getAttributeFields
from freppledb.common.models import Parameter
from freppledb.input.models import (
    Item,
    Resource,
    Operation,
    Location,
    SetupMatrix,
    SetupRule,
    Skill,
    ResourceSkill,
    OperationPlan,
    OperationPlanResource,
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
    getCurrentDate,
    GridFieldJSON,
)
from freppledb.output.models import ResourceSummary
from .utils import OperationPlanMixin

import logging

logger = logging.getLogger(__name__)


class SetupMatrixList(GridReport):
    title = _("setup matrices")
    basequeryset = SetupMatrix.objects.all()
    model = SetupMatrix
    frozenColumns = 1
    help_url = "model-reference/setup-matrices.html"
    message_when_empty = Template(
        """
        <h3>Define setup matrices</h3>
        <br>
        A setup matrix defines the time and cost of setup conversions on a resource.<br><br>
        A setup matrix contains a list of rules that define the changeover cost and duration.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/setupmatrix/add/" class="btn btn-primary">Add a setup matrix</a>
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
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class SetupRuleList(GridReport):
    title = _("setup rules")
    basequeryset = SetupRule.objects.all()
    model = SetupRule
    frozenColumns = 1
    help_url = "model-reference/setup-matrices.html"
    message_when_empty = Template(
        """
        <h3>Define setup matrix rules</h3>
        <br>
        A setup matrix rule defines the changeover cost and duration.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/setuprule/add/" class="btn btn-primary">Add a setup matrix rule</a>
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
            extra='"role":"input/setuprule"',
            initially_hidden=True,
        ),
        GridFieldText(
            "setupmatrix",
            title=_("setup matrix"),
            field_name="setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldText("fromsetup", title=_("from setup")),
        GridFieldText("tosetup", title=_("to setup")),
        GridFieldDuration("duration", title=_("duration")),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
        GridFieldLastModified("lastmodified"),
    )


class ResourceList(GridReport):
    title = _("resources")
    basequeryset = Resource.objects.all()
    model = Resource
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-capacity/resources.html"
    message_when_empty = Template(
        """
        <h3>Define resources</h3>
        <br>
        Resources represent capacity.<br>
        They represent a machine, a group of machines, an operator, a group
        of operators, or some logical capacity constraint.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/resource/add/" class="btn btn-primary">Create a single resource<br>in a form</a>
        <a href="{{request.prefix}}/wizard/load/production/?currentstep=8" class="btn btn-primary">Wizard to upload resources<br>from a spreadsheet</a>
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
            extra='"role":"input/resource"',
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
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
        GridFieldChoice("type", title=_("type"), choices=Resource.types),
        GridFieldBool("constrained", title=_("constrained")),
        GridFieldNumber("maximum", title=_("maximum")),
        GridFieldText(
            "maximum_calendar",
            title=_("maximum calendar"),
            field_name="maximum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldDuration("maxearly", title=_("maxearly"), initially_hidden=True),
        GridFieldText(
            "setupmatrix",
            title=_("setup matrix"),
            field_name="setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
            initially_hidden=True,
        ),
        GridFieldText("setup", title=_("setup"), initially_hidden=True),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        # Translator: xgettext:no-python-format
        GridFieldNumber("efficiency", title=_("efficiency %"), formatter="percentage"),
        GridFieldText(
            "efficiency_calendar",
            # Translator: xgettext:no-python-format
            title=_("efficiency % calendar"),
            initially_hidden=True,
            field_name="efficiency_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldLastModified("lastmodified"),
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


class SkillList(GridReport):
    title = _("skills")
    basequeryset = Skill.objects.all()
    model = Skill
    frozenColumns = 1
    help_url = "model-reference/skills.html"
    message_when_empty = Template(
        """
        <h3>Define skills</h3>
        <br>
        A skill defines a certain property that can be assigned to resources.<br><br>
        The operation-skill table associates a resource with all its skills. A resource can have any number of skills.<br><br>
        The operation-resource table defines the resources and skill required to perform the operation.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/skill/add/" class="btn btn-primary">Create a skill</a>
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
            extra='"role":"input/skill"',
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class ResourceSkillList(GridReport):
    title = _("resource skills")
    basequeryset = ResourceSkill.objects.all()
    model = ResourceSkill
    frozenColumns = 1
    help_url = "model-reference/resource-skills.html"
    message_when_empty = Template(
        """
        <h3>Define resource skills</h3>
        <br>
        The table defines all skills a resource has.<br>
        <br><br>
        <div role="group" class="btn-group.btn-group-justified">
        <a href="{{request.prefix}}/data/input/resourceskill/add/" class="btn btn-primary">Create a resource skill</a>
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
            extra='"role":"input/resourceskill"',
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
        ),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
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
            "resource__owner",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("owner")),
            field_name="resource__owner__name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom resource attributes
            for f in getAttributeFields(
                Resource,
                related_name_prefix="resource",
                initially_hidden=True,
                editable=False,
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "resource.%s, " % f.name.split("__")[-1]


class ResourceDetail(OperationPlanMixin):
    template = "input/operationplanreport.html"
    title = _("resource detail")
    model = OperationPlanResource
    permissions = (("view_resource_report", "Can view resource report"),)
    frozenColumns = 3
    editable = True
    multiselect = True
    height = 250
    help_url = "user-interface/plan-analysis/resource-detail-report.html"
    message_when_empty = Template(
        """
        <h3>Resource detail</h3>
        <br>
        This table has a list of all manufacturing orders assigned to a certain certain resource.<br><br>
        The planning algorithm will populate this table, and as a user you normally don't need to create records in this table.<br>
        <br>
        """
    )

    @classmethod
    def _generate_gantt_data(cls, request, *args, **kwargs):
        # Preparation of the correct filter for a column is currently done on the client side.
        # The kanban query also doesn't know about pages.
        request.GET = request.GET.copy()
        request.GET["page"] = None
        request.limit = request.pagesize
        return cls._generate_json_data(request, *args, **kwargs)

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            try:
                res = Resource.objects.using(request.database).get(name__exact=args[0])
                if not res.lft or not res.rght:
                    Resource.rebuildHierarchy(database=request.database)
                    res = Resource.objects.using(request.database).get(
                        name__exact=args[0]
                    )
                base = OperationPlanResource.objects.filter(
                    resource__lft__gte=res.lft, resource__rght__lte=res.rght
                )
            except OperationPlanResource.DoesNotExist:
                base = OperationPlanResource.objects.filter(resource__exact=args[0])
        else:
            base = OperationPlanResource.objects
        base = reportclass.operationplanExtraBasequery(base, request)
        if "calendarstart" in request.GET:
            base = base.filter(
                Q(operationplan__enddate__gte=request.GET["calendarstart"])
                | (
                    Q(operationplan__enddate__isnull=True)
                    & Q(operationplan__startdate__gte=request.GET["calendarstart"])
                )
            )
        if "calendarend" in request.GET:
            base = base.filter(
                Q(operationplan__startdate__lte=request.GET["calendarend"])
                | (
                    Q(operationplan__startdate__isnull=True)
                    & Q(operationplan__enddate__lte=request.GET["calendarend"])
                )
            )

        return base.select_related().annotate(
            opplan_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate)", []
            ),
            opplan_net_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate - coalesce((operationplan.plan->>'unavailable')::int * interval '1 second', interval '0 second'))",
                [],
            ),
            setup_end=RawSQL("(operationplan.plan->>'setupend')", []),
            setup_duration=RawSQL("(operationplan.plan->>'setup')", []),
            setup_override=RawSQL("(operationplan.plan->>'setupoverride')", []),
            resources=RawSQL(
                "(select json_agg(json_build_array(resource_id, quantity)) from (select resource_id, round(quantity,2) quantity from operationplanresource opplanres2 where operationplan.reference = opplanres2.operationplan_id  order by quantity desc limit 10) res)",
                [],
            ),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
        )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            # Adding custom operation attributes
            for f in getAttributeFields(
                Operation,
                related_name_prefix="operationplan__operation",
                editable=False,
            ):
                f.editable = False
                reportclass.rows += (f,)
            # Adding custom resource attributes
            for f in getAttributeFields(
                Resource, related_name_prefix="resource", editable=False
            ):
                f.editable = False
                reportclass.rows += (f,)
            # Adding custom item attributes
            for f in getAttributeFields(
                Item,
                related_name_prefix="operationplan__item",
                editable=False,
            ):
                f.editable = False
                reportclass.rows += (f,)
            # Adding custom operationplan attributes
            for f in getAttributeFields(
                OperationPlan,
                related_name_prefix="operationplan",
                initially_hidden=True,
                editable=False,
            ):
                f.editable = False
                reportclass.rows += (f,)

        # special case for bucketized resources, we need to scan for
        # records in the complete time bucket where the filters fall in

        try:
            if "/operationplanresource/resource/" in request.path:
                resource = request.path.strip("/").split("/")[-1]
                res = Resource.objects.using(request.database).get(name__exact=resource)
                dateformat = (
                    settings.DATETIME_INPUT_FORMATS
                    if settings.DATE_STYLE_WITH_HOURS
                    else settings.DATE_INPUT_FORMATS
                )[0]
                if "buckets" in res.type.lower() and res.lft == res.rght - 1:
                    if "operationplan__startdate__gte" in request.GET:
                        startdate_filter = request.GET["operationplan__startdate__gte"]
                        startdate = datetime.strptime(
                            startdate_filter,
                            dateformat,
                        )
                        r = (
                            ResourceSummary.objects.using(request.database)
                            .filter(resource=res.name)
                            .filter(startdate__lte=startdate)
                            .order_by("-startdate")
                            .values("startdate")[:1]
                        )
                        bucketstart = (
                            r[0]["startdate"] if len(r) == 1 else datetime(2000, 1, 1)
                        ).strftime(dateformat)
                        request.GET._mutable = True  # to make it editable
                        request.GET["operationplan__startdate__gte"] = bucketstart
                        request.GET._mutable = False

                    if "operationplan__startdate__lt" in request.GET:
                        startdate_filter = request.GET["operationplan__startdate__lt"]
                        startdate = datetime.strptime(
                            startdate_filter,
                            dateformat,
                        )
                        r = (
                            ResourceSummary.objects.using(request.database)
                            .filter(resource=res.name)
                            .filter(startdate__gte=startdate)
                            .order_by("startdate")
                            .values("startdate")[:1]
                        )
                        bucketend = (
                            r[0]["startdate"] if len(r) == 1 else datetime(2030, 12, 31)
                        ).strftime(dateformat)
                        request.GET._mutable = True  # to make it editable
                        request.GET["operationplan__startdate__lt"] = bucketend
                        request.GET._mutable = False
        except Exception:
            # silently fail
            pass

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        groupingcfg = OrderedDict()
        groupingcfg["resource"] = force_str(_("resource"))
        groupingcfg["operationplan__location"] = force_str(_("location"))
        groupingcfg["operationplan__operation__category"] = force_str(
            format_lazy("{} - {}", _("operation"), _("category"))
        )
        groupingcfg["operationplan__operation__subcategory"] = force_str(
            format_lazy("{} - {}", _("operation"), _("subcategory"))
        )
        groupingcfg["resource__category"] = force_str(
            format_lazy("{} - {}", _("resource"), _("category"))
        )
        groupingcfg["resource__subcategory"] = force_str(
            format_lazy("{} - {}", _("resource"), _("subcategory"))
        )
        individualPoolResources = (
            Parameter.getValue(
                "plan.individualPoolResources", request.database, "false"
            ).lower()
            == "true"
        )
        ctx = super().extra_context(request, *args, **kwargs)
        if args and args[0]:
            request.session["lasttab"] = "plandetail"
            ctx.update(
                {
                    "default_operationplan_type": "MO",
                    "groupBy": "operationplan__status",
                    "active_tab": "plandetail",
                    "model": Resource,
                    "title": force_str(Resource._meta.verbose_name) + " " + args[0],
                    "post_title": _("plan detail"),
                    "groupingcfg": groupingcfg,
                    "currentdate": getCurrentDate(
                        database=request.database, lastplan=True
                    ),
                    "individualPoolResources": individualPoolResources,
                    "showGantt": True,
                }
            )
        else:
            ctx.update(
                {
                    "default_operationplan_type": "MO",
                    "groupBy": "operationplan__status",
                    "active_tab": "plandetail",
                    "model": OperationPlanResource,
                    "groupingcfg": groupingcfg,
                    "currentdate": getCurrentDate(
                        database=request.database, lastplan=True
                    ),
                    "individualPoolResources": individualPoolResources,
                    "showGantt": True,
                }
            )
        return ctx

    rows = (
        GridFieldInteger(
            "id",
            title="identifier",
            key=True,
            editable=False,
            formatter="detail",
            extra='"role":"input/operationplanresource"',
            initially_hidden=True,
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldText("operationplan__reference", title=_("reference"), editable=False),
        GridFieldText(
            "operationplan__remark",
            title=_("remark"),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="operationplan__owner__reference",
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            initially_hidden=True,
            editable=False,
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
            "operationplan__item__name",
            title=_("item"),
            editable=False,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "operationplan__location__name",
            title=_("location"),
            editable=False,
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "operationplan__operation__name",
            title=_("operation"),
            editable=False,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "operationplan__batch",
            title=_("batch"),
            editable=False,
            field_name="operationplan__batch",
            initially_hidden=True,
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
            "operationplan__startdate",
            title=_("start date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"%s", "defaultValue":""}, "summaryType":"min"'
            % settings.DATETIME_FORMAT,
        ),
        GridFieldDateTime(
            "operationplan__enddate",
            title=_("end date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"%s", "defaultValue":""}, "summaryType":"max"'
            % settings.DATETIME_FORMAT,
        ),
        GridFieldDuration(
            "opplan_duration",
            title=_("duration"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "opplan_net_duration",
            title=_("net duration"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "operationplan__quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "operationplan__quantity_completed",
            title=_("quantity completed"),
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "operationplan__status",
            title=_("status"),
            choices=OperationPlan.orderstatus,
        ),
        GridFieldNumber(
            "operationplan__criticality",
            title=_("criticality"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "operationplan__delay",
            title=_("delay"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
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
        GridFieldText(
            "operationplan__type",
            title=_("type"),
            field_name="operationplan__type",
            editable=False,
        ),
        GridFieldNumber(
            "quantity",
            title=_("load quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText("setup", title=_("setup"), editable=False, initially_hidden=True),
        GridFieldDateTime(
            "setup_end",
            title=_("setup end date"),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldDuration(
            "setup_duration",
            title=_("setup duration"),
            editable=False,
            initially_hidden=True,
            search=False,
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
            search=False,
        ),
        GridFieldJSON(
            "resources",
            title=_("resources"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        # Optional fields referencing the item
        GridFieldText(
            "operationplan__item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__item__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("description")),
        ),
        GridFieldText(
            "operationplan__item__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("category")),
        ),
        GridFieldText(
            "operationplan__item__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
        ),
        GridFieldCurrency(
            "operationplan__item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operationplan__item__volume",
            title=format_lazy("{} - {}", _("item"), _("volume")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operationplan__item__weight",
            title=format_lazy("{} - {}", _("item"), _("weight")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__item__uom",
            title=format_lazy("{} - {}", _("item"), _("unit of measure")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operationplan__item__periodofcover",
            title=format_lazy("{} - {}", _("item"), _("period of cover")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__item__owner",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="operationplan__item__owner__name",
        ),
        GridFieldText(
            "operationplan__item__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("source")),
        ),
        GridFieldLastModified(
            "operationplan__item__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("last modified")),
        ),
        # Optional fields referencing the operation location
        GridFieldText(
            "operationplan__operation__location__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("description")),
        ),
        GridFieldText(
            "operationplan__operation__location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__location__available",
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="operationplan__operation__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "operationplan__operation__location__owner",
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("owner")),
            field_name="operationplan__operation__location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__location__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("source")),
        ),
        GridFieldLastModified(
            "operationplan__operation__location__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("last modified")),
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
        GridFieldBool(
            "resource__constrained",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("constrained")),
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
            "resource_location",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("location")),
            field_name="resource__location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        # Optional fields referencing the resource location
        GridFieldText(
            "resource__location__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("description")
            ),
        ),
        GridFieldText(
            "resource__location__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("category")
            ),
        ),
        GridFieldText(
            "resource__location__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("subcategory")
            ),
        ),
        GridFieldText(
            "resource__location__available",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("available")
            ),
            field_name="resource__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "resource__location__owner",
            extra='"role":"input/location"',
            editable=False,
            title=format_lazy("{} - {} - {}", _("resource"), _("location"), _("owner")),
            initially_hidden=True,
            field_name="resource__location__owner__name",
            formatter="detail",
        ),
        GridFieldText(
            "resource__location__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("source")
            ),
        ),
        # Status field currently not used
        # GridFieldChoice('status', title=_('load status'), choices=OperationPlanResource.OPRstatus),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified", initially_hidden=True),
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
                "function": "grid.setStatus('proposed', 'operationplan__')",
            },
            {
                "name": "approved",
                "label": format_lazy(
                    _("change status to {status}"), status=_("approved")
                ),
                "function": "grid.setStatus('approved', 'operationplan__')",
            },
            {
                "name": "confirmed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("confirmed")
                ),
                "function": "grid.setStatus('confirmed', 'operationplan__')",
            },
            {
                "name": "completed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("completed")
                ),
                "function": "grid.setStatus('completed', 'operationplan__')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed', 'operationplan__')",
            },
        ]
