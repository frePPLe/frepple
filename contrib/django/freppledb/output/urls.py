#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

from django.conf.urls import patterns

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

urlpatterns = patterns('',
    (r'^buffer/(.+)/$', freppledb.output.views.buffer.OverviewReport.as_view()),
    (r'^buffer/$', freppledb.output.views.buffer.OverviewReport.as_view()),
    (r'^demand/(.+)/$', freppledb.output.views.demand.OverviewReport.as_view()),
    (r'^demand/$',  freppledb.output.views.demand.OverviewReport.as_view()),
    (r'^resource/(.+)/$', freppledb.output.views.resource.OverviewReport.as_view()),
    (r'^resource/$', freppledb.output.views.resource.OverviewReport.as_view()),
    (r'^operation/([^.]+)/$', freppledb.output.views.operation.OverviewReport.as_view()),
    (r'^operation/$',  freppledb.output.views.operation.OverviewReport.as_view()),
    (r'^demandpegging/(.+)/$', freppledb.output.views.pegging.ReportByDemand.as_view()),
    (r'^bufferpegging/$', freppledb.output.views.pegging.ReportByBuffer.as_view()),
    (r'^resourcepegging/$', freppledb.output.views.pegging.ReportByResource.as_view()),
    (r'^operationpegging/$',  freppledb.output.views.pegging.ReportByOperation.as_view()),
    (r'^flowplan/(.+)/$', freppledb.output.views.buffer.DetailReport.as_view()),
    (r'^flowplan/$', freppledb.output.views.buffer.DetailReport.as_view()),
    (r'^problem/$', freppledb.output.views.problem.Report.as_view()),
    (r'^constraint/$', freppledb.output.views.constraint.BaseReport.as_view()),
    (r'^constraintdemand/(.+)/$', freppledb.output.views.constraint.ReportByDemand.as_view()),
    (r'^constraintbuffer/(.+)/$', freppledb.output.views.constraint.ReportByBuffer.as_view()),
    (r'^constraintresource/(.+)/$', freppledb.output.views.constraint.ReportByResource.as_view()),
    (r'^operationplan/(.+)/$', freppledb.output.views.operation.DetailReport.as_view()),
    (r'^operationplan/$', freppledb.output.views.operation.DetailReport.as_view()),
    (r'^loadplan/(.+)/$', freppledb.output.views.resource.DetailReport.as_view()),
    (r'^loadplan/$', freppledb.output.views.resource.DetailReport.as_view()),
    (r'^demandplan/(.+)/$', freppledb.output.views.demand.DetailReport.as_view()),
    (r'^demandplan/$', freppledb.output.views.demand.DetailReport.as_view()),
    (r'^kpi/$', freppledb.output.views.kpi.Report.as_view()),
)
