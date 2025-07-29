#
# Copyright (C) 2007-2020 by frePPLe bv
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

from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from freppledb.input.models import (
    Buffer,
    Calendar,
    CalendarBucket,
    Customer,
    DeliveryOrder,
    Demand,
    DistributionOrder,
    Item,
    ItemDistribution,
    ItemSupplier,
    Location,
    ManufacturingOrder,
    Operation,
    OperationDependency,
    OperationMaterial,
    OperationPlanMaterial,
    OperationPlanResource,
    OperationResource,
    PurchaseOrder,
    Resource,
    ResourceSkill,
    SetupMatrix,
    SetupRule,
    Skill,
    SubOperation,
    Supplier,
)
from freppledb.common.adminforms import MultiDBModelAdmin

from freppledb.admin import data_site
from freppledb.boot import getAttributes


@admin.register(CalendarBucket, site=data_site)
class CalendarBucket_admin(MultiDBModelAdmin):
    model = CalendarBucket
    raw_id_fields = ("calendar",)
    help_url = "model-reference/calendar-buckets.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "calendar",
                    "startdate",
                    "enddate",
                    "value",
                    "priority",
                    "starttime",
                    "endtime",
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
                + [a[0] for a in getAttributes(CalendarBucket) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_calendarbucket_change",
            "permissions": "input.change_calendarbucket",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_calendarbucket_comment",
        },
    ]


@admin.register(Calendar, site=data_site)
class Calendar_admin(MultiDBModelAdmin):
    model = Calendar
    save_on_top = True
    help_url = "model-reference/calendars.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "description",
                    "defaultvalue",
                    "category",
                    "subcategory",
                ]
                + [a[0] for a in getAttributes(Calendar) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_calendar_change",
            "permissions": "input.change_calendar",
        },
        {
            "name": "plan",
            "label": _("detail"),
            "view": "input_calendardetail",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_calendar_comment",
        },
    ]


@admin.register(Location, site=data_site)
class Location_admin(MultiDBModelAdmin):
    model = Location
    raw_id_fields = ("available", "owner")
    help_url = "model-reference/locations.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "owner",
                    "available",
                    "description",
                    "category",
                    "subcategory",
                ]
                + [a[0] for a in getAttributes(Location) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_location_change",
            "permissions": "input.change_location",
        },
        {
            "name": "inboundorders",
            "label": _("inbound distribution"),
            "view": "input_distributionorder_in_by_location",
        },
        {
            "name": "outboundorders",
            "label": _("outbound distribution"),
            "view": "input_distributionorder_out_by_location",
        },
        {
            "name": "manufacturingorders",
            "label": _("manufacturing orders"),
            "view": "input_manufacturingorder_by_location",
        },
        {
            "name": "purchaseorders",
            "label": _("purchase orders"),
            "view": "input_purchaseorder_by_location",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_location_comment",
        },
    ]


@admin.register(Customer, site=data_site)
class Customer_admin(MultiDBModelAdmin):
    model = Customer
    raw_id_fields = ("owner",)
    help_url = "model-reference/customers.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": ["name", "description", "category", "subcategory", "owner"]
                + [a[0] for a in getAttributes(Customer) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_customer_change",
            "permissions": "input.change_customer",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_customer_comment",
        },
    ]


@admin.register(Supplier, site=data_site)
class Supplier_admin(MultiDBModelAdmin):
    model = Supplier
    raw_id_fields = ("available", "owner")
    help_url = "model-reference/suppliers.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "description",
                    "category",
                    "subcategory",
                    "available",
                ]
                + [a[0] for a in getAttributes(Supplier) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_supplier_change",
            "permissions": "input.change_supplier",
        },
        {
            "name": "purchaseorders",
            "label": _("purchase orders"),
            "view": "input_purchaseorder_by_supplier",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_supplier_comment",
        },
    ]


