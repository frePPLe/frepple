#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.urls import path, re_path
from django.views.generic.base import TemplateView

from freppledb import mode

# Automatically add these URLs when the application is installed
autodiscover = True

if mode == "WSGI":
    from . import views
    from . import serializers
    from freppledb.common.api.router import rest_api_router

    urlpatterns = [
        # Overridable card for kanban and calendar views
        path(
            "input/kanbancard.html",
            TemplateView.as_view(template_name="input/kanbancard.html"),
        ),
        path("input/card.html", TemplateView.as_view(template_name="input/card.html")),
        # Model list reports, which override standard admin screens
        path(
            "data/input/buffer/",
            views.BufferList.as_view(),
            name="input_buffer_changelist",
        ),
        path(
            "data/input/resource/",
            views.ResourceList.as_view(),
            name="input_resource_changelist",
        ),
        path(
            "data/input/location/",
            views.LocationList.as_view(),
            name="input_location_changelist",
        ),
        path(
            "data/input/customer/",
            views.CustomerList.as_view(),
            name="input_customer_changelist",
        ),
        path(
            "data/input/demand/",
            views.DemandList.as_view(),
            name="input_demand_changelist",
        ),
        path(
            "data/input/item/",
            views.ItemList.as_view(),
            name="input_item_changelist",
        ),
        path(
            "data/input/operationresource/",
            views.OperationResourceList.as_view(),
            name="input_operationresource_changelist",
        ),
        path(
            "data/input/operationmaterial/",
            views.OperationMaterialList.as_view(),
            name="input_operationmaterial_changelist",
        ),
        path(
            "data/input/calendar/",
            views.CalendarList.as_view(),
            name="input_calendar_changelist",
        ),
        re_path(
            r"^data/input/calendardetail/(.+)/$",
            views.manufacturing.CalendarDetail.as_view(),
            name="input_calendardetail",
        ),
        path(
            "data/input/calendarbucket/",
            views.CalendarBucketList.as_view(),
            name="input_calendarbucket_changelist",
        ),
        path(
            "data/input/operation/",
            views.OperationList.as_view(),
            name="input_operation_changelist",
        ),
        path(
            "data/input/setupmatrix/",
            views.SetupMatrixList.as_view(),
            name="input_setupmatrix_changelist",
        ),
        path(
            "data/input/setuprule/",
            views.SetupRuleList.as_view(),
            name="input_setuprule_changelist",
        ),
        path(
            "data/input/suboperation/",
            views.SubOperationList.as_view(),
            name="input_suboperation_changelist",
        ),
        path(
            "data/input/operationdependency/",
            views.OperationDependencyList.as_view(),
            name="input_operationdepency_changelist",
        ),
        path(
            "data/input/workorder/",
            views.WorkOrderList.as_view(),
            name="input_workorder_changelist",
        ),
        re_path(
            r"^data/input/workorder/location/(.+)/$",
            views.WorkOrderList.as_view(),
            name="input_workorder_by_location",
        ),
        re_path(
            r"^data/input/workorder/operation/(.+)/$",
            views.WorkOrderList.as_view(),
            name="input_workorder_by_operation",
        ),
        re_path(
            r"^data/input/workorder/item/(.+)/$",
            views.WorkOrderList.as_view(),
            name="input_workorder_by_item",
        ),
        re_path(
            r"^data/input/workorder/operationplanmaterial/([^/]+)/([^/]+)/(.+)/$",
            views.WorkOrderList.as_view(),
            name="input_workorder_by_opm",
        ),
        re_path(
            r"^data/input/workorder/produced/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.WorkOrderList.as_view(),
            name="input_workorder_by_produced",
        ),
        re_path(
            r"^data/input/workorder/consumed/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.WorkOrderList.as_view(),
            name="input_workorder_by_consumed",
        ),
        path(
            "data/input/manufacturingorder/",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_changelist",
        ),
        re_path(
            r"^data/input/manufacturingorder/location/(.+)/$",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_by_location",
        ),
        re_path(
            r"^data/input/manufacturingorder/operation/(.+)/$",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_by_operation",
        ),
        re_path(
            r"^data/input/manufacturingorder/item/(.+)/$",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_by_item",
        ),
        re_path(
            r"^data/input/manufacturingorder/operationplanmaterial/([^/]+)/([^/]+)/(.+)/$",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_by_opm",
        ),
        re_path(
            r"^data/input/manufacturingorder/produced/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_by_produced",
        ),
        re_path(
            r"^data/input/manufacturingorder/consumed/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.ManufacturingOrderList.as_view(),
            name="input_manufacturingorder_by_consumed",
        ),
        path(
            "data/input/purchaseorder/",
            views.PurchaseOrderList.as_view(),
            name="input_purchaseorder_changelist",
        ),
        re_path(
            r"^data/input/purchaseorder/item/(.+)/$",
            views.PurchaseOrderList.as_view(),
            name="input_purchaseorder_by_item",
        ),
        re_path(
            r"^data/input/purchaseorder/supplier/(.+)/$",
            views.PurchaseOrderList.as_view(),
            name="input_purchaseorder_by_supplier",
        ),
        re_path(
            r"^data/input/purchaseorder/location/(.+)/$",
            views.PurchaseOrderList.as_view(),
            name="input_purchaseorder_by_location",
        ),
        re_path(
            r"^data/input/purchaseorder/operationplanmaterial/([^/]+)/([^/]+)/(.+)/$",
            views.PurchaseOrderList.as_view(),
            name="input_purchaseorder_by_opm",
        ),
        re_path(
            r"^data/input/purchaseorder/produced/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.PurchaseOrderList.as_view(),
            name="input_purchaseorder_by_produced",
        ),
        path(
            "data/input/distributionorder/",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_changelist",
        ),
        re_path(
            r"^data/input/distributionorder/item/(.+)/$",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_by_item",
        ),
        re_path(
            r"^data/input/distributionorder/location/(.+)/in/$",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_in_by_location",
        ),
        re_path(
            r"^data/input/distributionorder/location/(.+)/out/$",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_out_by_location",
        ),
        re_path(
            r"^data/input/distributionorder/operationplanmaterial/([^/]+)/([^/]+)/(.+)/$",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_by_opm",
        ),
        re_path(
            r"^data/input/distributionorder/produced/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_by_produced",
        ),
        re_path(
            r"^data/input/distributionorder/consumed/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.DistributionOrderList.as_view(),
            name="input_distributionorder_by_consumed",
        ),
        path(
            "data/input/skill/",
            views.SkillList.as_view(),
            name="input_skill_changelist",
        ),
        path(
            "data/input/resourceskill/",
            views.ResourceSkillList.as_view(),
            name="input_resourceskill_changelist",
        ),
        path(
            "data/input/supplier/",
            views.SupplierList.as_view(),
            name="input_supplier_changelist",
        ),
        path(
            "data/input/itemsupplier/",
            views.ItemSupplierList.as_view(),
            name="input_itemsupplier_changelist",
        ),
        path(
            "data/input/itemdistribution/",
            views.ItemDistributionList.as_view(),
            name="input_itemdistribution_changelist",
        ),
        re_path(
            r"^data/input/deliveryorder/item/(.+)/$",
            views.DeliveryOrderList.as_view(),
            name="input_deliveryorder_by_item",
        ),
        re_path(
            r"^data/input/deliveryorder/consumed/([^/]+)/([^/]+)/([^/]+)/(.+)/$",
            views.DeliveryOrderList.as_view(),
            name="input_deliveryorder_by_consumed",
        ),
        path(
            "data/input/deliveryorder/",
            views.DeliveryOrderList.as_view(),
            name="input_deliveryorder_changelist",
        ),
        re_path(
            r"^data/input/operationplanmaterial/item/(.+)/$",
            views.InventoryDetail.as_view(),
            name="input_operationplanmaterial_plandetail_by_item",
        ),
        re_path(
            r"^data/input/operationplanmaterial/buffer/(.+)/$",
            views.InventoryDetail.as_view(),
            name="input_operationplanmaterial_plandetail_by_buffer",
        ),
        path(
            "data/input/operationplanmaterial/",
            views.InventoryDetail.as_view(),
            name="input_operationplanmaterial_plan",
        ),
        re_path(
            r"^data/input/operationplanresource/resource/(.+)/$",
            views.ResourceDetail.as_view(),
            name="input_operationplanresource_plandetail",
        ),
        path(
            "data/input/operationplanresource/",
            views.ResourceDetail.as_view(),
            name="input_operationplanresource_plan",
        ),
        # Special reports
        re_path(
            r"^data/input/buffer/(.+)/create_or_edit/",
            views.CreateOrEditBuffer,
            name="create_or_edit_buffer",
        ),
        re_path(
            r"^supplypath/item/(.+)/$",
            views.UpstreamItemPath.as_view(),
            name="supplypath_item",
        ),
        re_path(
            r"^whereused/item/(.+)/$",
            views.DownstreamItemPath.as_view(),
            name="whereused_item",
        ),
        re_path(
            r"^supplypath/buffer/(.+)/$",
            views.UpstreamBufferPath.as_view(),
            name="supplypath_buffer",
        ),
        re_path(
            r"^whereused/buffer/(.+)/$",
            views.DownstreamBufferPath.as_view(),
            name="whereused_buffer",
        ),
        re_path(
            r"^supplypath/resource/(.+)/$",
            views.UpstreamResourcePath.as_view(),
            name="supplypath_resource",
        ),
        re_path(
            r"^supplypath/demand/(.+)/$",
            views.UpstreamDemandPath.as_view(),
            name="supplypath_demand",
        ),
        re_path(
            r"^whereused/resource/(.+)/$",
            views.DownstreamResourcePath.as_view(),
            name="whereused_resource",
        ),
        re_path(
            r"^supplypath/operation/(.+)/$",
            views.UpstreamOperationPath.as_view(),
            name="supplypath_operation",
        ),
        re_path(
            r"^whereused/operation/(.+)/$",
            views.DownstreamOperationPath.as_view(),
            name="whereused_operation",
        ),
        path("search/", views.search, name="search"),
        path(
            "operationplan/",
            views.OperationPlanDetail.as_view(),
            name="operationplandetail",
        ),
    ]

    rest_api_router.register(
        "input", "buffer", serializers.BufferAPI, serializers.BufferdetailAPI
    )
    rest_api_router.register(
        "input", "resource", serializers.ResourceAPI, serializers.ResourcedetailAPI
    )
    rest_api_router.register(
        "input", "location", serializers.LocationAPI, serializers.LocationdetailAPI
    )
    rest_api_router.register(
        "input", "customer", serializers.CustomerAPI, serializers.CustomerdetailAPI
    )
    rest_api_router.register(
        "input", "demand", serializers.DemandAPI, serializers.DemanddetailAPI
    )
    rest_api_router.register(
        "input", "item", serializers.ItemAPI, serializers.ItemdetailAPI
    )
    rest_api_router.register(
        "input",
        "operationresource",
        serializers.OperationResourceAPI,
        serializers.OperationResourcedetailAPI,
    )
    rest_api_router.register(
        "input",
        "operationmaterial",
        serializers.OperationMaterialAPI,
        serializers.OperationMaterialdetailAPI,
    )
    rest_api_router.register(
        "input",
        "operationplanresource",
        serializers.OperationPlanResourceAPI,
        serializers.OperationPlanResourcedetailAPI,
    )
    rest_api_router.register(
        "input",
        "operationplanmaterial",
        serializers.OperationPlanMaterialAPI,
        serializers.OperationPlanMaterialdetailAPI,
    )
    rest_api_router.register(
        "input", "calendar", serializers.CalendarAPI, serializers.CalendardetailAPI
    )
    rest_api_router.register(
        "input",
        "calendarbucket",
        serializers.CalendarBucketAPI,
        serializers.CalendarBucketdetailAPI,
    )
    rest_api_router.register(
        "input", "operation", serializers.OperationAPI, serializers.OperationdetailAPI
    )
    rest_api_router.register(
        "input",
        "setupmatrix",
        serializers.SetupMatrixAPI,
        serializers.SetupMatrixdetailAPI,
    )
    rest_api_router.register(
        "input", "setuprule", serializers.SetupRuleAPI, serializers.SetupRuledetailAPI
    )
    rest_api_router.register(
        "input",
        "suboperation",
        serializers.SubOperationAPI,
        serializers.SubOperationdetailAPI,
    )
    rest_api_router.register(
        "input",
        "operationdependency",
        serializers.OperationDependencyAPI,
        serializers.OperationDependencydetailAPI,
    )
    rest_api_router.register(
        "input",
        "manufacturingorder",
        serializers.ManufacturingOrderAPI,
        serializers.ManufacturingOrderdetailAPI,
    )
    rest_api_router.register(
        "input", "workorder", serializers.WorkOrderAPI, serializers.WorkOrderdetailAPI
    )
    rest_api_router.register(
        "input",
        "purchaseorder",
        serializers.PurchaseOrderAPI,
        serializers.PurchaseOrderdetailAPI,
    )
    rest_api_router.register(
        "input",
        "distributionorder",
        serializers.DistributionOrderAPI,
        serializers.DistributionOrderdetailAPI,
    )
    rest_api_router.register(
        "input",
        "deliveryorder",
        serializers.DeliveryOrderAPI,
        serializers.DeliveryOrderdetailAPI,
    )
    rest_api_router.register(
        "input", "skill", serializers.SkillAPI, serializers.SkilldetailAPI
    )
    rest_api_router.register(
        "input",
        "resourceskill",
        serializers.ResourceSkillAPI,
        serializers.ResourceSkilldetailAPI,
    )
    rest_api_router.register(
        "input", "supplier", serializers.SupplierAPI, serializers.SupplierdetailAPI
    )
    rest_api_router.register(
        "input",
        "itemsupplier",
        serializers.ItemSupplierAPI,
        serializers.ItemSupplierdetailAPI,
    )
    rest_api_router.register(
        "input",
        "itemdistribution",
        serializers.ItemDistributionAPI,
        serializers.ItemDistributiondetailAPI,
    )

else:
    from . import services

    svcpatterns = [
        path("operationplan/", services.OperationplanService.as_asgi()),
        path("supplypath/<str:model>/<str:name>/", services.SupplyPathSvc.as_asgi()),
        path("whereused/<str:model>/<str:name>/", services.SupplyPathSvc.as_asgi()),
    ]
