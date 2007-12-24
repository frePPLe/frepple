#
# Copyright (C) 2007 by Johan De Taeye
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
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.conf.urls.defaults import *

import output.views.buffer
import output.views.demand
import output.views.problem
import output.views.forecast
import output.views.resource
import output.views.operation
import output.views.pegging
import output.views.kpi


urlpatterns = patterns('',
    (r'^buffer/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.buffer.OverviewReport,}),
    (r'^buffer/$', 'utils.report.view_report',
      {'report': output.views.buffer.OverviewReport,}),
    (r'^demand/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.demand.OverviewReport,}),
    (r'^demand/$', 'utils.report.view_report',
      {'report': output.views.demand.OverviewReport,}),
    (r'^resource/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.resource.OverviewReport,}),
    (r'^resource/$', 'utils.report.view_report',
      {'report': output.views.resource.OverviewReport,}),
    (r'^operation/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.operation.OverviewReport,}),
    (r'^operation/$', 'utils.report.view_report',
      {'report': output.views.operation.OverviewReport,}),
    (r'^forecast/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.forecast.OverviewReport,}),
    (r'^forecast/$', 'utils.report.view_report',
      {'report': output.views.forecast.OverviewReport,}),
    (r'^pegging/$', 'utils.report.view_report',
      {'report': output.views.pegging.Report,}),
    (r'^flowplan/$', 'utils.report.view_report',
      {'report': output.views.buffer.DetailReport,}),
    (r'^problem/$', 'utils.report.view_report',
      {'report': output.views.problem.Report,}),
    (r'^operationplan/$', 'utils.report.view_report',
      {'report': output.views.operation.DetailReport,}),
    (r'^loadplan/$', 'utils.report.view_report',
      {'report': output.views.resource.DetailReport,}),
    (r'^demandplan/$', 'utils.report.view_report',
      {'report': output.views.demand.DetailReport,}),
    (r'^kpi/$', 'utils.report.view_report',
      {'report': output.views.kpi.Report,}),
)