#
# Copyright (C) 2020 by frePPLe bv
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

from urllib.parse import urlencode

from django.contrib.admin.utils import quote
from django.db import DEFAULT_DB_ALIAS
from django.db.models import F
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.report import getCurrency
from freppledb.input.models import Item


@Dashboard.register
class AnalysisDemandProblems(Widget):
    name = "analysis_demand_problems"
    title = _("analyze late demands")
    tooltip = _("Spot the top items with many late demands")
    permissions = (("view_demand_report", "Can view demand report"),)
    asynchronous = True
    url = "/demand/?noautofilter&sidx=latedemandvalue%20desc%2C%20latedemandquantity%20desc%2C%20latedemandcount&sord=desc"
    exporturl = True
    size = 'lg'
    limit = 20
    orderby = "latedemandvalue"

    def args(self):
        return "?%s" % urlencode({"limit": self.limit, "orderby": self.orderby})

    @classmethod
    def render(cls, request=None):
        limit = int(request.GET.get("limit", cls.limit))
        orderby = request.GET.get("orderby", cls.orderby)
        currency = getCurrency()
        result = [
            '<div class="table-responsive"><table class="table table-sm table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="text-center">%s</th>'
            '<th class="text-center">%s</th><th class="text-center">%s</th></tr></thead>'
            % (
                capfirst(force_str(_("item"))),
                capfirst(force_str(_("value of late demands"))),
                capfirst(force_str(_("quantity of late demands"))),
                capfirst(force_str(_("number of late demands"))),
            ),
        ]
        if orderby == "latedemandcount":
            topitems = (
                Item.objects.all()
                .using(request.database)
                .order_by("-latedemandcount", "latedemandvalue", "-latedemandquantity")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        elif orderby == "latedemandquantity":
            topitems = (
                Item.objects.all()
                .using(request.database)
                .order_by("-latedemandquantity", "latedemandvalue", "-latedemandcount")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        else:
            topitems = (
                Item.objects.all()
                .using(request.database)
                .order_by("-latedemandvalue", "-latedemandquantity", "-latedemandcount")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        alt = False
        for rec in topitems:
            result.append(
                '<tr%s><td class="text-decoration-underline"><a href="%s/buffer/item/%s/">%s</a></td>'
                '<td class="text-center">%s%s%s</td><td class="text-center">%s</td>'
                '<td class="text-center">%s</td></tr>'
                % (
                    alt and ' class="altRow"' or "",
                    request.prefix,
                    quote(rec.name),
                    escape(rec.name),
                    currency[0],
                    int(rec.latedemandvalue),
                    currency[1],
                    int(rec.latedemandquantity),
                    rec.latedemandcount,
                )
            )
            alt = not alt
        result.append("</table></div>")
        return HttpResponse("\n".join(result))
