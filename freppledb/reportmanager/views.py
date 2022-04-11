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

from datetime import timedelta, date
import json
import logging
import sqlparse

from django.conf import settings
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
    Http404,
)
from django.shortcuts import render
from django.template import Template
from django.utils.encoding import smart_str

from django.utils.translation import gettext as _

from freppledb.common.models import User
from freppledb.common.report import (
    create_connection,
    GridReport,
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
from .models import SQLReport, SQLColumn
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
    template = "reportmanager/reportlist.html"
    title = _("my reports")
    model = SQLReport
    help_url = "user-interface/report-manager.html"
    message_when_empty = Template(
        """
        <h3>You didn't find the exact report you need? Do not despair!</h3>
        <br>
        You can add custom reports by writing a SQL query.<br>
        <br>
        Your custom report will show up in the navigation menu.<br>
        It will have the same filter, sort and export functionalities as all other reports.<br>
        You can choose to keep the report private or share it with other users.<br>
        <br><br>
        <a href="{{request.prefix}}/data/reportmanager/sqlreport/add/" class="btn btn-primary">Add custom report</a>
        <br>
        """
    )
    frozenColumns = 1
    rows = (
        GridFieldInteger(
            "id", title=_("identifier"), key=True, extra="formatter:reportlink"
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
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        return SQLReport.objects.filter(Q(user=request.user) | Q(public=True))


class ReportManager(GridReport):

    template = "reportmanager/reportmanager.html"
    reportkey = "reportmanager.reportmanager"
    help_url = "user-interface/report-manager.html"
    default_sort = ""

    @staticmethod
    def _filter_ne(reportrow, field, data):
        if isinstance(
            reportrow,
            (
                GridFieldCurrency,
                GridFieldInteger,
                GridFieldNumber,
                GridFieldDate,
                GridFieldDateTime,
            ),
        ):
            return ('"%s" is distinct from %%s' % field, [smart_str(data).strip()])
        else:
            return (
                'upper("%s") is distinct from upper(%%s)' % field,
                [smart_str(data).strip()],
            )

    @staticmethod
    def _filter_bn(reportrow, field, data):
        return (
            'not upper("%s") like upper(%%s)' % field,
            ["%s%%" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_en(reportrow, field, data):
        return (
            'not upper("%s") like upper(%%s)' % field,
            ["%%%s" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_nc(reportrow, field, data):
        return (
            'not upper("%s") like upper(%%s)' % field,
            ["%%%s%%" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_ni(reportrow, field, data):
        args = smart_str(data).strip().split(",")
        return ('"%s" not in (%s)' % (field, ",".join(["%s"] * len(args))), args)

    @staticmethod
    def _filter_in(reportrow, field, data):
        args = smart_str(data).strip().split(",")
        return ('"%s" in (%s)' % (field, ",".join(["%s"] * len(args))), args)

    @staticmethod
    def _filter_eq(reportrow, field, data):
        if isinstance(
            reportrow,
            (
                GridFieldCurrency,
                GridFieldInteger,
                GridFieldNumber,
                GridFieldDate,
                GridFieldDateTime,
            ),
        ):
            return ('"%s" = %%s' % field, [smart_str(data).strip()])
        else:
            return ('upper("%s") = upper(%%s)' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_bw(reportrow, field, data):
        return (
            'upper("%s") like upper(%%s)' % field,
            ["%s%%" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_gt(reportrow, field, data):
        return ('"%s" > %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_gte(reportrow, field, data):
        return ('"%s" >= %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_lt(reportrow, field, data):
        return ('"%s" < %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_lte(reportrow, field, data):
        return ('"%s" <= %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_ew(reportrow, field, data):
        return (
            'upper("%s") like upper(%%s)' % field,
            ["%%%s" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_cn(reportrow, field, data):
        return (
            'upper("%s") like upper(%%s)' % field,
            ["%%%s%%" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_win(reportrow, field, data):
        return (
            '"%s" <= %%s' % field,
            [date.today() + timedelta(int(float(smart_str(data))))],
        )

    @staticmethod
    def _filter_ico(reportrow, field, data):
        # not implmented
        return ""

    _filter_map_jqgrid_sql = {
        # jqgrid op: (django_lookup, use_exclude, use_extra_where)
        "ne": _filter_ne.__func__,
        "bn": _filter_bn.__func__,
        "en": _filter_en.__func__,
        "nc": _filter_nc.__func__,
        "ni": _filter_ni.__func__,
        "in": _filter_in.__func__,
        "eq": _filter_eq.__func__,
        "bw": _filter_bw.__func__,
        "gt": _filter_gt.__func__,
        "ge": _filter_gte.__func__,
        "lt": _filter_lt.__func__,
        "le": _filter_lte.__func__,
        "ew": _filter_ew.__func__,
        "cn": _filter_cn.__func__,
        "win": _filter_win.__func__,
        "ico": _filter_ico.__func__,
    }

    @classmethod
    def title(cls, request, *args, **kwargs):
        if args and args[0]:
            if not hasattr(request, "report"):
                request.report = (
                    SQLReport.objects.all().using(request.database).get(pk=args[0])
                )
            return request.report.name
        else:
            return _("Add custom report")

    @classmethod
    def has_permission(cls, user):
        return user.has_perm("reportmanager.view_sqlreport")

    @classmethod
    def getScenarios(cls, request, *args, **kwargs):
        """
        Because your report executes SQL statements on the database, we can
        only allow you to run on scenarios in which you are a superuser.
        """
        scenario_permissions = []
        if len(request.user.scenarios) > 1:
            original_database = request.database
            for scenario in request.user.scenarios:
                try:
                    user = User.objects.using(scenario.name).get(
                        username=request.user.username
                    )

                    if user.is_superuser:
                        scenario_permissions.append(
                            [
                                scenario.name,
                                scenario.description
                                if scenario.description
                                else scenario.name,
                                1 if scenario.name == original_database else 0,
                            ]
                        )
                except Exception:
                    pass
        return scenario_permissions

    @classmethod
    def _getRowByName(cls, request, name):
        for i in request.rows:
            if i.name == name:
                return i
        raise KeyError("row doesn't exists")

    @classmethod
    def _getFilter_internal(cls, request, filterdata, *args, **kwargs):
        q_filters = [[], []]
        for rule in filterdata["rules"]:
            try:
                op, field, data = rule["op"], rule["field"], rule["data"]
                reportrow = cls._getRowByName(request, field)
                if data == "":
                    # No filter value specified, which makes the filter invalid
                    continue
                else:
                    t = cls._filter_map_jqgrid_sql[op](reportrow, field, data)
                    q_filters[0].append(t[0])
                    q_filters[1].extend(t[1])
            except Exception:
                pass  # Silently ignore invalid filters
        if "groups" in filterdata:
            for group in filterdata["groups"]:
                try:
                    z = cls._getFilter_internal(request, group)
                    if z[0]:
                        q_filters[0].append("(%s)" % z[0])
                        q_filters[1].extend(z[1])
                except Exception:
                    pass  # Silently ignore invalid groups
        if q_filters[0]:
            if filterdata["groupOp"].upper() == "OR":
                q_filters[0] = " or ".join(q_filters[0])
            else:
                q_filters[0] = " and ".join(q_filters[0])
        return q_filters

    @classmethod
    def getFilter(cls, request, *args, **kwargs):
        # Jqgrid-style advanced filtering
        _filters = request.GET.get("filters")
        if _filters and _filters != '{"groupOp":"AND","rules":[]}':
            # Validate complex search JSON data
            try:
                return cls._getFilter_internal(
                    request, json.loads(_filters), *args, **kwargs
                )
            except ValueError:
                return ("", [])

        # Django-style filtering, using URL parameters
        q_filters = [[], []]
        for i, j in request.GET.items():
            for r in request.rows:
                try:
                    if not r.name or not j:
                        continue
                    elif i == r.field_name:
                        op = "eq"
                    elif i.startswith(r.field_name + "__"):
                        op = i[len(r.field_name + "__") :]
                    else:
                        continue
                    t = cls._filter_map_jqgrid_sql[op](r, r.name, j)
                    q_filters[0].append(t[0])
                    q_filters[1].extend(t[1])
                except Exception:
                    pass  # silently ignore invalid filters
        if q_filters[0]:
            q_filters[0] = " and ".join(q_filters[0])
        return q_filters

    @classmethod
    def data_query(cls, request, *args, page=None, **kwargs):
        # Main query that will return all data records.
        # It implements filtering, paging and sorting.
        conn = None
        if not hasattr(request, "report"):
            request.report = (
                SQLReport.objects.all().using(request.database).get(pk=args[0])
            )
        if request.report and request.report.sql:
            try:
                conn = create_connection(request.database)
                with conn.cursor() as cursor:
                    sqlrole = settings.DATABASES[request.database].get(
                        "SQL_ROLE", "report_role"
                    )
                    if sqlrole:
                        cursor.execute("set role %s" % (sqlrole,))
                    if not hasattr(request, "filter"):
                        request.filter = cls.getFilter(request, *args, **kwargs)
                    cursor.execute(
                        "select * from (%s) t_subquery %s order by %s %s %s"
                        % (
                            request.report.sql.replace("%", "%%"),
                            "where %s" % request.filter[0] if request.filter[0] else "",
                            cls._apply_sort_index(request),
                            ("offset %s" % ((page - 1) * request.pagesize + 1))
                            if page and page > 1
                            else "",
                            "limit %s" % request.pagesize if page else "",
                        ),
                        request.filter[1],
                    )
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
        if request.report and request.report.sql:
            try:
                conn = create_connection(request.database)
                with conn.cursor() as cursor:
                    sqlrole = settings.DATABASES[request.database].get(
                        "SQL_ROLE", "report_role"
                    )
                    if sqlrole:
                        cursor.execute("set role %s" % (sqlrole,))
                    if not hasattr(request, "filter"):
                        request.filter = cls.getFilter(request, *args, **kwargs)
                    cursor.execute(
                        "select count(*) from (%s) t_subquery %s"
                        % (
                            request.report.sql.replace("%", "%%"),
                            "where %s" % request.filter[0] if request.filter[0] else "",
                        ),
                        request.filter[1],
                    )
                    return cursor.fetchone()[0]
            finally:
                if conn:
                    conn.close()
        else:
            return 0

    def rows(self, request, *args, **kwargs):
        cols = []
        if args:
            for c in (
                SQLColumn.objects.using(request.database)
                .filter(report=args[0])
                .order_by("sequence")
            ):
                if c.format == "number":
                    cols.append(
                        GridFieldNumber(c.name, title=_(c.name), editable=False)
                    )
                elif c.format == "datetime":
                    cols.append(
                        GridFieldDateTime(c.name, title=_(c.name), editable=False)
                    )
                elif c.format == "date":
                    cols.append(GridFieldDate(c.name, title=_(c.name), editable=False))
                elif c.format == "integer":
                    cols.append(
                        GridFieldInteger(c.name, title=_(c.name), editable=False)
                    )
                elif c.format == "duration":
                    cols.append(
                        GridFieldDuration(c.name, title=_(c.name), editable=False)
                    )
                elif c.format == "text":
                    cols.append(GridFieldText(c.name, title=_(c.name), editable=False))
                elif c.format == "character":
                    cols.append(GridFieldText(c.name, title=_(c.name), editable=False))
                elif c.format == "bool":
                    cols.append(GridFieldBool(c.name, title=_(c.name), editable=False))
                elif c.format == "currency":
                    cols.append(
                        GridFieldCurrency(c.name, title=_(c.name), editable=False)
                    )
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
            try:
                request.report = SQLReport.objects.using(request.database).get(
                    pk=args[0]
                )
            except SQLReport.DoesNotExist:
                raise Http404("Report doesn't exist")
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
            "title": request.report.name
            if request.report
            else cls.title(request, *args, **kwargs),
            "report": getattr(request, "report", None),
        }

    @classmethod
    def post(cls, request, *args, **kwargs):
        # Check permissions
        if (
            request.method != "POST"
            or request.headers.get("x-requested-with") != "XMLHttpRequest"
            or (
                not request.user.has_perm("reportmanager.add_sqlreport")
                and not request.user.has_perm("reportmanager.change_sqlreport")
            )
        ):
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
                try:
                    m = f.save(commit=False)
                    m.user = request.user
                    m.save()
                    return JsonResponse({"id": m.id, "status": "ok"})
                except Exception as e:
                    # Exposing the exception to the user is acceptable here.
                    # Otherwise we don't provide feedback on how the query needs correcting
                    return JsonResponse(
                        {"id": m.id, "status": "Error: %s" % e}
                    )  # lgtm[py/stack-trace-exposure]
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
