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

import freppledb.input.views

urlpatterns = patterns('',

  # Model list reports, which override standard admin screens
  (r'^admin/input/buffer/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.BufferList,}),
  (r'^admin/input/resource/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.ResourceList,}),
  (r'^admin/input/location/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.LocationList,}),
  (r'^admin/input/customer/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.CustomerList,}),
  (r'^admin/input/demand/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.DemandList,}),
  (r'^admin/input/item/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.ItemList,}),
  (r'^admin/input/load/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.LoadList,}),
  (r'^admin/input/flow/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.FlowList,}),
  (r'^admin/input/forecast/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.ForecastList,}),
  (r'^admin/input/calendar/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.CalendarList,}),
  (r'^admin/input/operation/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.OperationList,}),
  (r'^admin/input/setupmatrix/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.SetupMatrixList,}),
  (r'^admin/input/suboperation/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.SubOperationList,}),
  (r'^admin/input/operationplan/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.OperationPlanList,}),
  (r'^admin/input/dates/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.DatesList,}),
  (r'^admin/input/parameter/$', 'freppledb.common.report.view_report',
    {'report': freppledb.input.views.ParameterList,}),

  # Special reports
  (r'^admin/input/calendar/location/([^/]+)/$', freppledb.input.views.location_calendar),
  (r'^supplypath/([^/]+)/([^/]+)/$', freppledb.input.views.pathreport.viewupstream),
  (r'^whereused/([^/]+)/([^/]+)/$', freppledb.input.views.pathreport.viewdownstream),
  (r'^edit/$', freppledb.input.views.uploadjson.post),
)