@admin.register(Item, site=data_site)
class Item_admin(MultiDBModelAdmin):
    model = Item
    save_on_top = True
    raw_id_fields = ("owner",)
    search_fields = ("name", "description")
    help_url = "model-reference/items.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "description",
                    "cost",
                    "owner",
                    "uom",
                    "category",
                    "subcategory",
                    "type",
                    "volume",
                    "weight",
                ]
                + [a[0] for a in getAttributes(Item) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_item_change",
            "permissions": "input.change_item",
        },
        {"name": "supplypath", "label": _("supply path"), "view": "supplypath_item"},
        {"name": "whereused", "label": _("where used"), "view": "whereused_item"},
        {
            "name": "inventory",
            "label": _("inventory"),
            "view": "output_buffer_plandetail_by_item",
        },
        {
            "name": "inventorydetail",
            "label": _("inventory detail"),
            "view": "input_operationplanmaterial_plandetail_by_item",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_item_comment",
        },
    ]


@admin.register(ItemSupplier, site=data_site)
class ItemSupplier_admin(MultiDBModelAdmin):
    model = ItemSupplier
    save_on_top = True
    raw_id_fields = ("item", "supplier", "resource")
    help_url = "model-reference/item-suppliers.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "item",
                    "supplier",
                    "location",
                    "leadtime",
                    "cost",
                    "sizeminimum",
                    "sizemultiple",
                    "sizemaximum",
                    "batchwindow",
                    "hard_safety_leadtime",
                    "extra_safety_leadtime",
                    "priority",
                    "fence",
                    "effective_start",
                    "effective_end",
                    "resource",
                    "resource_qty",
                ]
                + [a[0] for a in getAttributes(ItemSupplier) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_itemsupplier_change",
            "permissions": "input.change_itemsupplier",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_itemsupplier_comment",
        },
    ]


@admin.register(ItemDistribution, site=data_site)
class ItemDistribution_admin(MultiDBModelAdmin):
    model = ItemDistribution
    save_on_top = True
    raw_id_fields = ("item", "resource")
    help_url = "model-reference/item-distributions.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "item",
                    "location",
                    "origin",
                    "leadtime",
                    "sizeminimum",
                    "sizemultiple",
                    "sizemaximum",
                    "batchwindow",
                    "cost",
                    "priority",
                    "fence",
                    "effective_start",
                    "effective_end",
                    "resource",
                    "resource_qty",
                ]
                + [a[0] for a in getAttributes(ItemDistribution) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_itemdistribution_change",
            "permissions": "input.change_itemdistribution",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_itemdistribution_comment",
        },
    ]


@admin.register(Operation, site=data_site)
class Operation_admin(MultiDBModelAdmin):
    model = Operation
    raw_id_fields = ("item", "available", "owner")
    help_url = "model-reference/operations.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "type",
                    "item",
                    "location",
                    "duration",
                    "duration_per",
                    "owner",
                    "description",
                    "category",
                    "subcategory",
                    "fence",
                    "posttime",
                    "sizeminimum",
                    "sizemultiple",
                    "sizemaximum",
                    "cost",
                    "available",
                    "priority",
                    "search",
                    "effective_start",
                    "effective_end",
                ]
                + [a[0] for a in getAttributes(Operation) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_operation_change",
            "permissions": "input.change_operation",
        },
        {
            "name": "supplypath",
            "label": _("supply path"),
            "view": "supplypath_operation",
        },
        {"name": "whereused", "label": _("where used"), "view": "whereused_operation"},
        {"name": "plan", "label": _("plan"), "view": "output_operation_plandetail"},
        {
            "name": "plandetail",
            "label": _("manufacturing orders"),
            "view": "input_manufacturingorder_by_operation",
        },
        {
            "name": "constraint",
            "label": _("constrained demand"),
            "view": "output_constraint_operation",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_operation_comment",
        },
    ]


@admin.register(SubOperation, site=data_site)
class SubOperation_admin(MultiDBModelAdmin):
    model = SubOperation
    raw_id_fields = ("operation", "suboperation")
    help_url = "model-reference/suboperations.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "operation",
                    "suboperation",
                    "priority",
                    "effective_start",
                    "effective_end",
                ]
                + [a[0] for a in getAttributes(SubOperation) if a[3]]
                + ["source"]
            },
        ),
    )


