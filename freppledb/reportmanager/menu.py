# Copyright (C) 2019 by frePPLe bv
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

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from freppledb.common.menus import MenuItem
from freppledb.menu import menu

from .views import ReportList
from .models import SQLReport


def MyReports(request):
    if not request.user.has_perm(
        "reportmanager.view_sqlreport"
    ) and not request.user.has_perm("reportmanager.add_sqlreport"):
        return []
    result = []
    index = 1
    for x in (
        SQLReport.objects.all()
        .using(request.database)
        .filter(Q(user=request.user) | Q(public=True))
        .order_by("name")
    ):
        result.append(
            (
                index,
                x.name,
                MenuItem(
                    x.name,
                    url="/reportmanager/%s/" % x.id,
                    label=x.name,
                    index=index,
                    prefix=request.prefix,
                ),
            )
        )
        index += 1
    return result


menu.addGroup("myreports", label=_("my reports"), index=750)
menu.addItem("myreports", "myreports", callback=MyReports, index=100)
menu.addItem("myreports", "data", separator=True, index=1000)
menu.addItem(
    "myreports",
    "reportmanager",
    url="/data/reportmanager/sqlreport/",
    report=ReportList,
    permission="reportmanager.change_sqlreport",
    model=SQLReport,
    index=1100,
    admin=True,
)
