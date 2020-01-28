#
# Copyright (C) 2019 by frePPLe bvba
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

from datetime import timedelta
import json
import logging
import sqlparse

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections, transaction
from django.forms import ModelForm
from django.http import (
    StreamingHttpResponse,
    HttpResponse,
    JsonResponse,
    HttpResponseNotAllowed,
)
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

from freppledb.reportmanager.models import SQLReport
from django.contrib.auth.decorators import permission_required

logger = logging.getLogger(__name__)


class SQLReportForm(ModelForm):
    class Meta:
        model = SQLReport
        fields = "__all__"


@permission_required("create_custom_report", raise_exception=True)
def getSchema(request):
    """
    Construct schema information of the following form, sorted by db_table_name.
        [
            ("db_table_name",
                [
                    ("db_column_name", "DbFieldType"),
                    (...),
                ]
            )
        ]
    This data is then rendered with a template, and asynchronously added to the page.
    """
    # Build schema info
    schema = []
    connection = connections[request.database]
    with connection.cursor() as cursor:
        tables_to_introspect = connection.introspection.table_names(
            cursor, include_views=True
        )
        for table_name in tables_to_introspect:
            td = []
            table_description = connection.introspection.get_table_description(
                cursor, table_name
            )
            for row in table_description:
                column_name = row[0]
                try:
                    field_type = connection.introspection.get_field_type(
                        row[1], row
                    ).split(".")[-1]
                except KeyError:
                    field_type = "Unknown"
                td.append((column_name, field_type))
            schema.append((table_name, td))
    return render(request, "reportmanager/schema.html", context={"schema": schema})