@admin.register(OperationDependency, site=data_site)
class OperationDependency_admin(MultiDBModelAdmin):
    model = OperationDependency
    raw_id_fields = ("operation", "blockedby")
    help_url = "model-reference/operation-dependencies.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "operation",
                    "blockedby",
                    "quantity",
                    "safety_leadtime",
                    "hard_safety_leadtime",
                ]
                + [a[0] for a in getAttributes(OperationDependency) if a[3]]
                + ["source"]
            },
        ),
    )


@admin.register(Buffer, site=data_site)
class Buffer_admin(MultiDBModelAdmin):
    model = Buffer
    raw_id_fields = ("location", "item", "minimum_calendar")
    help_url = "model-reference/buffers.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "item",
                    "location",
                    "onhand",
                    "minimum",
                    "maximum",
                    "batch",
                    "description",
                    "category",
                    "subcategory",
                    "type",
                    "minimum_calendar",
                    "maximum_calendar",
                    "min_interval",
                ]
                + [a[0] for a in getAttributes(Buffer) if a[3]]
                + ["source"]
            },
        ),
    )
    save_on_top = True
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "create_or_edit_buffer",
            "permissions": "input.change_buffer",
        },
        {"name": "supplypath", "label": _("supply path"), "view": "supplypath_buffer"},
        {"name": "whereused", "label": _("where used"), "view": "whereused_buffer"},
        {"name": "plan", "label": _("plan"), "view": "output_buffer_plandetail"},
        {
            "name": "plandetail",
            "label": _("plan detail"),
            "view": "input_operationplanmaterial_plandetail_by_buffer",
        },
        {
            "name": "constraint",
            "label": _("constrained demand"),
            "view": "output_constraint_buffer",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_buffer_comment",
        },
    ]


@admin.register(SetupRule, site=data_site)
class SetupRule_admin(MultiDBModelAdmin):
    model = SetupRule
    raw_id_fields = ("setupmatrix",)
    help_url = "model-reference/setup-matrices.html#setup-rule"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "setupmatrix",
                    "priority",
                    "fromsetup",
                    "tosetup",
                    "duration",
                    "cost",
                ]
                + [a[0] for a in getAttributes(ResourceSkill) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_setuprule_change",
            "permissions": "input.change_setuprule",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_setuprule_comment",
        },
    ]


@admin.register(SetupMatrix, site=data_site)
class SetupMatrix_admin(MultiDBModelAdmin):
    model = SetupMatrix
    help_url = "model-reference/setup-matrices.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": ["name"]
                + [a[0] for a in getAttributes(ResourceSkill) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_setupmatrix_change",
            "permissions": "input.change_setupmatrix",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_setupmatrix_comment",
        },
    ]


@admin.register(Skill, site=data_site)
class Skill_admin(MultiDBModelAdmin):
    model = Skill
    help_url = "model-reference/skils.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": ["name"]
                + [a[0] for a in getAttributes(Skill) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_skill_change",
            "permissions": "input.change_skill",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_skill_comment",
        },
    ]


@admin.register(ResourceSkill, site=data_site)
class ResourceSkill_admin(MultiDBModelAdmin):
    model = ResourceSkill
    raw_id_fields = ("resource", "skill")
    help_url = "model-reference/resource-skills.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "resource",
                    "skill",
                    "priority",
                    "effective_start",
                    "effective_end",
                ]
                + [a[0] for a in getAttributes(ResourceSkill) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_resourceskill_change",
            "permissions": "input.change_resoureskill",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_resourceskill_comment",
        },
    ]


