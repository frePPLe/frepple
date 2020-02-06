#
# Copyright (C) 2020 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
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
            "permissions": "reportmanager.change_report",
        },
        {
            "name": "comments",
            "label": _("comments"),
            "view": "admin:reportmanager_sqlreport_comment",
        },
        {
            "name": "history",
            # . Translators: Translation included with Django
            "label": _("History"),
            "view": "admin:reportmanager_sqlreport_history",
        },
    ]


data_site.register(SQLReport, SQLReport_admin)
