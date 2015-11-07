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

  # REST framework
  (r'^api/input/buffer/$', freppledb.input.serializers.BufferREST.as_view()),
  (r'^api/input/resource/$', freppledb.input.serializers.ResourceREST.as_view()),
  (r'^api/input/location/$', freppledb.input.serializers.LocationREST.as_view()),
  (r'^api/input/customer/$', freppledb.input.serializers.CustomerREST.as_view()),
  (r'^api/input/demand/$', freppledb.input.serializers.DemandREST.as_view()),
  (r'^api/input/item/$', freppledb.input.serializers.ItemREST.as_view()),
  (r'^api/input/load/$', freppledb.input.serializers.LoadREST.as_view()),
  (r'^api/input/flow/$', freppledb.input.serializers.FlowREST.as_view()),
  (r'^api/input/calendar/$', freppledb.input.serializers.CalendarREST.as_view()),
  (r'^api/input/calendarbucket/$', freppledb.input.serializers.CalendarBucketREST.as_view()),
  (r'^api/input/operation/$', freppledb.input.serializers.OperationREST.as_view()),
  (r'^api/input/setupmatrix/$', freppledb.input.serializers.SetupMatrixREST.as_view()),
  (r'^api/input/setuprule/$', freppledb.input.serializers.SetupRuleREST.as_view()),
  (r'^api/input/suboperation/$', freppledb.input.serializers.SubOperationREST.as_view()),
  (r'^api/input/operationplan/$', freppledb.input.serializers.OperationPlanREST.as_view()),
  (r'^api/input/purchaseorder/$', freppledb.input.serializers.PurchaseOrderREST.as_view()),
  (r'^api/input/distributionorder/$', freppledb.input.serializers.DistributionOrderREST.as_view()),
  (r'^api/input/skill/$', freppledb.input.serializers.SkillREST.as_view()),
  (r'^api/input/resourceskill/$', freppledb.input.serializers.ResourceSkillREST.as_view()),
  (r'^api/input/supplier/$', freppledb.input.serializers.SupplierREST.as_view()),
  (r'^api/input/itemsupplier/$', freppledb.input.serializers.ItemSupplierREST.as_view()),
  (r'^api/input/itemdistribution/$', freppledb.input.serializers.ItemDistributionREST.as_view()),

  )
