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

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from freppledb.output.models import Problem
from freppledb.common.report import (
    GridReport,
    GridFieldText,
    GridFieldNumber,
    GridFieldDateTime,
    GridFieldInteger,
)


def getEntities(request):
    return tuple(
        [
            (i["entity"], format_lazy("{}:{}", _(i["entity"]), i["id__count"]))
            for i in Problem.objects.using(request.database)
            .values("entity")
            .annotate(Count("id"))
            .order_by("entity")
        ]
    )


def getNames(request):
    return tuple(
        [
            (i["name"], format_lazy("{}:{}", _(i["name"]), i["id__count"]))
            for i in Problem.objects.using(request.database)
            .values("name")
            .annotate(Count("id"))
            .order_by("name")
        ]
    )


class Report(GridReport):
    """
    A list report to show problems.
    """

    template = "output/problem.html"
    title = _("Problem report")
    basequeryset = (
        Problem.objects
    )  # TODO .extra(select={'forecast': "select name from forecast where out_problem.owner like forecast.name || ' - %%'",})
    model = Problem
    permissions = (("view_problem_report", "Can view problem report"),)
    frozenColumns = 0
    editable = False
    multiselect = False
    help_url = "user-interface/plan-analysis/problem-report.html"
    rows = (
        GridFieldInteger("id", title=_("id"), key=True, editable=False, hidden=True),
        GridFieldText(
            "entity", title=_("entity"), editable=False, align="center"
        ),  # TODO choices=getEntities
        GridFieldText(
            "name", title=_("name"), editable=False, align="center"
        ),  # TODO choices=getNames
        GridFieldText(
            "owner", title=_("owner"), editable=False, extra='"formatter":probfmt'
        ),
        GridFieldText("description", title=_("description"), editable=False, width=350),
        GridFieldDateTime("startdate", title=_("start date"), editable=False),
        GridFieldDateTime("enddate", title=_("end date"), editable=False),
    )
