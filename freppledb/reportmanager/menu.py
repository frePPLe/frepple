# Copyright (C) 2019 by frePPLe bv
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
    excludeFromBulkOperations=True,
)