@admin.register(Resource, site=data_site)
class Resource_admin(MultiDBModelAdmin):
    model = Resource
    raw_id_fields = (
        "maximum_calendar",
        "location",
        "setupmatrix",
        "owner",
        "available",
        "efficiency_calendar",
    )
    help_url = "model-reference/resources.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "location",
                    "type",
                    "maximum",
                    "maximum_calendar",
                    "available",
                    "constrained",
                    "description",
                    "category",
                    "subcategory",
                    "owner",
                    "cost",
                    "maxearly",
                    "setupmatrix",
                    "efficiency",
                    "efficiency_calendar",
                ]
                + [a[0] for a in getAttributes(Resource) if a[3]]
                + ["source"]
            },
        ),
    )
    save_on_top = True
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_resource_change",
            "permissions": "input.change_resource",
        },
        {
            "name": "supplypath",
            "label": _("supply path"),
            "view": "supplypath_resource",
        },
        {"name": "whereused", "label": _("where used"), "view": "whereused_resource"},
        {"name": "plan", "label": _("plan"), "view": "output_resource_plandetail"},
        {
            "name": "plandetail",
            "label": _("plan detail"),
            "view": "input_operationplanresource_plandetail",
        },
        {
            "name": "constraint",
            "label": _("constrained demand"),
            "view": "output_constraint_resource",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_resource_comment",
        },
    ]


@admin.register(OperationMaterial, site=data_site)
class OperationMaterial_admin(MultiDBModelAdmin):
    model = OperationMaterial
    raw_id_fields = ("operation", "item", "location")
    help_url = "model-reference/operation-materials.html"
    save_on_top = True
    exclude = ("id",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "operation",
                    "item",
                    "type",
                    "quantity",
                    "location",
                    "quantity_fixed",
                    "transferbatch",
                    "offset",
                    "effective_start",
                    "effective_end",
                    "name",
                    "priority",
                    "search",
                ]
                + [a[0] for a in getAttributes(OperationMaterial) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_operationmaterial_change",
            "permissions": "input.change_operationmaterial",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_operationmaterial_comment",
        },
    ]


@admin.register(OperationResource, site=data_site)
class OperationResource_admin(MultiDBModelAdmin):
    model = OperationResource
    raw_id_fields = ("operation", "resource", "skill")
    help_url = "model-reference/operation-resources.html"
    save_on_top = True
    exclude = ("id",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "operation",
                    "resource",
                    "quantity",
                    "skill",
                    "setup",
                    "quantity_fixed",
                    "effective_start",
                    "effective_end",
                    "name",
                    "priority",
                    "search",
                ]
                + [a[0] for a in getAttributes(OperationResource) if a[3]],
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_operationresource_change",
            "permissions": "input.change_operationresource",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_operationresource_comment",
        },
    ]


@admin.register(ManufacturingOrder, site=data_site)
class ManufacturingOrder_admin(MultiDBModelAdmin):
    model = ManufacturingOrder
    raw_id_fields = ("operation", "owner", "demand")
    help_url = "model-reference/manufacturing-orders.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "reference",
                    "operation",
                    "quantity",
                    "quantity_completed",
                    "startdate",
                    "enddate",
                    "owner",
                    "status",
                    "batch",
                    "remark",
                    "demand",
                ]
                + [a[0] for a in getAttributes(ManufacturingOrder) if a[3]]
            },
        ),
    )
    exclude = (
        "type",
        "source",
        "criticality",
        "delay",
        "origin",
        "destination",
        "item",
        "supplier",
        "location",
        "name",
        "due",
        "color",
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_manufacturingorder_change",
            "permissions": "input.change_manufacturingorder",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_manufacturingorder_comment",
        },
    ]


@admin.register(DistributionOrder, site=data_site)
class DistributionOrder_admin(MultiDBModelAdmin):
    model = DistributionOrder
    raw_id_fields = ("item",)
    help_url = "model-reference/distribution-orders.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "reference",
                    "item",
                    "origin",
                    "destination",
                    "quantity",
                    "shipping_date",
                    "receipt_date",
                    "status",
                    "batch",
                    "remark",
                ]
                + [a[0] for a in getAttributes(DistributionOrder) if a[3]]
            },
        ),
    )
    exclude = (
        "type",
        "source",
        "criticality",
        "delay",
        "operation",
        "owner",
        "color",
        "supplier",
        "location",
        "demand",
        "name",
        "due",
        "startdate",
        "enddate",
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_distributionorder_change",
            "permissions": "input.change_distributionorder",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_distributionorder_comment",
        },
    ]


