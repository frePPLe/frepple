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

from django.urls import path, re_path

from freppledb import mode

# Automatically add these URLs when the application is installed
autodiscover = True

if mode == "WSGI":
    import freppledb.output.views.buffer
    import freppledb.output.views.demand
    import freppledb.output.views.problem
    import freppledb.output.views.constraint
    import freppledb.output.views.resource
    import freppledb.output.views.operation
    import freppledb.output.views.pegging

    urlpatterns = [
        re_path(
            r"^buffer/item/(.+)/$",
            freppledb.output.views.buffer.OverviewReport.as_view(),
            name="output_buffer_plandetail_by_item",
        ),
        re_path(
            r"^buffer/(.+)/$",
            freppledb.output.views.buffer.OverviewReport.as_view(),
            name="output_buffer_plandetail",
        ),
        path(
            "buffer/",
            freppledb.output.views.buffer.OverviewReport.as_view(),
            name="output_buffer_plan",
        ),
        path(
            "demand/operationplans/",
            freppledb.output.views.demand.OperationPlans,
            name="output_demand_operationplans",
        ),
        path(
            "demand/",
            freppledb.output.views.demand.OverviewReport.as_view(),
            name="output_demand_plan",
        ),
        re_path(
            r"^resource/(.+)/$",
            freppledb.output.views.resource.OverviewReport.as_view(),
            name="output_resource_plandetail",
        ),
        path(
            "resource/",
            freppledb.output.views.resource.OverviewReport.as_view(),
            name="output_resource_plan",
        ),
        re_path(
            r"^operation/(.+)/$",
            freppledb.output.views.operation.OverviewReport.as_view(),
            name="output_operation_plandetail",
        ),
        path(
            "operation/",
            freppledb.output.views.operation.OverviewReport.as_view(),
            name="output_operation_plan",
        ),
        path(
            "purchase/",
            freppledb.output.views.operation.PurchaseReport.as_view(),
            name="output_purchase",
        ),
        path(
            "distribution/",
            freppledb.output.views.operation.DistributionReport.as_view(),
            name="output_distribution",
        ),
        re_path(
            r"^demandpegging/(.+)/$",
            freppledb.output.views.pegging.ReportByDemand.as_view(),
            name="output_demand_pegging",
        ),
        path(
            "problem/",
            freppledb.output.views.problem.Report.as_view(),
            name="output_problem",
        ),
        path(
            "constraint/",
            freppledb.output.views.constraint.BaseReport.as_view(),
            name="output_constraint",
        ),
        re_path(
            r"^constraintoperation/(.+)/$",
            freppledb.output.views.constraint.ReportByOperation.as_view(),
            name="output_constraint_operation",
        ),
        re_path(
            r"^constraintdemand/(.+)/$",
            freppledb.output.views.constraint.ReportByDemand.as_view(),
            name="output_constraint_demand",
        ),
        re_path(
            r"^constraintbuffer/(.+)/$",
            freppledb.output.views.constraint.ReportByBuffer.as_view(),
            name="output_constraint_buffer",
        ),
        re_path(
            r"^constraintresource/(.+)/$",
            freppledb.output.views.constraint.ReportByResource.as_view(),
            name="output_constraint_resource",
        ),
    ]
