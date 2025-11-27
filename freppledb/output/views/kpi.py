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

from django.utils.translation import gettext_lazy as _
from django.db import connections

from freppledb.common.models import Parameter
from freppledb.common.report import GridReport, GridFieldText, GridFieldInteger


class Report(GridReport):
    title = _("Performance Indicators")
    frozenColumns = 0
    basequeryset = Parameter.objects.all()
    permissions = (("view_kpi_report", "Can view kpi report"),)
    rows = (
        GridFieldText(
            "category",
            title=_("category"),
            sortable=False,
            editable=False,
            align="center",
        ),
        GridFieldText(
            "name", title=_("name"), sortable=False, editable=False, align="center"
        ),
        GridFieldInteger(
            "value", title=_("value"), sortable=False, editable=False, align="center"
        ),
    )
    default_sort = (1, "asc")
    filterable = False
    multiselect = False
    help_url = "user-interface/plan-analysis/performance-indicator-report.html"

    @staticmethod
    def query(request, basequery):
        # Execute the query
        cursor = connections[request.database].cursor()
        cursor.execute(
            """
            select 101 as id, 'Problem count' as category, name as name, count(*) as value
            from out_problem
            group by name
            -- union all
            -- select 102, 'Problem weight', name, round(sum(weight))
            -- from out_problem
            -- group by name
            union all
            select 201, 'Demand', 'Requested', coalesce(round(sum(quantity)),0)
            from demand
            where status in ('open', 'quote')
            union all
            select 202, 'Demand', 'Planned', coalesce(round(sum(quantity)),0)
            from operationplan
            where demand_id is not null and owner_id is null
            union all
            select 203, 'Demand', 'Planned late', coalesce(round(sum(quantity)),0)
            from operationplan
            where enddate > due and demand_id is not null and owner_id is null
            union all
            select 204, 'Demand', 'Planned on time', coalesce(round(sum(quantity)),0)
            from operationplan
            where enddate <= due and demand_id is not null and owner_id is null
            -- union all
            -- select 205, 'Demand', 'Unplanned', coalesce(round(sum(weight)),0)
            -- from out_problem
            -- where name = 'unplanned'
            union all
            select 206, 'Demand', 'Total lateness', coalesce(round(sum(quantity * extract(epoch from enddate - due)) / 86400),0)
            from operationplan
            where enddate > due and demand_id is not null and owner_id is null
            union all
            select 301, 'Operation', 'Count', count(*)
            from operationplan
            union all
            select 301, 'Operation', 'Quantity', coalesce(round(sum(quantity)),0)
            from operationplan
            union all
            select 302, 'Resource', 'Usage', coalesce(round(sum(operationplanresource.quantity * extract(epoch from operationplan.enddate - operationplan.startdate)) / 86400),0)
            from operationplanresource
            inner join operationplan on operationplanresource.operationplan_id = operationplan.reference
            union all
            select 401, 'Material', 'Produced', coalesce(round(sum(quantity)),0)
            from operationplanmaterial
            where quantity>0
            union all
            select 402, 'Material', 'Consumed', coalesce(round(sum(-quantity)),0)
            from operationplanmaterial
            where quantity<0
            order by 1
            """
        )

        # Build the python result
        for row in cursor.fetchall():
            yield {"category": row[1], "name": row[2], "value": row[3]}