@admin.register(PurchaseOrder, site=data_site)
class PurchaseOrder_admin(MultiDBModelAdmin):
    model = PurchaseOrder
    raw_id_fields = ("item", "supplier")
    help_url = "model-reference/purchase-orders.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "reference",
                    "item",
                    "location",
                    "supplier",
                    "quantity",
                    "ordering_date",
                    "receipt_date",
                    "status",
                    "batch",
                    "remark",
                ]
                + [a[0] for a in getAttributes(PurchaseOrder) if a[3]]
            },
        ),
    )
    exclude = (
        "type",
        "source",
        "criticality",
        "delay",
        "operation",
        "owner",
        "color",
        "origin",
        "destination",
        "demand",
        "name",
        "due",
        "startdate",
        "enddate",
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_purchaseorder_change",
            "permissions": "input.change_purchaseorder",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_purchaseorder_comment",
        },
    ]


@admin.register(DeliveryOrder, site=data_site)
class DeliveryOrder_admin(MultiDBModelAdmin):
    model = DeliveryOrder
    raw_id_fields = ("item", "demand")
    help_url = "model-reference/delivery-orders.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "reference",
                    "demand",
                    "item",
                    "location",
                    "quantity",
                    "status",
                    "batch",
                    "remark",
                )
            },
        ),
    )
    exclude = (
        "type",
        "source",
        "criticality",
        "delay",
        "operation",
        "owner",
        "color",
        "origin",
        "destination",
        "name",
        "supplier",
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_deliveryorder_change",
            "permissions": "input.change_deliveryorder",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_deliveryorder_comment",
        },
    ]


@admin.register(Demand, site=data_site)
class Demand_admin(MultiDBModelAdmin):
    model = Demand
    raw_id_fields = ("customer", "item", "operation")
    help_url = "model-reference/sales-orders.html"
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "owner",
                    "item",
                    "location",
                    "customer",
                    "due",
                    "quantity",
                    "priority",
                    "status",
                    "description",
                    "category",
                    "subcategory",
                    "batch",
                    "operation",
                    "policy",
                    "minshipment",
                    "maxlateness",
                ]
                + [a[0] for a in getAttributes(Demand) if a[3]]
                + ["source"]
            },
        ),
    )
    save_on_top = True
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_demand_change",
            "permissions": "input.change_demand",
        },
        {"name": "supplypath", "label": _("supply path"), "view": "supplypath_demand"},
        {
            "name": "constraint",
            "label": _("why short or late?"),
            "view": "output_constraint_demand",
        },
        {"name": "plan", "label": _("plan"), "view": "output_demand_pegging"},
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_demand_comment",
        },
    ]


@admin.register(OperationPlanResource, site=data_site)
class OperationPlanResource_admin(MultiDBModelAdmin):
    model = OperationPlanResource
    raw_id_fields = (
        "operationplan",
    )  # TODO a foreign key to OperationPlan doesn't work because it's an abstract class without admin
    help_url = "model-reference/operationplan-resources.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": ["operationplan", "resource", "quantity"]
                + [a[0] for a in getAttributes(OperationPlanResource) if a[3]]
                + ["source"]
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_operationplanresource_change",
            "permissions": "input.change_operationplanresource",
        }
    ]


@admin.register(OperationPlanMaterial, site=data_site)
class OperationPlanMaterial_admin(MultiDBModelAdmin):
    model = OperationPlanMaterial
    raw_id_fields = (
        "operationplan",
        "item",
    )  # TODO a foreign key to OperationPlan doesn't work because it's an abstract class without admin
    help_url = "model-reference/operationplan-materials.html"
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "operationplan",
                    "item",
                    "location",
                    "status",
                    "quantity",
                    "flowdate",
                )
            },
        ),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_operationplanmaterial_change",
            "permissions": "input.change_operationplanmaterial",
        }
    ]
