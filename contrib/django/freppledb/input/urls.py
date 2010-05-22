#
# Copyright (C) 2007-2010 by Johan De Taeye
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

from django.conf.urls.defaults import *

import input.views

urlpatterns = patterns('',

  # Model list reports, which override standard admin screens
  (r'^admin/input/buffer/$', 'common.report.view_report',
    {'report': input.views.BufferList,}),
  (r'^admin/input/resource/$', 'common.report.view_report',
    {'report': input.views.ResourceList,}),
  (r'^admin/input/location/$', 'common.report.view_report',
    {'report': input.views.LocationList,}),
  (r'^admin/input/customer/$', 'common.report.view_report',
    {'report': input.views.CustomerList,}),
  (r'^admin/input/demand/$', 'common.report.view_report',
    {'report': input.views.DemandList,}),
  (r'^admin/input/item/$', 'common.report.view_report',
    {'report': input.views.ItemList,}),
  (r'^admin/input/load/$', 'common.report.view_report',
    {'report': input.views.LoadList,}),
  (r'^admin/input/flow/$', 'common.report.view_report',
    {'report': input.views.FlowList,}),
  (r'^admin/input/forecast/$', 'common.report.view_report',
    {'report': input.views.ForecastList,}),
  (r'^admin/input/calendar/$', 'common.report.view_report',
    {'report': input.views.CalendarList,}),
  (r'^admin/input/operation/$', 'common.report.view_report',
    {'report': input.views.OperationList,}),
  (r'^admin/input/setupmatrix/$', 'common.report.view_report',
    {'report': input.views.SetupMatrixList,}),
  (r'^admin/input/suboperation/$', 'common.report.view_report',
    {'report': input.views.SubOperationList,}),
  (r'^admin/input/operationplan/$', 'common.report.view_report',
    {'report': input.views.OperationPlanList,}),
  (r'^admin/input/dates/$', 'common.report.view_report',
    {'report': input.views.DatesList,}),
  (r'^admin/input/parameter/$', 'common.report.view_report',
    {'report': input.views.ParameterList,}),

  # Special reports
  (r'^admin/input/calendar/location/([^/]+)/$', 'input.views.location_calendar'),
  (r'^supplypath/([^/]+)/([^/]+)/$', input.views.pathreport.viewupstream),
  (r'^whereused/([^/]+)/([^/]+)/$', input.views.pathreport.viewdownstream),
  (r'^edit/$', input.views.uploadjson.post),
)
