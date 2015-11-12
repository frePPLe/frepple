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

from django.conf.urls import patterns

import freppledb.input.views
import freppledb.input.serializers

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = patterns(
  '',  # Prefix

  # Model list reports, which override standard admin screens
  (r'^data/input/buffer/$', freppledb.input.views.BufferList.as_view()),
  (r'^data/input/resource/$', freppledb.input.views.ResourceList.as_view()),
  (r'^data/input/location/$', freppledb.input.views.LocationList.as_view()),
  (r'^data/input/customer/$', freppledb.input.views.CustomerList.as_view()),
  (r'^data/input/demand/$', freppledb.input.views.DemandList.as_view()),
  (r'^data/input/item/$', freppledb.input.views.ItemList.as_view()),
  (r'^data/input/load/$', freppledb.input.views.LoadList.as_view()),
  (r'^data/input/flow/$', freppledb.input.views.FlowList.as_view()),
  (r'^data/input/calendar/$', freppledb.input.views.CalendarList.as_view()),
  (r'^data/input/calendarbucket/$', freppledb.input.views.CalendarBucketList.as_view()),
  (r'^data/input/operation/$', freppledb.input.views.OperationList.as_view()),
  (r'^data/input/setupmatrix/$', freppledb.input.views.SetupMatrixList.as_view()),
  (r'^data/input/suboperation/$', freppledb.input.views.SubOperationList.as_view()),
  (r'^data/input/operationplan/$', freppledb.input.views.OperationPlanList.as_view()),
  (r'^data/input/purchaseorder/$', freppledb.input.views.PurchaseOrderList.as_view()),
  (r'^data/input/distributionorder/$', freppledb.input.views.DistributionOrderList.as_view()),
  (r'^data/input/skill/$', freppledb.input.views.SkillList.as_view()),
  (r'^data/input/resourceskill/$', freppledb.input.views.ResourceSkillList.as_view()),
  (r'^data/input/supplier/$', freppledb.input.views.SupplierList.as_view()),
  (r'^data/input/itemsupplier/$', freppledb.input.views.ItemSupplierList.as_view()),
  (r'^data/input/itemdistribution/$', freppledb.input.views.ItemDistributionList.as_view()),

  # Special reports
  (r'^supplypath/item/(.+)/$', freppledb.input.views.UpstreamItemPath.as_view()),
  (r'^whereused/item/(.+)/$', freppledb.input.views.DownstreamItemPath.as_view()),
  (r'^supplypath/buffer/(.+)/$', freppledb.input.views.UpstreamBufferPath.as_view()),
  (r'^whereused/buffer/(.+)/$', freppledb.input.views.DownstreamBufferPath.as_view()),
  (r'^supplypath/resource/(.+)/$', freppledb.input.views.UpstreamResourcePath.as_view()),
  (r'^supplypath/demand/(.+)/$', freppledb.input.views.UpstreamDemandPath.as_view()),
  (r'^whereused/resource/(.+)/$', freppledb.input.views.DownstreamResourcePath.as_view()),
  (r'^supplypath/operation/(.+)/$', freppledb.input.views.UpstreamOperationPath.as_view()),
  (r'^whereused/operation/(.+)/$', freppledb.input.views.DownstreamOperationPath.as_view()),
  (r'^search/$', freppledb.input.views.search),

  # REST API framework
  (r'^api/input/buffer/$', freppledb.input.serializers.BufferAPI.as_view()),
  (r'^api/input/resource/$', freppledb.input.serializers.ResourceAPI.as_view()),
  (r'^api/input/location/$', freppledb.input.serializers.LocationAPI.as_view()),
  (r'^api/input/customer/$', freppledb.input.serializers.CustomerAPI.as_view()),
  (r'^api/input/demand/$', freppledb.input.serializers.DemandAPI.as_view()),
  (r'^api/input/item/$', freppledb.input.serializers.ItemAPI.as_view()),
  (r'^api/input/load/$', freppledb.input.serializers.LoadAPI.as_view()),
  (r'^api/input/flow/$', freppledb.input.serializers.FlowAPI.as_view()),
  (r'^api/input/calendar/$', freppledb.input.serializers.CalendarAPI.as_view()),
  (r'^api/input/calendarbucket/$', freppledb.input.serializers.CalendarBucketAPI.as_view()),
  (r'^api/input/operation/$', freppledb.input.serializers.OperationAPI.as_view()),
  (r'^api/input/setupmatrix/$', freppledb.input.serializers.SetupMatrixAPI.as_view()),
  (r'^api/input/setuprule/$', freppledb.input.serializers.SetupRuleAPI.as_view()),
  (r'^api/input/suboperation/$', freppledb.input.serializers.SubOperationAPI.as_view()),
  (r'^api/input/operationplan/$', freppledb.input.serializers.OperationPlanAPI.as_view()),
  (r'^api/input/purchaseorder/$', freppledb.input.serializers.PurchaseOrderAPI.as_view()),
  (r'^api/input/distributionorder/$', freppledb.input.serializers.DistributionOrderAPI.as_view()),
  (r'^api/input/skill/$', freppledb.input.serializers.SkillAPI.as_view()),
  (r'^api/input/resourceskill/$', freppledb.input.serializers.ResourceSkillAPI.as_view()),
  (r'^api/input/supplier/$', freppledb.input.serializers.SupplierAPI.as_view()),
  (r'^api/input/itemsupplier/$', freppledb.input.serializers.ItemSupplierAPI.as_view()),
  (r'^api/input/itemdistribution/$', freppledb.input.serializers.ItemDistributionAPI.as_view()),

  (r'^api/input/buffer/(?P<pk>(.+))/$', freppledb.input.serializers.BufferdetailAPI.as_view()),
  (r'^api/input/resource/(?P<pk>(.+))/$', freppledb.input.serializers.ResourcedetailAPI.as_view()),
  (r'^api/input/location/(?P<pk>(.+))/$', freppledb.input.serializers.LocationdetailAPI.as_view()),
  (r'^api/input/customer/(?P<pk>(.+))/$', freppledb.input.serializers.CustomerdetailAPI.as_view()),
  (r'^api/input/demand/(?P<pk>(.+))/$', freppledb.input.serializers.DemanddetailAPI.as_view()),
  (r'^api/input/item/(?P<pk>(.+))/$', freppledb.input.serializers.ItemdetailAPI.as_view()),
  (r'^api/input/load/(?P<pk>(.+))/$', freppledb.input.serializers.LoaddetailAPI.as_view()),
  (r'^api/input/flow/(?P<pk>(.+))/$', freppledb.input.serializers.FlowdetailAPI.as_view()),
  (r'^api/input/calendar/(?P<pk>(.+))/$', freppledb.input.serializers.CalendardetailAPI.as_view()),
  (r'^api/input/calendarbucket/(?P<pk>(.+))/$', freppledb.input.serializers.CalendarBucketdetailAPI.as_view()),
  (r'^api/input/operation/(?P<pk>(.+))/$', freppledb.input.serializers.OperationdetailAPI.as_view()),
  (r'^api/input/setupmatrix/(?P<pk>(.+))/$', freppledb.input.serializers.SetupMatrixdetailAPI.as_view()),
  (r'^api/input/setuprule/(?P<pk>(.+))/$', freppledb.input.serializers.SetupRuledetailAPI.as_view()),
  (r'^api/input/suboperation/(?P<pk>(.+))/$', freppledb.input.serializers.SubOperationdetailAPI.as_view()),
  (r'^api/input/operationplan/(?P<pk>(.+))/$', freppledb.input.serializers.OperationPlandetailAPI.as_view()),
  (r'^api/input/purchaseorder/(?P<pk>(.+))/$', freppledb.input.serializers.PurchaseOrderdetailAPI.as_view()),
  (r'^api/input/distributionorder/(?P<pk>(.+))/$', freppledb.input.serializers.DistributionOrderdetailAPI.as_view()),
  (r'^api/input/skill/(?P<pk>(.+))/$', freppledb.input.serializers.SkilldetailAPI.as_view()),
  (r'^api/input/resourceskill/(?P<pk>(.+))/$', freppledb.input.serializers.ResourceSkilldetailAPI.as_view()),
  (r'^api/input/supplier/(?P<pk>(.+))/$', freppledb.input.serializers.SupplierdetailAPI.as_view()),
  (r'^api/input/itemsupplier/(?P<pk>(.+))/$', freppledb.input.serializers.ItemSupplierdetailAPI.as_view()),
  (r'^api/input/itemdistribution/(?P<pk>(.+))/$', freppledb.input.serializers.ItemDistributiondetailAPI.as_view()),

  )
