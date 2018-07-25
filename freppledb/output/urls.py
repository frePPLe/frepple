#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from django.conf.urls import url

import freppledb.output.views.buffer
import freppledb.output.views.demand
import freppledb.output.views.problem
import freppledb.output.views.constraint
import freppledb.output.views.resource
import freppledb.output.views.operation
import freppledb.output.views.pegging
import freppledb.output.views.kpi

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [

  url(r'^buffer/(.+)/$', freppledb.output.views.buffer.OverviewReport.as_view(), name="output_buffer_plandetail"),
  url(r'^buffer/$', freppledb.output.views.buffer.OverviewReport.as_view(), name="output_buffer_plan"),
  url(r'^demand/operationplans/$', freppledb.output.views.demand.OperationPlans, name="output_demand_operationplans"),
  url(r'^demand/(.+)/$', freppledb.output.views.demand.OverviewReport.as_view(), name="output_demand_plandetail"),
  url(r'^demand/$', freppledb.output.views.demand.OverviewReport.as_view(), name="output_demand_plan"),
  url(r'^resource/(.+)/$', freppledb.output.views.resource.OverviewReport.as_view(), name="output_resource_plandetail"),
  url(r'^resource/$', freppledb.output.views.resource.OverviewReport.as_view(), name="output_resource_plan"),
  url(r'^operation/(.+)/$', freppledb.output.views.operation.OverviewReport.as_view(), name="output_operation_plandetail"),
  url(r'^operation/$', freppledb.output.views.operation.OverviewReport.as_view(), name="output_operation_plan"),
  url(r'^purchase/$', freppledb.output.views.operation.PurchaseReport.as_view(), name="output_purchase"),
  url(r'^distribution/$', freppledb.output.views.operation.DistributionReport.as_view(), name="output_distribution"),
  url(r'^demandpegging/(.+)/$', freppledb.output.views.pegging.ReportByDemand.as_view(), name="output_demand_pegging"),
  url(r'^flowplan/(.+)/$', freppledb.output.views.buffer.DetailReport.as_view(), name="output_flowplan_plandetail"),
  url(r'^flowplan/$', freppledb.output.views.buffer.DetailReport.as_view(), name="output_flowplan_plan"),
  url(r'^problem/$', freppledb.output.views.problem.Report.as_view(), name="output_problem"),
  url(r'^constraint/$', freppledb.output.views.constraint.BaseReport.as_view(), name="output_constraint"),
  url(r'^constraintoperation/(.+)/$', freppledb.output.views.constraint.ReportByOperation.as_view(), name="output_constraint_operation"),
  url(r'^constraintdemand/(.+)/$', freppledb.output.views.constraint.ReportByDemand.as_view(), name="output_constraint_demand"),
  url(r'^constraintbuffer/(.+)/$', freppledb.output.views.constraint.ReportByBuffer.as_view(), name="output_constraint_buffer"),
  url(r'^constraintresource/(.+)/$', freppledb.output.views.constraint.ReportByResource.as_view(), name="output_constraint_resource"),
  url(r'^loadplan/(.+)/$', freppledb.output.views.resource.DetailReport.as_view(), name="output_loadplan_plandetail"),
  url(r'^loadplan/$', freppledb.output.views.resource.DetailReport.as_view(), name="output_loadplan_plan"),
  url(r'^kpi/$', freppledb.output.views.kpi.Report.as_view(), name="output_kpi"),

  ]
