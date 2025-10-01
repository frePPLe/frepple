#
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
from django.utils.encoding import smart_str, force_str
from django.utils.translation import gettext_lazy as _

from freppledb.common.localization import parseLocalizedDate, parseLocalizedDateTime
from freppledb.common.models import User, Parameter
from freppledb.common.report import (
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
from freppledb.common.utils import get_databases
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
            "id",
            title=_("identifier"),
            key=True,
            extra="formatter:reportlink",
            hidden=True,
        ),
        GridFieldText(
            "name",
            title=_("name"),
            extra="formatter:reportlink",
            editable=False,
        ),
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
    default_sort = None

    @staticmethod
    def _filter_ne(reportrow, field, data):
        if isinstance(
            reportrow,
            (GridFieldCurrency, GridFieldInteger, GridFieldNumber),
        ):
            return ('"%s" is distinct from %%s' % field, [smart_str(data).strip()])
        elif isinstance(reportrow, GridFieldDateTime):
            return ('"%s" is distinct from %%s' % field, [parseLocalizedDateTime(data)])
        elif isinstance(reportrow, GridFieldDate):
            return ('"%s" is distinct from %%s' % field, [parseLocalizedDate(data)])
        else:
            return (
                'upper("%s"::text) is distinct from upper(%%s)' % field,
                [smart_str(data).strip()],
            )

    @staticmethod
    def _filter_bn(reportrow, field, data):
        return (
            'not upper("%s"::text) like upper(%%s)' % field,
            ["%s%%" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_en(reportrow, field, data):
        return (
            'not upper("%s"::text) like upper(%%s)' % field,
            ["%%%s" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_nc(reportrow, field, data):
        return (
            'not upper("%s"::text) like upper(%%s)' % field,
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
            (GridFieldCurrency, GridFieldInteger, GridFieldNumber),
        ):
            return ('"%s" = %%s' % field, [smart_str(data).strip()])
        elif isinstance(reportrow, GridFieldDateTime):
            return ('"%s" = %%s' % field, [parseLocalizedDateTime(data)])
        elif isinstance(reportrow, GridFieldDate):
            return ('"%s" = %%s' % field, [parseLocalizedDate(data)])
        else:
            return ('upper("%s"::text) = upper(%%s)' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_bw(reportrow, field, data):
        return (
            'upper("%s"::text) like upper(%%s)' % field,
            ["%s%%" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_gt(reportrow, field, data):
        if isinstance(reportrow, GridFieldDateTime):
            return ('"%s" > %%s' % field, [parseLocalizedDateTime(data)])
        elif isinstance(reportrow, GridFieldDate):
            return ('"%s" > %%s' % field, [parseLocalizedDate(data)])
        else:
            return ('"%s" > %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_gte(reportrow, field, data):
        if isinstance(reportrow, GridFieldDateTime):
            return ('"%s" >= %%s' % field, [parseLocalizedDateTime(data)])
        elif isinstance(reportrow, GridFieldDate):
            return ('"%s" >= %%s' % field, [parseLocalizedDate(data)])
        else:
            return ('"%s" >= %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_lt(reportrow, field, data):
        if isinstance(reportrow, GridFieldDateTime):
            return ('"%s" < %%s' % field, [parseLocalizedDateTime(data)])
        elif isinstance(reportrow, GridFieldDate):
            return ('"%s" < %%s' % field, [parseLocalizedDate(data)])
        else:
            return ('"%s" < %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_lte(reportrow, field, data):
        if isinstance(reportrow, GridFieldDateTime):
            return ('"%s" <= %%s' % field, [parseLocalizedDateTime(data)])
        elif isinstance(reportrow, GridFieldDate):
            return ('"%s" <= %%s' % field, [parseLocalizedDate(data)])
        else:
            return ('"%s" <= %%s' % field, [smart_str(data).strip()])

    @staticmethod
    def _filter_ew(reportrow, field, data):
        return (
            'upper("%s"::text) like upper(%%s)' % field,
            ["%%%s" % smart_str(data).strip()],
        )

    @staticmethod
    def _filter_cn(reportrow, field, data):
        return (
            'upper("%s"::text) like upper(%%s)' % field,
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
        # not implemented. Report manager has no hierarchy fields.
        return ""

    @staticmethod
    def _filter_isnull(reportrow, field, data):
        if data.lower() in ["0", "false", force_str(_("false"))]:
            return ('not "%s" is null' % field, [])
        else:
            return ('"%s" is null' % field, [])

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
        "isnull": _filter_isnull.__func__,
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

                    if user.is_superuser or (
                        request.database == scenario.name and cls.has_permission(user)
                    ):
                        scenario_permissions.append(
                            [
                                scenario.name,
                                (
                                    scenario.description
                                    if scenario.description
                                    else scenario.name
                                ),
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
        if not hasattr(request, "report"):
            request.report = (
                SQLReport.objects.all().using(request.database).get(pk=args[0])
            )
        if request.report and request.report.sql:
            with connections[
                (
                    request.database
                    if f"{request.database}_report" not in get_databases(True)
                    else f"{request.database}_report"
                )
            ].cursor() as cursor:
                if not hasattr(request, "filter"):
                    request.filter = cls.getFilter(request, *args, **kwargs)
                cursor.execute(
                    "select * from (%s) t_subquery %s %s %s %s"
                    % (
                        request.report.sql.replace("%", "%%"),
                        "where %s" % request.filter[0] if request.filter[0] else "",
                        (
                            f"order by {cls._apply_sort_index(request)}"
                            if request.GET.get("sidx", None)
                            or (request.prefs and "sidx" in request.prefs)
                            else ""
                        ),
                        (
                            ("offset %s" % ((page - 1) * request.pagesize + 1))
                            if page and page > 1
                            else ""
                        ),
                        (
                            "limit %s" % request.pagesize
                            if page
                            else (
                                "limit %s" % kwargs["report_download_limit"]
                                if "report_download_limit" in kwargs
                                else ""
                            )
                        ),
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

    @classmethod
    def count_query(cls, request, *args, **kwargs):
        # Query that returns the number of records in the report.
        # It implements filtering, but no paging or sorting.
        if not hasattr(request, "report"):
            request.report = (
                SQLReport.objects.all().using(request.database).get(pk=args[0])
            )
        if request.report and request.report.sql:

            with connections[
                (
                    request.database
                    if f"{request.database}_report" not in get_databases(True)
                    else f"{request.database}_report"
                )
            ].cursor() as cursor:

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
        else:
            return 0

    @classmethod
    def rows(cls, request, *args, **kwargs):
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
                not request.report.public
                and request.report.user
                and request.report.user.id != request.user.id
            ):
                return HttpResponseForbidden("You're not the owner of this report")
        else:
            request.report = None
            if not request.user.has_perm("reportmanager.add_sqlreport"):
                return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # restrict the download size
        fmt = request.GET.get("format", None)
        if fmt in (
            "spreadsheetlist",
            "spreadsheettable",
            "spreadsheet",
            "csvlist",
            "csvtable",
            "csv",
        ):
            kwargs["report_download_limit"] = int(
                Parameter.getValue("report_download_limit", request.database, None)
                or 20000
            )
        # Default logic
        return super().get(request, *args, **kwargs)

    @classmethod
    def extra_context(cls, request, *args, **kwargs):
        return {
            "title": (
                request.report.name
                if request.report
                else cls.title(request, *args, **kwargs)
            ),
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
                if m.user and not m.public and m.user.id != request.user.id:
                    return JsonResponse(
                        {
                            "id": m.id,
                            "status": force_str(
                                _("Private reports can only be edited by their owner")
                            ),
                        }
                    )
                elif (
                    m.user
                    and m.public
                    and m.user.id != request.user.id
                    and not request.user.is_superuser
                ):
                    return JsonResponse(
                        {
                            "id": m.id,
                            "status": force_str(
                                _(
                                    "Only superusers can edit public reports they don't own"
                                )
                            ),
                        }
                    )
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
                        {
                            "status": "Error: %s" % e,  # lgtm[py/stack-trace-exposure]
                        }
                    )
            else:
                return JsonResponse({"status": force_str(_("Error saving report"))})

        elif "delete" in request.POST:
            pk = request.POST["id"]
            m = SQLReport.objects.using(request.database).get(pk=request.POST["id"])
            if m.user and not m.public and m.user.id != request.user.id:
                return JsonResponse(
                    {
                        "id": m.id,
                        "status": force_str(
                            _("Private reports can only be edited by their owner")
                        ),
                    }
                )
            elif (
                m.user
                and m.public
                and m.user.id != request.user.id
                and not request.user.is_superuser
            ):
                return JsonResponse(
                    {
                        "id": m.id,
                        "status": force_str(
                            _(
                                "Only superusers can delete public reports they don't own"
                            )
                        ),
                    }
                )
            m.delete()
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
