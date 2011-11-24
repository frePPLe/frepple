#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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

import freppledb.input.views

urlpatterns = patterns('',

  # Model list reports, which override standard admin screens
  (r'^admin/input/buffer/$', freppledb.input.views.BufferList.as_view()),
  (r'^admin/input/resource/$', freppledb.input.views.ResourceList.as_view()),
  (r'^admin/input/location/$', freppledb.input.views.LocationList.as_view()),
  (r'^admin/input/customer/$', freppledb.input.views.CustomerList.as_view()),
  (r'^admin/input/demand/$', freppledb.input.views.DemandList.as_view()),
  (r'^admin/input/item/$', freppledb.input.views.ItemList.as_view()),
  (r'^admin/input/load/$', freppledb.input.views.LoadList.as_view()),
  (r'^admin/input/flow/$', freppledb.input.views.FlowList.as_view()),
  (r'^admin/input/forecast/$', freppledb.input.views.ForecastList.as_view()),
  (r'^admin/input/calendar/$', freppledb.input.views.CalendarList.as_view()),
  (r'^admin/input/operation/$', freppledb.input.views.OperationList.as_view()),
  (r'^admin/input/setupmatrix/$', freppledb.input.views.SetupMatrixList.as_view()),
  (r'^admin/input/suboperation/$', freppledb.input.views.SubOperationList.as_view()),
  (r'^admin/input/operationplan/$', freppledb.input.views.OperationPlanList.as_view()),
  (r'^admin/input/bucket/$', freppledb.input.views.BucketList.as_view()),
  (r'^admin/input/bucketdetail/$', freppledb.input.views.BucketDetailList.as_view()),
  (r'^admin/input/calendarbucket/$', freppledb.input.views.CalendarBucketList.as_view()),
  (r'^admin/input/parameter/$', freppledb.input.views.ParameterList.as_view()),

  # Special reports
  (r'^admin/input/calendar/location/([^/]+)/$', freppledb.input.views.location_calendar),
  (r'^supplypath/([^/]+)/([^/]+)/$', freppledb.input.views.pathreport.viewupstream),
  (r'^whereused/([^/]+)/([^/]+)/$', freppledb.input.views.pathreport.viewdownstream),
  (r'^edit/$', freppledb.input.views.uploadjson.post),  
)
