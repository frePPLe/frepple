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

import csv
from datetime import timedelta
from io import BytesIO, StringIO
import json
import logging
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import NamedStyle, PatternFill
from openpyxl.comments import Comment as CellComment
import sqlparse
import urllib

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.db import connections
from django.db.models import Q
from django.http import (
    StreamingHttpResponse,
    HttpResponse,
    JsonResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.formats import get_format
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from freppledb.reportmanager.models import SQLReport
from freppledb.common.report import (
    create_connection,
    GridReport,
    _getCellValue,
    GridFieldText,
    GridFieldLastModified,
    GridFieldBoolNullable,
    GridFieldInteger,
)
from .admin import SQLReportForm

logger = logging.getLogger(__name__)


@permission_required("reportmanager.add_sqlreport", raise_exception=True)
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
                    field_type = "JSONB"
                td.append((column_name, field_type))
            schema.append((table_name, td))
    return render(request, "reportmanager/schema.html", context={"schema": schema})


class ReportList(GridReport):
    template = "admin/base_site_grid.html"
    title = _("my reports")
    model = SQLReport
    help_url = "user-guide/user-interface/report-manager.html"
    frozenColumns = 1
    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"reportmanager/sqlreport"',
        ),
        GridFieldText("name", title=_("name")),
        GridFieldText("description", title=_("description")),
        GridFieldText("sql", title=_("SQL query")),
        GridFieldBoolNullable("public", title=_("public")),
        GridFieldText(
            "user__username",
            title=_("user"),
            editable=False,
            formatter="detail",
            extra='"role":"common/user"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        return SQLReport.objects.filter(Q(user=request.user) | Q(public=True))


class ReportManager(GridReport):

    title = _("report editor")
    template = "reportmanager/reportmanager.html"
    reportkey = "reportmanager.reportmanager"

    @classmethod
    def has_permission(cls, user):
        return user.has_perm("reportmanager.view_sqlreport")

    @classmethod
    def get(cls, request, *args, **kwargs):
        request.prefs = request.user.getPreference(
            cls.reportkey, database=request.database
        )
        if args:
            report = SQLReport.objects.using(request.database).get(pk=args[0])
            if not cls.has_permission(request.user) or (
                not report.public and report.user.id != request.user.id
            ):
                return HttpResponseForbidden("You're not the owner of this report")
        else:
            report = None
            if not request.user.has_perm("reportmanager.add_sqlreport"):
                return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        if report:
            fmt = request.GET.get("format", None)
            if fmt in ("spreadsheetlist", "spreadsheet"):
                # Return an excel spreadsheet
                out = BytesIO()
                cls._generate_spreadsheet_data(request, out, report, *args, **kwargs)
                response = HttpResponse(
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    content=out.getvalue(),
                )
                # Filename parameter is encoded as specified in rfc5987
                response["Content-Disposition"] = (
                    "attachment; filename*=utf-8''%s.xlsx"
                    % urllib.parse.quote(report.name)
                )
                response["Cache-Control"] = "no-cache, no-store"
                return response
            elif fmt in ("csvlist", "csv"):
                # Return CSV file
                response = StreamingHttpResponse(
                    content_type="text/csv; charset=%s" % settings.CSV_CHARSET,
                    streaming_content=cls._generate_csv_data(
                        request, report, *args, **kwargs
                    ),
                )
                # Filename parameter is encoded as specified in rfc5987
                response["Content-Disposition"] = (
                    "attachment; filename*=utf-8''%s.csv"
                    % urllib.parse.quote(report.name)
                )
                response["Cache-Control"] = "no-cache, no-store"
                return response
            elif fmt == "json":
                # Return json
                return StreamingHttpResponse(
                    content_type="application/json; charset=%s"
                    % settings.DEFAULT_CHARSET,
                    streaming_content=cls._generate_json_data(
                        database=request.database, sql=report.sql
                    ),
                )
        return render(
            request,
            cls.template,
            {
                "title": report.name if report else _("report editor"),
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
    def post(cls, request, *args, **kwargs):
        # Allow only post from superusers
        if not request.user.is_superuser:
            return HttpResponseNotAllowed(
                ["post"], content="Only a superuser can execute SQL statements"
            )
        if request.method != "POST" or not request.is_ajax():
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

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
            if "id" in request.POST:
                m = SQLReport.objects.using(request.database).get(pk=request.POST["id"])
                if m.user.id != request.user.id:
                    return HttpResponseForbidden("You're not the owner of this report")
                f = SQLReportForm(request.POST, instance=m)
            else:
                f = SQLReportForm(request.POST)
            if f.is_valid():
                m = f.save(commit=False)
                m.user = request.user
                m.save()
                return JsonResponse({"id": m.id})
            else:
                return HttpResponseServerError("Error saving report")

        elif "delete" in request.POST:
            pk = request.POST["id"]
            SQLReport.objects.using(request.database).filter(
                pk=pk, user=request.user
            ).delete()
            messages.add_message(
                request,
                messages.INFO,
                _('The %(name)s "%(obj)s" was deleted successfully.')
                % {"name": _("my report"), "obj": pk},
            )
            return HttpResponse("ok")

        elif "test" in request.POST:
            return StreamingHttpResponse(
                content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
                streaming_content=cls._generate_json_data(
                    database=request.database, sql=request.POST["sql"]
                ),
            )

        else:
            return HttpResponseNotAllowed("Unknown post request")

    @classmethod
    def getColModel(cls, name, oid, counter):
        colmodel = {
            "name": name,
            "index": name,
            "label": capfirst(name),
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

    @staticmethod
    def getSQL(sql):
        # TODO optionally wrap in another query that can be filtered, paged and sorted
        return sqlparse.split(sql)[0] if sql else ""

    @classmethod
    def _generate_json_data(cls, database, sql):
        conn = None
        try:
            conn = create_connection(database)
            with conn.cursor() as cursor:
                sqlrole = settings.DATABASES[database].get("SQL_ROLE", "report_role")
                if sqlrole:
                    cursor.execute("set role %s" % (sqlrole,))
                cursor.execute(sql=cls.getSQL(sql))
                if cursor.description:
                    counter = 0
                    columns = []
                    colmodel = []
                    for f in cursor.description:
                        columns.append(f[0])
                        colmodel.append(cls.getColModel(f[0], f[1], counter))
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
        finally:
            if conn:
                conn.close()

    @classmethod
    def _generate_csv_data(cls, request, report, *args, **kwargs):
        sf = StringIO()
        decimal_separator = get_format("DECIMAL_SEPARATOR", request.LANGUAGE_CODE, True)
        if decimal_separator == ",":
            writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=";")
        else:
            writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=",")

        # Write a Unicode Byte Order Mark header, aka BOM (Excel needs it to open UTF-8 file properly)
        yield cls.getBOM(settings.CSV_CHARSET)

        # Run the query
        conn = None
        try:
            conn = create_connection(request.database)
            with conn.cursor() as cursor:
                sqlrole = settings.DATABASES[request.database].get(
                    "SQL_ROLE", "report_role"
                )
                if sqlrole:
                    cursor.execute("set role %s" % (sqlrole,))
                cursor.execute(sql=cls.getSQL(report.sql))
                if cursor.description:
                    # Write header row
                    writer.writerow([f[0] for f in cursor.description])
                    yield sf.getvalue()

                # Write all output rows
                for result in cursor.fetchall():
                    # Clear the return string buffer
                    sf.seek(0)
                    sf.truncate(0)
                    writer.writerow(
                        [
                            cls._getCSVValue(
                                i, request=request, decimal_separator=decimal_separator
                            )
                            for i in result
                        ]
                    )
                    yield sf.getvalue()
        except GeneratorExit:
            pass
        finally:
            if conn:
                conn.close()

    @classmethod
    def _generate_spreadsheet_data(cls, request, out, report, *args, **kwargs):
        # Create a workbook
        wb = Workbook(write_only=True)
        ws = wb.create_sheet(title=report.name)

        # Create a named style for the header row
        readlonlyheaderstyle = NamedStyle(name="readlonlyheaderstyle")
        readlonlyheaderstyle.fill = PatternFill(fill_type="solid", fgColor="d0ebfb")
        wb.add_named_style(readlonlyheaderstyle)

        # Run the query
        conn = None
        try:
            conn = create_connection(request.database)
            comment = CellComment(
                force_text(_("Read only")), "Author", height=20, width=80
            )
            with conn.cursor() as cursor:
                sqlrole = settings.DATABASES[request.database].get(
                    "SQL_ROLE", "report_role"
                )
                if sqlrole:
                    cursor.execute("set role %s" % (sqlrole,))
                cursor.execute(sql=cls.getSQL(report.sql))
                if cursor.description:
                    # Write header row
                    header = []
                    for f in cursor.description:
                        cell = WriteOnlyCell(ws, value=f[0])
                        cell.style = "readlonlyheaderstyle"
                        cell.comment = comment
                        header.append(cell)
                    ws.append(header)

                    # Add an auto-filter to the table
                    ws.auto_filter.ref = "A1:%s1048576" % get_column_letter(len(header))

                # Write all output rows
                for result in cursor.fetchall():
                    ws.append([_getCellValue(i, request=request) for i in result])

            # Write the spreadsheet
            wb.save(out)
        finally:
            if conn:
                conn.close()
