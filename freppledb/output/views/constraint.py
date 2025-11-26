#
# Copyright (C) 2010-2013 by frePPLe bv
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

from django.db.models import Count
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str

from freppledb.output.models import Constraint
from freppledb.common.report import (
    GridReport,
    GridFieldText,
    GridFieldNumber,
    GridFieldDateTime,
    GridFieldInteger,
)
from freppledb.input.models import Demand, Resource, Buffer, Operation


entities = (
    ("demand", _("demand")),
    ("material", _("material")),
    ("capacity", _("capacity")),
    ("operation", _("operation")),
)

names = (
    ("overload", _("overload")),
    ("underload", _("underload")),
    ("material shortage", _("material shortage")),
    ("excess", _("excess")),
    ("short", _("short")),
    ("early", _("early")),
    ("late", _("late")),
    ("unplanned", _("unplanned")),
    ("precedence", _("precedence")),
    ("before fence", _("before fence")),
    ("before current", _("before current")),
)


def getEntities(request):
    return tuple(
        [
            (i["entity"], format_lazy("{}:{}", _(i["entity"]), i["id__count"]))
            for i in Constraint.objects.using(request.database)
            .values("entity")
            .annotate(Count("id"))
            .order_by("entity")
        ]
    )


def getNames(request):
    return tuple(
        [
            (i["name"], format_lazy("{}:{}", _(i["name"]), i["id__count"]))
            for i in Constraint.objects.using(request.database)
            .values("name")
            .annotate(Count("id"))
            .order_by("name")
        ]
    )


class BaseReport(GridReport):
    """
    A list report to show constraints.
    """

    template = "output/constraint.html"
    title = _("Constraint report")
    basequeryset = Constraint.objects.all()
    permissions = (("view_constraint_report", "Can view constraint report"),)
    frozenColumns = 0
    editable = False
    multiselect = False
    help_url = "user-interface/plan-analysis/constraint-report.html"
    detail_post_title = _("constrained demand")
    detailmodel = None
    rows = (
        GridFieldInteger("id", title=_("id"), key=True, editable=False, hidden=True),
        GridFieldText(
            "demand",
            title=_("demand"),
            editable=False,
            formatter="detail",
            extra='"role":"input/demand"',
        ),
        GridFieldText(
            "forecast",
            title=_("forecast"),
            editable=False,
            formatter="detail",
            extra='"role":"forecast/forecast"',
        ),
        GridFieldText(
            "entity", title=_("entity"), editable=False, width=80, align="center"
        ),
        GridFieldText(
            "name", title=_("name"), editable=False, width=100, align="center"
        ),
        GridFieldText(
            "owner", title=_("owner"), editable=False, extra='"formatter":probfmt'
        ),
        GridFieldText("description", title=_("description"), editable=False, width=350),
        GridFieldDateTime("startdate", title=_("start date"), editable=False),
        GridFieldDateTime("enddate", title=_("end date"), editable=False),
    )

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0] and reportclass.detailmodel:
            request.session["lasttab"] = "constraint"
            if (
                reportclass.detailmodel._meta.model_name == "buffer"
                and " @ " not in args[0]
            ):
                b = Buffer.objects.get(id=args[0])
                bufferName = b.item.name + " @ " + b.location.name
            return {
                "active_tab": "constraint",
                "title": force_str(reportclass.detailmodel._meta.verbose_name)
                + " "
                + (bufferName if "bufferName" in vars() else args[0]),
                "post_title": reportclass.detail_post_title,
                "model": reportclass.detailmodel,
            }
        else:
            return {"active_tab": "constraint"}


class ReportByDemand(BaseReport):
    template = "output/constraint_demand.html"

    detailmodel = Demand

    detail_post_title = _("why short or late?")

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "constraint"
            return Constraint.objects.all().filter(demand__exact=args[0])
        else:
            return Constraint.objects.all()


class ReportByBuffer(BaseReport):
    template = "output/constraint_buffer.html"

    detailmodel = Buffer

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            if not " @ " in args[0]:
                b = Buffer.objects.get(id=args[0])
                bufferName = b.item.name + " @ " + b.location.name
            else:
                bufferName = args[0]
            request.session["lasttab"] = "constraint"
            return Constraint.objects.all().filter(
                owner__exact=bufferName, entity__exact="material"
            )
        else:
            return Constraint.objects.all()


class ReportByOperation(BaseReport):
    template = "output/constraint_operation.html"

    detailmodel = Operation

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "constraint"
            return Constraint.objects.all().filter(
                owner__exact=args[0], entity__exact="operation"
            )
        else:
            return Constraint.objects.all()


class ReportByResource(BaseReport):
    template = "output/constraint_resource.html"

    detailmodel = Resource

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "constraint"
            return Constraint.objects.all().filter(
                owner__exact=args[0], entity__exact="capacity"
            )
        else:
            return Constraint.objects.all()
