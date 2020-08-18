#
# Copyright (C) 2020 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from urllib.parse import urlencode

from django.contrib.admin.utils import quote
from django.db import DEFAULT_DB_ALIAS
from django.db.models import F
from django.http import HttpResponse
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from freppledb.common.middleware import _thread_locals
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
    limit = 20
    orderby = "latedemandvalue"

    def args(self):
        return "?%s" % urlencode({"limit": self.limit, "orderby": self.orderby})

    @classmethod
    def render(cls, request=None):
        limit = int(request.GET.get("limit", cls.limit))
        orderby = request.GET.get("orderby", cls.orderby)
        currency = getCurrency()
        try:
            db = _thread_locals.request.database or DEFAULT_DB_ALIAS
        except Exception:
            db = DEFAULT_DB_ALIAS
        result = [
            '<div class="table-responsive"><table class="table table-condensed table-hover">',
            '<thead><tr><th class="alignleft">%s</th><th class="aligncenter">%s</th>'
            '<th class="aligncenter">%s</th><th class="aligncenter">%s</th></tr></thead>'
            % (
                capfirst(force_text(_("item"))),
                capfirst(force_text(_("value of late demands"))),
                capfirst(force_text(_("quantity of late demands"))),
                capfirst(force_text(_("number of late demands"))),
            ),
        ]
        if orderby == "latedemandcount":
            topitems = (
                Item.objects.all()
                .using(db)
                .order_by("-latedemandcount", "latedemandvalue", "-latedemandquantity")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        elif orderby == "latedemandquantity":
            topitems = (
                Item.objects.all()
                .using(db)
                .order_by("-latedemandquantity", "latedemandvalue", "-latedemandcount")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        else:
            topitems = (
                Item.objects.all()
                .using(db)
                .order_by("-latedemandvalue", "-latedemandquantity", "-latedemandcount")
                .filter(rght=F("lft") + 1, latedemandcount__gt=0)
                .only(
                    "name", "latedemandcount", "latedemandquantity", "latedemandvalue"
                )[:limit]
            )
        alt = False
        for rec in topitems:
            result.append(
                '<tr%s><td class="underline"><a href="%s/demand/%s/">%s</a></td>'
                '<td class="aligncenter">%s%s%s</td><td class="aligncenter">%s</td>'
                '<td class="aligncenter">%s</td></tr>'
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
