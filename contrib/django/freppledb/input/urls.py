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

import input.views

urlpatterns = patterns('',

  # Plan report: no list, but redirect to edit page of plan
  ('^admin/input/plan/$', 'django.views.generic.simple.redirect_to',
    {'url': '/admin/input/plan/1/'}),

  # Model list reports, which override standard admin screens
  (r'^admin/input/buffer/$', 'utils.report.view_report',
    {'report': input.views.BufferList,}),
  (r'^admin/input/resource/$', 'utils.report.view_report',
    {'report': input.views.ResourceList,}),
  (r'^admin/input/location/$', 'utils.report.view_report',
    {'report': input.views.LocationList,}),
  (r'^admin/input/customer/$', 'utils.report.view_report',
    {'report': input.views.CustomerList,}),
  (r'^admin/input/demand/$', 'utils.report.view_report',
    {'report': input.views.DemandList,}),
  (r'^admin/input/item/$', 'utils.report.view_report',
    {'report': input.views.ItemList,}),
  (r'^admin/input/load/$', 'utils.report.view_report',
    {'report': input.views.LoadList,}),
  (r'^admin/input/flow/$', 'utils.report.view_report',
    {'report': input.views.FlowList,}),
  (r'^admin/input/forecast/$', 'utils.report.view_report',
    {'report': input.views.ForecastList,}),
  (r'^admin/input/dates/$', 'utils.report.view_report',
    {'report': input.views.DatesList,}),
  (r'^admin/input/calendar/$', 'utils.report.view_report',
    {'report': input.views.CalendarList,}),
  (r'^admin/input/operation/$', 'utils.report.view_report',
    {'report': input.views.OperationList,}),
  (r'^admin/input/suboperation/$', 'utils.report.view_report',
    {'report': input.views.SubOperationList,}),
  (r'^admin/input/operationplan/$', 'utils.report.view_report',
    {'report': input.views.OperationPlanList,}),

  # Special reports
  (r'^supplypath/([^/]+)/([^/]+)/$', input.views.pathreport.viewupstream),
  (r'^whereused/([^/]+)/([^/]+)/$', input.views.pathreport.viewdownstream),
  (r'^edit/$', input.views.uploadjson.post),
)
