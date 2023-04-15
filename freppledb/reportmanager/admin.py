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

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from freppledb.admin import data_site
from freppledb.common.adminforms import MultiDBModelAdmin
from django.forms import ModelForm

from .models import SQLReport


class SQLReportForm(ModelForm):
    class Meta:
        model = SQLReport
        fields = "__all__"


@admin.register(SQLReport, site=data_site)
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
