#
# Copyright (C) 2007-2020 by frePPLe bv
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

from django.utils.translation import gettext_lazy as _

from freppledb.input.models import Resource, Operation, Location, SetupMatrix, SetupRule
from freppledb.input.models import Buffer, Customer, Demand, Item, OperationResource
from freppledb.input.models import OperationMaterial, Skill, ResourceSkill, Supplier
from freppledb.input.models import (
    Calendar,
    CalendarBucket,
    ManufacturingOrder,
    SubOperation,
)
from freppledb.input.models import ItemSupplier, ItemDistribution, DistributionOrder
from freppledb.input.models import PurchaseOrder, DeliveryOrder, OperationPlanResource
from freppledb.input.models import OperationPlanMaterial
from freppledb.common.adminforms import MultiDBModelAdmin, MultiDBTabularInline

from freppledb.admin import data_site
from freppledb.boot import getAttributes


class CalendarBucket_inline(MultiDBTabularInline):
    model = CalendarBucket
    extra = 0
    exclude = ("source",)


class CalendarBucket_admin(MultiDBModelAdmin):
    model = CalendarBucket
    raw_id_fields = ("calendar",)
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("calendar", ("startdate", "enddate"), "value", "priority")}),
        (
            _("repeating pattern"),
            {
                "fields": (
                    ("starttime", "endtime"),
                    (
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ),
                )
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


data_site.register(CalendarBucket, CalendarBucket_admin)


class Calendar_admin(MultiDBModelAdmin):
    model = Calendar
    save_on_top = True
    inlines = [CalendarBucket_inline]
    fieldsets = (
        (None, {"fields": ("name", "defaultvalue")}),
        (
            _("advanced"),
            {
                "fields": ["description", "category", "subcategory"]
                + [a[0] for a in getAttributes(Calendar) if a[3]],
                "classes": ("collapse",),
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
            "name": "messages",
            "label": _("messages"),
            "view": "admin:input_calendar_comment",
        },
    ]


data_site.register(Calendar, Calendar_admin)


class Location_admin(MultiDBModelAdmin):
    model = Location
    raw_id_fields = ("available", "owner")
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("name", "owner")}),
        (
            _("Advanced"),
            {
                "fields": ["description", "category", "subcategory", "available"]
                + [a[0] for a in getAttributes(Location) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Location, Location_admin)


class Customer_admin(MultiDBModelAdmin):
    model = Customer
    raw_id_fields = ("owner",)
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("name", "description", "owner")}),
        (
            _("Advanced"),
            {
                "fields": ["category", "subcategory"]
                + [a[0] for a in getAttributes(Location) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Customer, Customer_admin)


class Supplier_admin(MultiDBModelAdmin):
    model = Supplier
    raw_id_fields = ("available", "owner")
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (
            _("Advanced"),
            {
                "fields": ["category", "subcategory"]
                + [a[0] for a in getAttributes(Supplier) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Supplier, Supplier_admin)


class Item_admin(MultiDBModelAdmin):
    model = Item
    save_on_top = True
    raw_id_fields = ("owner",)
    search_fields = ("name", "description")
    fieldsets = (
        (None, {"fields": ("name", "description", "cost", "owner")}),
        (
            _("Advanced"),
            {
                "fields": ["category", "subcategory", "type"]
                + [a[0] for a in getAttributes(Item) if a[3]],
                "classes": ("collapse",),
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
        {"name": "plan", "label": _("plan"), "view": "output_demand_plandetail"},
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


data_site.register(Item, Item_admin)


class ItemSupplier_admin(MultiDBModelAdmin):
    model = ItemSupplier
    save_on_top = True
    raw_id_fields = ("item", "supplier", "resource")
    fieldsets = (
        (None, {"fields": ("item", "supplier", "location", "leadtime", "cost")}),
        (
            _("Advanced"),
            {
                "fields": [
                    "sizeminimum",
                    "sizemultiple",
                    "sizemaximum",
                    "priority",
                    "fence",
                    "effective_start",
                    "effective_end",
                    "resource",
                    "resource_qty",
                ]
                + [a[0] for a in getAttributes(ItemSupplier) if a[3]],
                "classes": ("collapse",),
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


data_site.register(ItemSupplier, ItemSupplier_admin)


class ItemDistribution_admin(MultiDBModelAdmin):
    model = ItemDistribution
    save_on_top = True
    raw_id_fields = ("item", "resource")
    fieldsets = (
        (None, {"fields": ("item", "location", "origin", "leadtime")}),
        (
            _("Advanced"),
            {
                "fields": [
                    "sizeminimum",
                    "sizemultiple",
                    "sizemaximum",
                    "cost",
                    "priority",
                    "fence",
                    "effective_start",
                    "effective_end",
                    "resource",
                    "resource_qty",
                ]
                + [a[0] for a in getAttributes(ItemDistribution) if a[3]],
                "classes": ("collapse",),
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


data_site.register(ItemDistribution, ItemDistribution_admin)


class Operation_admin(MultiDBModelAdmin):
    model = Operation
    raw_id_fields = ("item", "available", "owner")
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "type",
                    "item",
                    "location",
                    "duration",
                    "duration_per",
                    "owner",
                )
            },
        ),
        (
            _("Advanced"),
            {
                "fields": [
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
                + [a[0] for a in getAttributes(Operation) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Operation, Operation_admin)


class SubOperation_admin(MultiDBModelAdmin):
    model = SubOperation
    raw_id_fields = ("operation", "suboperation")
    save_on_top = True
    exclude = ("source", "id")


data_site.register(SubOperation, SubOperation_admin)


class Buffer_admin(MultiDBModelAdmin):
    model = Buffer
    raw_id_fields = ("location", "item", "minimum_calendar")
    fieldsets = (
        (None, {"fields": ("item", "location", "onhand", "minimum")}),
        (
            _("advanced"),
            {
                "fields": [
                    "batch",
                    "description",
                    "category",
                    "subcategory",
                    "type",
                    "minimum_calendar",
                    "min_interval",
                ]
                + [a[0] for a in getAttributes(Buffer) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Buffer, Buffer_admin)


class SetupRule_admin(MultiDBModelAdmin):
    model = SetupRule
    raw_id_fields = ("setupmatrix",)
    save_on_top = True
    exclude = ("source",)
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


data_site.register(SetupRule, SetupRule_admin)


class SetupMatrix_admin(MultiDBModelAdmin):
    model = SetupMatrix
    save_on_top = True
    exclude = ("source",)
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


data_site.register(SetupMatrix, SetupMatrix_admin)


class Skill_admin(MultiDBModelAdmin):
    model = Skill
    save_on_top = True
    exclude = ("source",)
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


data_site.register(Skill, Skill_admin)


class ResourceSkill_admin(MultiDBModelAdmin):
    model = ResourceSkill
    raw_id_fields = ("resource", "skill")
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("resource", "skill")}),
        (
            _("advanced"),
            {
                "fields": ["priority", "effective_start", "effective_end"]
                + [a[0] for a in getAttributes(ResourceSkill) if a[3]],
                "classes": ("collapse",),
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


data_site.register(ResourceSkill, ResourceSkill_admin)


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
    fieldsets = (
        (None, {"fields": ("name", "location", "type", "maximum")}),
        (
            _("advanced"),
            {
                "fields": [
                    "description",
                    "category",
                    "subcategory",
                    "constrained",
                    "owner",
                    "maximum_calendar",
                    "available",
                    "cost",
                    "maxearly",
                    "setupmatrix",
                    "efficiency",
                    "efficiency_calendar",
                ]
                + [a[0] for a in getAttributes(Resource) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Resource, Resource_admin)


class OperationMaterial_admin(MultiDBModelAdmin):
    model = OperationMaterial
    raw_id_fields = ("operation", "item")
    save_on_top = True
    exclude = ("id",)
    fieldsets = (
        (None, {"fields": ("operation", "item", "type", "quantity")}),
        (
            _("Advanced"),
            {
                "fields": [
                    "quantity_fixed",
                    "transferbatch",
                    "offset",
                    "effective_start",
                    "effective_end",
                    "name",
                    "priority",
                    "search",
                ]
                + [a[0] for a in getAttributes(OperationMaterial) if a[3]],
                "classes": ("collapse",),
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


data_site.register(OperationMaterial, OperationMaterial_admin)


class OperationResource_admin(MultiDBModelAdmin):
    model = OperationResource
    raw_id_fields = ("operation", "resource", "skill")
    save_on_top = True
    exclude = ("id",)
    fieldsets = (
        (None, {"fields": ("operation", "resource", "quantity")}),
        (
            _("Advanced"),
            {
                "fields": [
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
                "classes": ("collapse",),
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


data_site.register(OperationResource, OperationResource_admin)


class ManufacturingOrder_admin(MultiDBModelAdmin):
    model = ManufacturingOrder
    raw_id_fields = ("operation", "owner")
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "reference",
                    "operation",
                    "quantity",
                    "startdate",
                    "enddate",
                    "owner",
                    "status",
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
        "demand",
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
        }
    ]


data_site.register(ManufacturingOrder, ManufacturingOrder_admin)


class DistributionOrder_admin(MultiDBModelAdmin):
    model = DistributionOrder
    raw_id_fields = ("item",)
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
        }
    ]


data_site.register(DistributionOrder, DistributionOrder_admin)


class PurchaseOrder_admin(MultiDBModelAdmin):
    model = PurchaseOrder
    raw_id_fields = ("item", "supplier")
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
        }
    ]


data_site.register(PurchaseOrder, PurchaseOrder_admin)


class DeliveryOrder_admin(MultiDBModelAdmin):
    model = DeliveryOrder
    raw_id_fields = ("item", "demand")
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
        }
    ]


data_site.register(DeliveryOrder, DeliveryOrder_admin)


class Demand_admin(MultiDBModelAdmin):
    model = Demand
    raw_id_fields = ("customer", "item", "operation", "owner")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "item",
                    "location",
                    "customer",
                    "due",
                    "quantity",
                    "priority",
                    "status",
                )
            },
        ),
        (
            _("Advanced"),
            {
                "fields": [
                    "description",
                    "category",
                    "subcategory",
                    "batch",
                    "operation",
                    "minshipment",
                    "maxlateness",
                ]
                + [a[0] for a in getAttributes(Demand) if a[3]],
                "classes": ("collapse",),
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


data_site.register(Demand, Demand_admin)


class OperationPlanResource_admin(MultiDBModelAdmin):
    model = OperationPlanResource
    raw_id_fields = (
        "operationplan",
    )  # TODO a foreign key to OperationPlan doesn't work because it's an abstract class without admin
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("operationplan", "resource", "status")}),
        (_("computed fields"), {"fields": ("quantity", "startdate", "enddate")}),
    )
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:input_operationplanresource_change",
            "permissions": "input.change_operationplanresource",
        }
    ]


data_site.register(OperationPlanResource, OperationPlanResource_admin)


class OperationPlanMaterial_admin(MultiDBModelAdmin):
    model = OperationPlanMaterial
    raw_id_fields = (
        "operationplan",
        "item",
    )  # TODO a foreign key to OperationPlan doesn't work because it's an abstract class without admin
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


data_site.register(OperationPlanMaterial, OperationPlanMaterial_admin)
