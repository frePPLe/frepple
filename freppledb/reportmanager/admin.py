#
# Copyright (C) 2020 by frePPLe bv
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

from django.utils.translation import gettext_lazy as _

from freppledb.admin import data_site
from freppledb.common.adminforms import MultiDBModelAdmin
from django.forms import ModelForm

from .models import SQLReport


class SQLReportForm(ModelForm):
    class Meta:
        model = SQLReport
        fields = "__all__"


class SQLReport_admin(MultiDBModelAdmin):
    model = SQLReport
    exclude = ("id",)
    save_on_top = True
    fieldsets = ((None, {"fields": (("name"), ("description"), ("public"), ("sql"))}),)

    form = SQLReportForm

    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:reportmanager_sqlreport_change",
            "permissions": "reportmanager.change_sqlreport",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:reportmanager_sqlreport_comment",
        },
    ]


data_site.register(SQLReport, SQLReport_admin)
