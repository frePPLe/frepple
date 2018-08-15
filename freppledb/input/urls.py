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

import freppledb.input.views
import freppledb.input.serializers

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [

  # Model list reports, which override standard admin screens
  url(r'^data/input/buffer/$', freppledb.input.views.BufferList.as_view(), name="input_buffer_changelist"),
  url(r'^data/input/resource/$', freppledb.input.views.ResourceList.as_view(), name="input_resource_changelist"),
  url(r'^data/input/location/$', freppledb.input.views.LocationList.as_view(), name="input_location_changelist"),
  url(r'^data/input/customer/$', freppledb.input.views.CustomerList.as_view(), name="input_customer_changelist"),
  url(r'^data/input/demand/$', freppledb.input.views.DemandList.as_view(), name="input_demand_changelist"),
  url(r'^data/input/item/$', freppledb.input.views.ItemList.as_view(), name="input_item_changelist"),
  url(r'^data/input/operationresource/$', freppledb.input.views.OperationResourceList.as_view(), name="input_operationresource_changelist"),
  url(r'^data/input/operationmaterial/$', freppledb.input.views.OperationMaterialList.as_view(), name="input_operationmaterial_changelist"),
  url(r'^data/input/calendar/$', freppledb.input.views.CalendarList.as_view(), name="input_calendar_changelist"),
  url(r'^data/input/calendarbucket/$', freppledb.input.views.CalendarBucketList.as_view(), name="input_calendarbucket_changelist"),
  url(r'^data/input/operation/$', freppledb.input.views.OperationList.as_view(), name="input_operation_changelist"),
  url(r'^data/input/setupmatrix/$', freppledb.input.views.SetupMatrixList.as_view(), name="input_setupmatrix_changelist"),
  url(r'^data/input/setuprule/$', freppledb.input.views.SetupRuleList.as_view(), name="input_setuprule_changelist"),
  url(r'^data/input/suboperation/$', freppledb.input.views.SubOperationList.as_view(), name="input_suboperation_changelist"),
  url(r'^data/input/manufacturingorder/$', freppledb.input.views.ManufacturingOrderList.as_view(), name="input_manufacturingorder_changelist"),
  url(r'^data/input/manufacturingorder/location/(.+)/$', freppledb.input.views.ManufacturingOrderList.as_view(), name="input_manufacturingorder_by_location"),
  url(r'^data/input/purchaseorder/$', freppledb.input.views.PurchaseOrderList.as_view(), name="input_purchaseorder_changelist"),
  url(r'^data/input/purchaseorder/item/(.+)/$', freppledb.input.views.PurchaseOrderList.as_view(), name="input_purchaseorder_by_item"),
  url(r'^data/input/purchaseorder/supplier/(.+)/$', freppledb.input.views.PurchaseOrderList.as_view(), name="input_purchaseorder_by_supplier"),
  url(r'^data/input/purchaseorder/location/(.+)/$', freppledb.input.views.PurchaseOrderList.as_view(), name="input_purchaseorder_by_location"),
  url(r'^data/input/distributionorder/$', freppledb.input.views.DistributionOrderList.as_view(), name="input_distributionorder_changelist"),
  url(r'^data/input/distributionorder/location/(.+)/in/$', freppledb.input.views.DistributionOrderList.as_view(), name="input_distributionorder_in_by_location"),
  url(r'^data/input/distributionorder/location/(.+)/out/$', freppledb.input.views.DistributionOrderList.as_view(), name="input_distributionorder_out_by_location"),
  url(r'^data/input/skill/$', freppledb.input.views.SkillList.as_view(), name="input_skill_changelist"),
  url(r'^data/input/resourceskill/$', freppledb.input.views.ResourceSkillList.as_view(), name="input_resourceskill_changelist"),
  url(r'^data/input/supplier/$', freppledb.input.views.SupplierList.as_view(), name="input_supplier_changelist"),
  url(r'^data/input/itemsupplier/$', freppledb.input.views.ItemSupplierList.as_view(), name="input_itemsupplier_changelist"),
  url(r'^data/input/itemdistribution/$', freppledb.input.views.ItemDistributionList.as_view(), name="input_itemdistribution_changelist"),
  url(r'^data/input/deliveryorder/item/(.+)/$', freppledb.input.views.DeliveryOrderList.as_view(), name="input_deliveryorder_by_item"),
  url(r'^data/input/deliveryorder/$', freppledb.input.views.DeliveryOrderList.as_view(), name="input_deliveryorder_changelist"),

  # Special reports
  url(r'^supplypath/item/(.+)/$', freppledb.input.views.UpstreamItemPath.as_view(), name="supplypath_item"),
  url(r'^whereused/item/(.+)/$', freppledb.input.views.DownstreamItemPath.as_view(), name="whereused_item"),
  url(r'^supplypath/buffer/(.+)/$', freppledb.input.views.UpstreamBufferPath.as_view(), name="supplypath_buffer"),
  url(r'^whereused/buffer/(.+)/$', freppledb.input.views.DownstreamBufferPath.as_view(), name="whereused_buffer"),
  url(r'^supplypath/resource/(.+)/$', freppledb.input.views.UpstreamResourcePath.as_view(), name="supplypath_resource"),
  url(r'^supplypath/demand/(.+)/$', freppledb.input.views.UpstreamDemandPath.as_view(), name="supplypath_demand"),
  url(r'^whereused/resource/(.+)/$', freppledb.input.views.DownstreamResourcePath.as_view(), name="whereused_resource"),
  url(r'^supplypath/operation/(.+)/$', freppledb.input.views.UpstreamOperationPath.as_view(), name="supplypath_operation"),
  url(r'^whereused/operation/(.+)/$', freppledb.input.views.DownstreamOperationPath.as_view(), name="whereused_operation"),
  url(r'^search/$', freppledb.input.views.search, name="search"),
  url(r'^operationplan/$', freppledb.input.views.OperationPlanDetail.as_view(), name="operationplandetail"),

  # REST API framework
  url(r'^api/input/buffer/$', freppledb.input.serializers.BufferAPI.as_view()),
  url(r'^api/input/resource/$', freppledb.input.serializers.ResourceAPI.as_view()),
  url(r'^api/input/location/$', freppledb.input.serializers.LocationAPI.as_view()),
  url(r'^api/input/customer/$', freppledb.input.serializers.CustomerAPI.as_view()),
  url(r'^api/input/demand/$', freppledb.input.serializers.DemandAPI.as_view()),
  url(r'^api/input/item/$', freppledb.input.serializers.ItemAPI.as_view()),
  url(r'^api/input/operationresource/$', freppledb.input.serializers.OperationResourceAPI.as_view()),
  url(r'^api/input/operationmaterial/$', freppledb.input.serializers.OperationMaterialAPI.as_view()),
  url(r'^api/input/calendar/$', freppledb.input.serializers.CalendarAPI.as_view()),
  url(r'^api/input/calendarbucket/$', freppledb.input.serializers.CalendarBucketAPI.as_view()),
  url(r'^api/input/operation/$', freppledb.input.serializers.OperationAPI.as_view()),
  url(r'^api/input/setupmatrix/$', freppledb.input.serializers.SetupMatrixAPI.as_view()),
  url(r'^api/input/setuprule/$', freppledb.input.serializers.SetupRuleAPI.as_view()),
  url(r'^api/input/suboperation/$', freppledb.input.serializers.SubOperationAPI.as_view()),
  url(r'^api/input/manufacturingorder/$', freppledb.input.serializers.ManufacturingOrderAPI.as_view()),
  url(r'^api/input/purchaseorder/$', freppledb.input.serializers.PurchaseOrderAPI.as_view()),
  url(r'^api/input/distributionorder/$', freppledb.input.serializers.DistributionOrderAPI.as_view()),
  url(r'^api/input/deliveryorder/$', freppledb.input.serializers.DeliveryOrderAPI.as_view()),
  url(r'^api/input/skill/$', freppledb.input.serializers.SkillAPI.as_view()),
  url(r'^api/input/resourceskill/$', freppledb.input.serializers.ResourceSkillAPI.as_view()),
  url(r'^api/input/supplier/$', freppledb.input.serializers.SupplierAPI.as_view()),
  url(r'^api/input/itemsupplier/$', freppledb.input.serializers.ItemSupplierAPI.as_view()),
  url(r'^api/input/itemdistribution/$', freppledb.input.serializers.ItemDistributionAPI.as_view()),

  url(r'^api/input/buffer/(?P<pk>(.+))/$', freppledb.input.serializers.BufferdetailAPI.as_view()),
  url(r'^api/input/resource/(?P<pk>(.+))/$', freppledb.input.serializers.ResourcedetailAPI.as_view()),
  url(r'^api/input/location/(?P<pk>(.+))/$', freppledb.input.serializers.LocationdetailAPI.as_view()),
  url(r'^api/input/customer/(?P<pk>(.+))/$', freppledb.input.serializers.CustomerdetailAPI.as_view()),
  url(r'^api/input/demand/(?P<pk>(.+))/$', freppledb.input.serializers.DemanddetailAPI.as_view()),
  url(r'^api/input/item/(?P<pk>(.+))/$', freppledb.input.serializers.ItemdetailAPI.as_view()),
  url(r'^api/input/operationresource/(?P<pk>(.+))/$', freppledb.input.serializers.OperationResourcedetailAPI.as_view()),
  url(r'^api/input/operationmaterial/(?P<pk>(.+))/$', freppledb.input.serializers.OperationMaterialdetailAPI.as_view()),
  url(r'^api/input/calendar/(?P<pk>(.+))/$', freppledb.input.serializers.CalendardetailAPI.as_view()),
  url(r'^api/input/calendarbucket/(?P<pk>(.+))/$', freppledb.input.serializers.CalendarBucketdetailAPI.as_view()),
  url(r'^api/input/operation/(?P<pk>(.+))/$', freppledb.input.serializers.OperationdetailAPI.as_view()),
  url(r'^api/input/setupmatrix/(?P<pk>(.+))/$', freppledb.input.serializers.SetupMatrixdetailAPI.as_view()),
  url(r'^api/input/setuprule/(?P<pk>(.+))/$', freppledb.input.serializers.SetupRuledetailAPI.as_view()),
  url(r'^api/input/suboperation/(?P<pk>(.+))/$', freppledb.input.serializers.SubOperationdetailAPI.as_view()),
  url(r'^api/input/manufacturingorder/(?P<pk>(.+))/$', freppledb.input.serializers.ManufacturingOrderdetailAPI.as_view()),
  url(r'^api/input/purchaseorder/(?P<pk>(.+))/$', freppledb.input.serializers.PurchaseOrderdetailAPI.as_view()),
  url(r'^api/input/distributionorder/(?P<pk>(.+))/$', freppledb.input.serializers.DistributionOrderdetailAPI.as_view()),
  url(r'^api/input/deliveryorder/(?P<pk>(.+))/$', freppledb.input.serializers.DeliveryOrderdetailAPI.as_view()),
  url(r'^api/input/skill/(?P<pk>(.+))/$', freppledb.input.serializers.SkilldetailAPI.as_view()),
  url(r'^api/input/resourceskill/(?P<pk>(.+))/$', freppledb.input.serializers.ResourceSkilldetailAPI.as_view()),
  url(r'^api/input/supplier/(?P<pk>(.+))/$', freppledb.input.serializers.SupplierdetailAPI.as_view()),
  url(r'^api/input/itemsupplier/(?P<pk>(.+))/$', freppledb.input.serializers.ItemSupplierdetailAPI.as_view()),
  url(r'^api/input/itemdistribution/(?P<pk>(.+))/$', freppledb.input.serializers.ItemDistributiondetailAPI.as_view()),

  ]
