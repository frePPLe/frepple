#
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

from freppledb.reportmanager.models import SQLReport, SQLColumn
from freppledb.common.report import (
    create_connection,
    GridReport,
    _getCellValue,
    GridFieldText,
    GridFieldLastModified,
    GridFieldBoolNullable,
    GridFieldInteger,
    GridFieldBool,
    GridFieldNumber,
    GridFieldDuration,
    GridFieldCurrency,
    GridFieldDateTime,
    GridFieldDate,
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
    help_url = "user-guide/user-interface/report-manager.html"
    default_sort = ""

    @classmethod
    def has_permission(cls, user):
        return user.has_perm("reportmanager.view_sqlreport")

    @classmethod
    def data_query(cls, request, *args, **kwargs):
        # Main query that will return all data records.
        # It implements filtering, paging and sorting.
        conn = None
        if not hasattr(request, "report"):
            request.report = (
                SQLReport.objects.all().using(request.database).get(pk=args[0])
            )
        try:
            conn = create_connection(request.database)
            with conn.cursor() as cursor:
                sqlrole = settings.DATABASES[request.database].get(
                    "SQL_ROLE", "report_role"
                )
                if sqlrole:
                    cursor.execute("set role %s" % (sqlrole,))
                cursor.execute(
                    request.report.sql
                )  # xxx query may require arguments for filtering!!!!
                for rec in cursor.fetchall():
                    result = {}
                    idx = 0
                    for f in request.rows:
                        result[f.name] = rec[idx]
                        idx += 1
                    yield result
        finally:
            if conn:
                conn.close()

    @classmethod
    def count_query(cls, request, *args, **kwargs):
        # Query that returns the number of records in the report.
        # It implements filtering, but no paging or sorting.
        conn = None
        if not hasattr(request, "report"):
            request.report = (
                SQLReport.objects.all().using(request.database).get(pk=args[0])
            )
        try:
            conn = create_connection(request.database)
            with conn.cursor() as cursor:
                sqlrole = settings.DATABASES[request.database].get(
                    "SQL_ROLE", "report_role"
                )
                if sqlrole:
                    cursor.execute("set role %s" % (sqlrole,))
                cursor.execute(
                    "select count(*) from (" + request.report.sql + ") t_subquery"
                )  # xxx query may require arguments for filtering!!!!
                return cursor.fetchone()[0]
        finally:
            if conn:
                conn.close()

    def rows(self, request, *args, **kwargs):
        cols = []
        if args:
            for c in (
                SQLColumn.objects.using(request.database)
                .filter(report=args[0])
                .order_by("sequence")
            ):
                if c.format == "number":
                    cols.append(GridFieldNumber(_(c.name)))
                elif c.format == "datetime":
                    cols.append(GridFieldDateTime(_(c.name)))
                elif c.format == "date":
                    cols.append(GridFieldDate(_(c.name)))
                elif c.format == "integer":
                    cols.append(GridFieldInteger(_(c.name)))
                elif c.format == "duration":
                    cols.append(GridFieldDuration(_(c.name)))
                elif c.format == "text":
                    cols.append(GridFieldText(_(c.name)))
                elif c.format == "character":
                    cols.append(GridFieldText(_(c.name)))
                elif c.format == "bool":
                    cols.append(GridFieldBool(_(c.name)))
                elif c.format == "currency":
                    cols.append(GridFieldCurrency(_(c.name)))
        return cols

    @classmethod
    def getKey(cls, request, *args, **kwargs):
        if args:
            return "%s.%s.%s" % (cls.__module__, cls.__name__, args[0])
        else:
            return "%s.%s" % (cls.__module__, cls.__name__)

    @classmethod
    def get(cls, request, *args, **kwargs):
        # Extra permission check
        if args:
            request.report = SQLReport.objects.using(request.database).get(pk=args[0])
            if not cls.has_permission(request.user) or (
                not request.report.public and request.report.user.id != request.user.id
            ):
                return HttpResponseForbidden("You're not the owner of this report")
        else:
            request.report = None
            if not request.user.has_perm("reportmanager.add_sqlreport"):
                return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # Default logic
        return super().get(request, *args, **kwargs)

    @classmethod
    def extra_context(cls, request, *args, **kwargs):
        return {
            "title": request.report.name if request.report else cls.title,
            "report": getattr(request, "report", None),
        }

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
