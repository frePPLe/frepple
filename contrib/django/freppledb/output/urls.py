#
# Copyright (C) 2007-2010 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.conf.urls.defaults import patterns

import freppledb.output.views.buffer
import freppledb.output.views.demand
import freppledb.output.views.problem
import freppledb.output.views.constraint
import freppledb.output.views.forecast
import freppledb.output.views.resource
import freppledb.output.views.operation
import freppledb.output.views.pegging
import freppledb.output.views.kpi


urlpatterns = patterns('',
    (r'^buffer/([^/]+)/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.buffer.OverviewReport,}),
    (r'^buffergraph/([^/]+)/$', 'freppledb.output.views.buffer.GraphData'),
    (r'^buffer/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.buffer.OverviewReport,}),
    (r'^demand/([^/]+)/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.demand.OverviewReport,}),
    (r'^demandgraph/([^/]+)/$', 'freppledb.output.views.demand.GraphData'),
    (r'^demand/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.demand.OverviewReport,}),
    (r'^resource/([^/]+)/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.resource.OverviewReport,}),
    (r'^resourcegraph/([^/]+)/$', 'freppledb.output.views.resource.GraphData'),
    (r'^resource/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.resource.OverviewReport,}),
    (r'^operation/([^/]+)/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.operation.OverviewReport,}),
    (r'^operationgraph/([^/]+)/$', 'freppledb.output.views.operation.GraphData'),
    (r'^operation/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.operation.OverviewReport,}),
    (r'^forecast/([^/]+)/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.forecast.OverviewReport,}),
    (r'^forecastgraph/([^/]+)/$', 'freppledb.output.views.forecast.GraphData'),
    (r'^forecast/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.forecast.OverviewReport,}),
    (r'^demandpegging/([^/]+)/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.pegging.ReportByDemand,}),
    (r'^pegginggraph/([^/]+)/$', 'freppledb.output.views.pegging.GraphData'),
    (r'^bufferpegging/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.pegging.ReportByBuffer,}),
    (r'^resourcepegging/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.pegging.ReportByResource,}),
    (r'^operationpegging/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.pegging.ReportByOperation,}),
    (r'^flowplan/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.buffer.DetailReport,}),
    (r'^problem/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.problem.Report,}),
    (r'^constraint/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.constraint.Report,}),
    (r'^operationplan/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.operation.DetailReport,}),
    (r'^loadplan/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.resource.DetailReport,}),
    (r'^demandplan/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.demand.DetailReport,}),
    (r'^kpi/$', 'freppledb.common.report.view_report',
      {'report': freppledb.output.views.kpi.Report,}),
)
