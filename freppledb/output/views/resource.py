#
# Copyright (C) 2007-2013 by frePPLe bv
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

from django.db import connections, transaction
from django.db.models.expressions import RawSQL
from django.utils.encoding import force_str
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from freppledb.boot import getAttributeFields
from freppledb.input.models import Resource, Location
from freppledb.common.models import Parameter
from freppledb.common.report import GridPivot, GridFieldCurrency, GridFieldDuration
from freppledb.common.report import GridFieldNumber, GridFieldText, GridFieldBool


class OverviewReport(GridPivot):
    """
    A report showing the loading of each resource.
    """

    template = "output/resource.html"
    title = _("Resource report")
    model = Resource
    permissions = (("view_resource_report", "Can view resource report"),)
    editable = False
    help_url = "user-interface/plan-analysis/resource-report.html"

    rows = (
        GridFieldText(
            "resource",
            title=_("resource"),
            key=True,
            editable=False,
            field_name="name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "description",
            title=_("description"),
            editable=False,
            field_name="description",
            initially_hidden=True,
        ),
        GridFieldText(
            "category",
            title=_("category"),
            editable=False,
            field_name="category",
            initially_hidden=True,
        ),
        GridFieldText(
            "subcategory",
            title=_("subcategory"),
            editable=False,
            field_name="subcategory",
            initially_hidden=True,
        ),
        GridFieldText(
            "type",
            title=_("type"),
            editable=False,
            field_name="type",
            initially_hidden=True,
        ),
        GridFieldBool(
            "constrained",
            title=_("constrained"),
            editable=False,
            field_name="constrained",
            initially_hidden=True,
        ),
        GridFieldNumber(
            "maximum",
            title=_("maximum"),
            editable=False,
            field_name="maximum",
            initially_hidden=True,
        ),
        GridFieldText(
            "maximum_calendar",
            title=_("maximum calendar"),
            editable=False,
            field_name="maximum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "cost",
            title=_("cost"),
            editable=False,
            field_name="cost",
            initially_hidden=True,
        ),
        GridFieldDuration(
            "maxearly",
            title=_("maxearly"),
            editable=False,
            field_name="maxearly",
            initially_hidden=True,
        ),
        GridFieldText(
            "setupmatrix",
            title=_("setupmatrix"),
            editable=False,
            field_name="setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
            initially_hidden=True,
        ),
        GridFieldText(
            "setup",
            title=_("setup"),
            editable=False,
            field_name="setup",
            initially_hidden=True,
        ),
        GridFieldText(
            "location__name",
            title=_("location"),
            editable=False,
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            editable=False,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
        GridFieldNumber(
            "avgutil",
            title=_("utilization %"),
            formatter="percentage",
            editable=False,
            width=100,
            align="center",
        ),
        GridFieldText(
            "available_calendar",
            title=_("available calendar"),
            editable=False,
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            editable=False,
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
    )
    crosses = (
        ("available", {"title": _("available")}),
        ("unavailable", {"title": _("unavailable"), "initially_hidden": True}),
        ("setuptime", {"title": _("setup"), "initially_hidden": True}),
        ("load", {"title": _("load")}),
        ("utilization", {"title": _("utilization %")}),
    )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom resource attributes
            for f in getAttributeFields(Resource, initially_hidden=True):
                f.editable = False
                reportclass.rows += (f,)
                if f.formatter == "detail":
                    reportclass.attr_sql += f"res.{ f.field_name.split("__")[0] }_id, "
                else:
                    reportclass.attr_sql += f"res.{ f.field_name.split("__")[-1] }, "
            # Adding custom location attributes
            for f in getAttributeFields(
                Location, related_name_prefix="location", initially_hidden=True
            ):
                f.editable = False
                reportclass.rows += (f,)
                reportclass.attr_sql += "location.%s, " % f.name.split("__")[-1]

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plan"
            return {
                "units": reportclass.getUnits(request),
                "title": force_str(Resource._meta.verbose_name) + " " + args[0],
                "post_title": _("plan"),
                "model": Resource,
            }
        else:
            return {"units": reportclass.getUnits(request)}

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            queryset = Resource.objects.filter(name=args[0])
        else:
            queryset = Resource.objects.all()
        return queryset.annotate(
            avgutil=RawSQL(
                """
          select ( coalesce(sum(out_resourceplan.load),0) + coalesce(sum(out_resourceplan.setup),0) )
             * 100.0 / coalesce(greatest(sum(out_resourceplan.available), 0.0001),1) as avg_util
          from out_resourceplan
          where out_resourceplan.startdate >= %s
          and out_resourceplan.startdate < %s
          and out_resourceplan.resource = resource.name
          """,
                (request.report_startdate, request.report_enddate),
            )
        )

    @classmethod
    def getUnits(reportclass, request):
        try:
            units = Parameter.objects.using(request.database).get(
                name="loading_time_units"
            )
            if units.value == "hours":
                return (1.0, _("hours"))
            elif units.value == "weeks":
                return (168, _("weeks"))
            else:
                return (24, _("days"))
        except Exception:
            return (24, _("days"))

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Get the time units
        units = OverviewReport.getUnits(request)

        # Assure the item hierarchy is up to date
        Resource.rebuildHierarchy(database=basequery.db)

        # Execute the query
        query = """
      select res.name, res.description, res.category, res.subcategory,
        res.type, res.constrained, res.maximum, res.maximum_calendar_id,
        res.cost, res.maxearly, res.setupmatrix_id, res.setup, location.name,
        location.description, location.category, location.subcategory,
        location.available_id, res.avgutil, res.available_id available_calendar,
        res.owner_id,
        %s
        d.bucket as col1, d.startdate as col2,
        coalesce(sum(out_resourceplan.available),0) / (case when res.type = 'buckets' then 1 else %f end) as available,
        coalesce(sum(out_resourceplan.unavailable),0) / (case when res.type = 'buckets' then 1 else %f end) as unavailable,
        coalesce(sum(out_resourceplan.load),0) / (case when res.type = 'buckets' then 1 else %f end) as loading,
        coalesce(sum(out_resourceplan.setup),0) / (case when res.type = 'buckets' then 1 else %f end) as setup
      from (%s) res
      left outer join location
        on res.location_id = location.name
      -- Multiply with buckets
      cross join (
                   select name as bucket, startdate, enddate
                   from common_bucketdetail
                   where bucket_id = '%s' and enddate > '%s' and startdate < '%s'
                   ) d
      -- Utilization info
      left join out_resourceplan
      on res.name = out_resourceplan.resource
      and d.startdate <= out_resourceplan.startdate
      and d.enddate > out_resourceplan.startdate
      and out_resourceplan.startdate >= '%s'
      and out_resourceplan.startdate < '%s'
      -- Grouping and sorting
      group by res.name, res.description, res.category, res.subcategory,
        res.type, res.maximum, res.maximum_calendar_id, res.available_id, res.cost, res.maxearly,
        res.setupmatrix_id, res.setup, location.name, location.description,
        location.category, location.subcategory, location.available_id, res.avgutil, res.owner_id,
        res.constrained,
        %s d.bucket, d.startdate
      order by %s, d.startdate
      """ % (
            reportclass.attr_sql,
            units[0],
            units[0],
            units[0],
            units[0],
            basesql,
            request.report_bucket,
            request.report_startdate,
            request.report_enddate,
            request.report_startdate,
            request.report_enddate,
            reportclass.attr_sql,
            sortsql,
        )

        # Build the python result
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(query, baseparams)
                resourceattributefields = getAttributeFields(Resource)
                locationattributefields = getAttributeFields(Location)
                for row in cursor_chunked:
                    numfields = len(row)
                    if row[numfields - 4] != 0:
                        util = round(row[numfields - 2] * 100 / row[numfields - 4], 2)
                    else:
                        util = 0
                    result = {
                        "resource": row[0],
                        "description": row[1],
                        "category": row[2],
                        "subcategory": row[3],
                        "type": row[4],
                        "constrained": row[5],
                        "maximum": row[6],
                        "maximum_calendar": row[7],
                        "cost": row[8],
                        "maxearly": row[9],
                        "setupmatrix": row[10],
                        "setup": row[11],
                        "location__name": row[12],
                        "location__description": row[13],
                        "location__category": row[14],
                        "location__subcategory": row[15],
                        "location__available": row[16],
                        "avgutil": round(row[17], 2),
                        "available_calendar": row[18],
                        "owner": row[19],
                        "bucket": row[numfields - 6],
                        "startdate": row[numfields - 5],
                        "available": row[numfields - 4],
                        "unavailable": row[numfields - 3],
                        "load": row[numfields - 2],
                        "setuptime": row[numfields - 1],
                        "utilization": util,
                    }
                    idx = 20
                    for f in resourceattributefields:
                        result[f.name] = row[idx]
                        idx += 1
                    for f in locationattributefields:
                        result[f.field_name] = row[idx]
                        idx += 1
                    yield result