class ReportManager(View):

    title = _("report manager")
    permissions = (("create_custom_report", "Can create custom reports"),)
    template = "reportmanager/reportmanager.html"
    reportkey = "reportmanager.reportmanager"

    @classmethod
    def get(cls, request, *args, **kwargs):
        request.prefs = request.user.getPreference(
            cls.reportkey, database=request.database
        )
        if args:
            report = SQLReport.objects.using(request.database).get(pk=args[0])
        else:
            report = None
        return render(
            request,
            cls.template,
            {
                "title": report.name if report else _("Report manager"),
                "report": report,
                "reportkey": "%s.%s" % (cls.reportkey, report.id)
                if report
                else cls.reportkey,
            },
        )

    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @classmethod
    def getColModel(cls, name, oid, counter):
        colmodel = {
            "name": name,
            "index": name,
            "label": name,
            "editable": False,
            "title": False,
            "counter": counter,
        }
        if oid == 1700:
            # Numeric field
            colmodel.update(
                {
                    "align": "center",
                    "formatter": "number",
                    "searchrules": {"number": True},
                    "searchoptions": {
                        "sopt": ["eq", "ne", "in", "ni", "lt", "le", "gt", "ge"],
                        "searchhidden": True,
                    },
                    "formatoptions": {"defaultValue": "", "decimalPlaces": "auto"},
                    "width": 70,
                }
            )
        elif oid == 1184:
            # Datetime field
            colmodel.update(
                {
                    "align": "center",
                    "formatter": "date",
                    "searchoptions": {
                        "sopt": [
                            "cn",
                            "em",
                            "nm",
                            "in",
                            "ni",
                            "eq",
                            "bw",
                            "ew",
                            "bn",
                            "nc",
                            "en",
                            "win",
                        ],
                        "searchhidden": True,
                    },
                    "formatoptions": {
                        "srcformat": "Y-m-d H:i:s",
                        "newformat": "Y-m-d H:i:s",
                    },
                    "width": 140,
                }
            )
        elif oid == 23:
            # Integer
            colmodel.update(
                {
                    "align": "center",
                    "formatter": "integer",
                    "searchrules": {"integer": True},
                    "searchoptions": {
                        "sopt": ["eq", "ne", "in", "ni", "lt", "le", "gt", "ge"],
                        "searchhidden": True,
                    },
                    "formatoptions": {"defaultValue": ""},
                    "width": 70,
                }
            )
        elif oid == 1186:
            # Duration field
            colmodel.update(
                {
                    "align": "center",
                    "formatter": "duration",
                    "searchoptions": {
                        "sopt": ["eq", "ne", "in", "ni", "lt", "le", "gt", "ge"],
                        "searchhidden": True,
                    },
                    "width": 80,
                }
            )
        elif oid == 1043:
            # Text field
            colmodel.update(
                {
                    "align": "left",
                    "searchoptions": {
                        "sopt": [
                            "cn",
                            "nc",
                            "eq",
                            "ne",
                            "lt",
                            "le",
                            "gt",
                            "ge",
                            "bw",
                            "bn",
                            "in",
                            "ni",
                            "ew",
                            "en",
                        ],
                        "searchhidden": True,
                    },
                    "width": 200,
                }
            )
            if name in ("item", "item_id"):
                colmodel.update({"formatter": "detail", "role": "input/item"})
            elif name in ("location", "location_id"):
                colmodel.update({"formatter": "detail", "role": "input/location"})
            elif name in ("supplier", "supplier_id"):
                colmodel.update({"formatter": "detail", "role": "input/supplier"})
            elif name in ("resource", "resource_id"):
                colmodel.update({"formatter": "detail", "role": "input/resource"})
            elif name in ("customer", "customer_id"):
                colmodel.update({"formatter": "detail", "role": "input/customer"})
            elif name in ("demand", "demand_id"):
                colmodel.update({"formatter": "detail", "role": "input/demand"})
        else:
            # Text, jsonb and any other unknown field
            colmodel.update(
                {
                    "align": "left",
                    "searchoptions": {
                        "sopt": [
                            "cn",
                            "nc",
                            "eq",
                            "ne",
                            "lt",
                            "le",
                            "gt",
                            "ge",
                            "bw",
                            "bn",
                            "in",
                            "ni",
                            "ew",
                            "en",
                        ],
                        "searchhidden": True,
                    },
                    "width": 200,
                }
            )
        return colmodel

    @classmethod
    def post(cls, request, *args, **kwargs):
        # Allow only post from superusers
        if not request.user.is_superuser:
            return HttpResponseNotAllowed(
                ["post"], content="Only a superuser can execute SQL statements"
            )
        if request.method != "POST" or not request.is_ajax():
            return HttpResponseNotAllowed("Only ajax post requests allowed")

        if "format" in request.POST:
            formatted = sqlparse.format(
                request.POST.get("sql", ""),
                keyword_case="lower",
                identifier_case="lower",
                strip_comments=False,
                reindent=True,
                wrap_after=50,
                indent_tabs=False,
                indent_width=2,
            )
            return JsonResponse({"formatted": formatted})

        elif "save" in request.POST:
            f = SQLReportForm(request.POST)
            if f.is_valid():
                m = f.save(commit=False)
                m.user = request.user
                m.save()
            return JsonResponse({"result": 1})

        elif "delete" in request.POST:
            SQLReport.objects.using(request.database).filter(
                pk=request.POST["id"]
            ).delete()
            return HttpResponse("ok")

        elif "test" in request.POST:

            def runQuery():
                try:
                    with connections[request.database].cursor() as cursor:
                        with transaction.atomic():
                            cursor.execute(sql=request.POST["sql"])
                            if cursor.description:
                                counter = 0
                                columns = []
                                colmodel = []
                                for f in cursor.description:
                                    columns.append(f[0])
                                    colmodel.append(
                                        cls.getColModel(f[0], f[1], counter)
                                    )
                                    counter += 1

                                yield """{
                                    "rowcount": %s,
                                    "status": "ok",
                                    "columns": %s,
                                    "colmodel": %s,
                                    "data": [
                                    """ % (
                                    cursor.rowcount,
                                    json.dumps(columns),
                                    json.dumps(colmodel),
                                )
                                first = True
                                for result in cursor.fetchall():
                                    if first:
                                        yield json.dumps(
                                            dict(
                                                zip(
                                                    columns,
                                                    [
                                                        i
                                                        if i is None
                                                        else i.total_seconds()
                                                        if isinstance(i, timedelta)
                                                        else str(i)
                                                        for i in result
                                                    ],
                                                )
                                            )
                                        )
                                        first = False
                                    else:
                                        yield ",%s" % json.dumps(
                                            dict(
                                                zip(
                                                    columns,
                                                    [
                                                        i
                                                        if i is None
                                                        else i.total_seconds()
                                                        if isinstance(i, timedelta)
                                                        else str(i)
                                                        for i in result
                                                    ],
                                                )
                                            )
                                        )
                                yield "]}"
                            elif cursor.rowcount:
                                yield '{"rowcount": %s, "status": "Updated %s rows"}' % (
                                    cursor.rowcount,
                                    cursor.rowcount,
                                )
                            else:
                                yield '{"rowcount": %s, "status": "Done"}' % cursor.rowcount
                except GeneratorExit:
                    pass
                except Exception as e:
                    yield json.dumps({"status": str(e)})

            return StreamingHttpResponse(
                content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
                streaming_content=runQuery(),
            )

        else:
            print("request.", request.POST)
            return HttpResponseNotAllowed("Unknown post request")
