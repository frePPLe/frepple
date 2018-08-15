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

from django.utils.translation import ugettext_lazy as _

from freppledb.input.models import Resource, Operation, Location, SetupMatrix, SetupRule
from freppledb.input.models import Buffer, Customer, Demand, Item, OperationResource
from freppledb.input.models import OperationMaterial, Skill, ResourceSkill, Supplier
from freppledb.input.models import Calendar, CalendarBucket, ManufacturingOrder, SubOperation
from freppledb.input.models import ItemSupplier, ItemDistribution, DistributionOrder
from freppledb.input.models import PurchaseOrder, DeliveryOrder
from freppledb.common.adminforms import MultiDBModelAdmin, MultiDBTabularInline

from freppledb.admin import data_site


class CalendarBucket_inline(MultiDBTabularInline):
  model = CalendarBucket
  extra = 0
  exclude = ('source',)


class CalendarBucket_admin(MultiDBModelAdmin):
  model = CalendarBucket
  raw_id_fields = ('calendar',)
  save_on_top = True
  fieldsets = (
    (None, {'fields': ('calendar', ('startdate', 'enddate'), 'value', 'priority')}),
    (_('repeating pattern'), {
      'fields': (('starttime', 'endtime'), ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')),
      }),
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_calendarbucket_change", "permissions": "input.change_calendarbucket"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_calendarbucket_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_calendarbucket_history"},
    ]
data_site.register(CalendarBucket, CalendarBucket_admin)


class Calendar_admin(MultiDBModelAdmin):
  model = Calendar
  save_on_top = True
  inlines = [ CalendarBucket_inline, ]
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_calendar_change", "permissions": "input.change_calendar"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_calendar_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_calendar_history"},
    ]
data_site.register(Calendar, Calendar_admin)


class Location_admin(MultiDBModelAdmin):
  model = Location
  raw_id_fields = ('available', 'owner',)
  save_on_top = True
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_location_change", "permissions": "input.change_location"},
    {"name": 'inboundorders', "label": _("inbound distribution"), "view": "input_distributionorder_in_by_location"},
    {"name": 'outboundorders', "label": _("outbound distribution"), "view": "input_distributionorder_out_by_location"},
    {"name": 'manufacturingorders', "label": _("manufacturing orders"), "view": "input_manufacturingorder_by_location"},
    {"name": 'purchaseorders', "label": _("purchase orders"), "view": "input_purchaseorder_by_location"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_location_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_location_history"},
    ]
data_site.register(Location, Location_admin)


class Customer_admin(MultiDBModelAdmin):
  model = Customer
  raw_id_fields = ('owner',)
  save_on_top = True
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_customer_change", "permissions": "input.change_customer"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_customer_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_customer_history"},
    ]
data_site.register(Customer, Customer_admin)


class ItemSupplier_inline(MultiDBTabularInline):
  model = ItemSupplier
  fk_name = 'item'
  raw_id_fields = ('supplier', 'location', 'resource')
  extra = 0
  exclude = ('source',)


class Supplier_admin(MultiDBModelAdmin):
  model = Supplier
  raw_id_fields = ('owner',)
  save_on_top = True
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_supplier_change", "permissions": "input.change_supplier"},
    {"name": 'purchaseorders', "label": _("purchase orders"), "view": "input_purchaseorder_by_supplier"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_supplier_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_supplier_history"},
    ]
data_site.register(Supplier, Supplier_admin)


class OperationMaterial_inline(MultiDBTabularInline):
  model = OperationMaterial
  fields = ('item', 'operation', 'quantity', 'quantity_fixed', 'type', 'transferbatch', 'effective_start', 'effective_end')
  raw_id_fields = ('operation', 'item',)
  extra = 0
  exclude = ('source',)


class OperationResource_inline(MultiDBTabularInline):
  model = OperationResource
  raw_id_fields = ('operation', 'resource', 'skill')
  fields = ('resource', 'operation', 'quantity', 'effective_start', 'effective_end', 'skill', 'setup', 'search')
  extra = 0
  exclude = ('source',)


class Item_admin(MultiDBModelAdmin):
  model = Item
  save_on_top = True
  raw_id_fields = ('owner',)
  inlines = [ ItemSupplier_inline, OperationMaterial_inline ]
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_item_change", "permissions": "input.change_item"},
    {"name": 'supplypath', "label": _("supply path"), "view": "supplypath_item"},
    {"name": 'whereused', "label": _("where used"), "view": "whereused_item"},
    {"name": 'plan', "label": _("plan"), "view": "output_demand_plandetail"},
    {"name": 'plandetail', "label": _("delivery orders"), "view": "input_deliveryorder_by_item"},
    {"name": 'purchaseorders', "label": _("purchase orders"), "view": "input_purchaseorder_by_item"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_item_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_item_history"},
    ]
data_site.register(Item, Item_admin)


class ItemSupplier_admin(MultiDBModelAdmin):
  model = ItemSupplier
  save_on_top = True
  raw_id_fields = ('item', 'supplier', 'resource')
  exclude = ('source', 'id')
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_itemsupplier_change", "permissions": "input.change_itemsupplier"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_itemsupplier_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_itemsupplier_history"},
    ]
data_site.register(ItemSupplier, ItemSupplier_admin)


class ItemDistribution_admin(MultiDBModelAdmin):
  model = ItemDistribution
  save_on_top = True
  raw_id_fields = ('item', 'resource')
  exclude = ('source', 'id')
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_itemdistribution_change", "permissions": "input.change_itemdistribution"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_itemdistribution_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_itemdistribution_history"},
  ]
data_site.register(ItemDistribution, ItemDistribution_admin)


class SubOperation_inline(MultiDBTabularInline):
  model = SubOperation
  fk_name = 'operation'
  extra = 1
  raw_id_fields = ('suboperation',)
  exclude = ('source',)


class ResourceSkill_inline(MultiDBTabularInline):
  model = ResourceSkill
  fk_name = 'resource'
  raw_id_fields = ('skill',)
  extra = 1
  exclude = ('source',)


class Operation_admin(MultiDBModelAdmin):
  model = Operation
  raw_id_fields = ('location', 'item', 'available')
  save_on_top = True
  inlines = [ SubOperation_inline, OperationMaterial_inline, OperationResource_inline, ]
  fieldsets = (
    (None, {'fields': ('name', 'type', 'item', 'location', 'description', 'category', 'subcategory')}),
    (_('planning parameters'), {
      'fields': (
        'fence', 'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum', 'cost',
        'duration', 'duration_per', 'available', 'effective_start', 'effective_end', 'search'
        ),
       }),
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_operation_change", "permissions": "input.change_operation"},
    {"name": 'supplypath', "label": _("supply path"), "view": "supplypath_operation"},
    {"name": 'whereused', "label": _("where used"),"view": "whereused_operation"},
    {"name": 'plan', "label": _("plan"), "view": "output_operation_plandetail"},
    # {"name": 'plandetail', "label": _("plan detail"), "view": "output_operationplan_plandetail"},
    {"name": 'constraint', "label": _("constrained demand"), "view": "output_constraint_operation"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_operation_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_operation_history"},
  ]
data_site.register(Operation, Operation_admin)


class SubOperation_admin(MultiDBModelAdmin):
  model = SubOperation
  raw_id_fields = ('operation', 'suboperation')
  save_on_top = True
  exclude = ('source', 'id')
data_site.register(SubOperation, SubOperation_admin)


class Buffer_admin(MultiDBModelAdmin):
  raw_id_fields = ('location', 'item', 'minimum_calendar', )
  fieldsets = (
    (None, {
      'fields': ('item', 'location', 'description', 'category', 'subcategory')}),
    (_('inventory'), {
      'fields': ('onhand',)
      }),
    (_('planning parameters'), {
      'fields': ('type', 'minimum', 'minimum_calendar', 'min_interval'),
      }),
    )
  save_on_top = True
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_buffer_change", "permissions": "input.change_buffer"},
    {"name": 'supplypath', "label": _("supply path"), "view": "supplypath_buffer"},
    {"name": 'whereused', "label": _("where used"),"view": "whereused_buffer"},
    {"name": 'plan', "label": _("plan"), "view": "output_buffer_plandetail"},
    {"name": 'plandetail', "label": _("plan detail"), "view": "output_flowplan_plandetail"},
    {"name": 'constraint', "label": _("constrained demand"), "view": "output_constraint_buffer"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_buffer_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_buffer_history"},
    ]
data_site.register(Buffer, Buffer_admin)


class SetupRule_inline(MultiDBTabularInline):
  model = SetupRule
  extra = 3
  exclude = ('source',)


class SetupRule_admin(MultiDBModelAdmin):
  model = SetupRule
  raw_id_fields = ('setupmatrix',)
  save_on_top = True
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_setuprule_change", "permissions": "input.change_setuprule"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_setuprule_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_setuprule_history"},
    ]
data_site.register(SetupRule, SetupRule_admin)


class SetupMatrix_admin(MultiDBModelAdmin):
  model = SetupMatrix
  save_on_top = True
  inlines = [ SetupRule_inline, ]
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_setupmatrix_change", "permissions": "input.change_setupmatrix"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_setupmatrix_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_setupmatrix_history"},
    ]
data_site.register(SetupMatrix, SetupMatrix_admin)


class Skill_admin(MultiDBModelAdmin):
  model = Skill
  save_on_top = True
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_skill_change", "permissions": "input.change_skill"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_skill_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_skill_history"},
    ]
data_site.register(Skill, Skill_admin)


class ResourceSkill_admin(MultiDBModelAdmin):
  model = ResourceSkill
  raw_id_fields = ('resource', 'skill')
  save_on_top = True
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_resourceskill_change", "permissions": "input.change_resoureskill"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_resourceskill_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_resourceskill_history"},
    ]
data_site.register(ResourceSkill, ResourceSkill_admin)


class Resource_admin(MultiDBModelAdmin):
  model = Resource
  raw_id_fields = ('maximum_calendar', 'location', 'setupmatrix', 'owner', 'available', 'efficiency_calendar')
  save_on_top = True
  inlines = [ OperationResource_inline, ResourceSkill_inline, ]
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_resource_change", "permissions": "input.change_resource"},
    {"name": 'supplypath', "label": _("supply path"), "view": "supplypath_resource"},
    {"name": 'whereused', "label": _("where used"), "view": "whereused_resource"},
    {"name": 'plan', "label": _("plan"), "view": "output_resource_plandetail"},
    {"name": 'plandetail', "label": _("plan detail"), "view": "output_loadplan_plandetail"},
    {"name": 'constraint', "label": _("constrained demand"), "view": "output_constraint_resource"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_resource_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_resource_history"},
    ]
data_site.register(Resource, Resource_admin)


class OperationMaterial_admin(MultiDBModelAdmin):
  model = OperationMaterial
  raw_id_fields = ('operation', 'item',)
  save_on_top = True
  exclude = ('id',)
  fieldsets = (
    (None, {'fields': ('item', 'operation', 'type', 'quantity', 'quantity_fixed', 'transferbatch', ('effective_start', 'effective_end'))}),
    (_('alternates'), {'fields': ('name', 'priority', 'search'), }),
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_operationmaterial_change", "permissions": "input.change_operationmaterial"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_operationmaterial_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_operationmaterial_history"},
    ]
data_site.register(OperationMaterial, OperationMaterial_admin)


class OperationResource_admin(MultiDBModelAdmin):
  model = OperationResource
  raw_id_fields = ('operation', 'resource', 'skill')
  save_on_top = True
  exclude = ('id',)
  fieldsets = (
    (None, {'fields': ('resource', 'operation', 'quantity', 'skill', 'setup', ('effective_start', 'effective_end'))}),
    (_('alternates'), {'fields': ('name', 'priority', 'search'), }),
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_operationresource_change", "permissions": "input.change_operationresource"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_operationresource_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_operationresource_history"},
    ]
data_site.register(OperationResource, OperationResource_admin)


class ManufacturingOrder_admin(MultiDBModelAdmin):
  model = ManufacturingOrder
  raw_id_fields = ('operation', 'owner',)
  save_on_top = True
  fieldsets = (
    (None, {
      'fields': ('reference', 'operation', 'quantity', 'startdate', 'enddate', 'owner', 'status', )}),
    )
  exclude = (
    'type', 'source', 'criticality', 'delay', 'origin', 'destination',
    'item', 'supplier', 'location', 'demand', 'name', 'due', 'color'
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_manufacturingorder_change", "permissions": "input.change_manufacturingorder"},
    ]
data_site.register(ManufacturingOrder, ManufacturingOrder_admin)


class DistributionOrder_admin(MultiDBModelAdmin):
  model = DistributionOrder
  raw_id_fields = ('item',)
  save_on_top = True
  fieldsets = (
    (None, {
      'fields': ('reference', 'item', 'origin', 'destination', 'quantity', 'shipping_date', 'receipt_date', 'status', )}),
    )
  exclude = (
    'type', 'source', 'criticality', 'delay', 'operation', 'owner', 'color',
    'supplier', 'location', 'demand', 'name', 'due', 'startdate', 'enddate'
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_distributionorder_change", "permissions": "input.change_distributionorder"},
    ]
data_site.register(DistributionOrder, DistributionOrder_admin)


class PurchaseOrder_admin(MultiDBModelAdmin):
  model = PurchaseOrder
  raw_id_fields = ('item', 'supplier',)  
  save_on_top = True
  fieldsets = (
    (None, {
      'fields': ('reference', 'item', 'location', 'supplier', 'quantity', 'ordering_date', 'receipt_date', 'status', )}),
    )
  exclude = (
    'type', 'source', 'criticality', 'delay', 'operation', 'owner', 'color',
    'origin', 'destination', 'demand', 'name', 'due', 'startdate', 'enddate'
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_purchaseorder_change", "permissions": "input.change_purchaseorder"},
    ]
data_site.register(PurchaseOrder, PurchaseOrder_admin)


class DeliveryOrder_admin(MultiDBModelAdmin):
  model = DeliveryOrder
  raw_id_fields = ('item', 'demand')
  save_on_top = True
  fieldsets = (
    (None, {
      'fields': ('reference', 'demand', 'item', 'location', 'quantity', 'status', )}),
    )
  exclude = (
    'type', 'source', 'criticality', 'delay', 'operation', 'owner', 'color'
    'origin', 'destination', 'name', 'due', 'startdate', 'enddate', 'supplier'
    )
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_deliveryorder_change", "permissions": "input.change_deliveryorder"},
    ]
data_site.register(DeliveryOrder, DeliveryOrder_admin)


class Demand_admin(MultiDBModelAdmin):
  model = Demand
  raw_id_fields = ('customer', 'item', 'operation', 'owner',)
  fieldsets = (
    (None, {'fields': (
      'name', 'item', 'location', 'customer', 'description', 'category',
      'subcategory', 'due', 'quantity', 'priority', 'status', 'owner'
      )}),
    (_('planning parameters'), {'fields': (
      'operation', 'minshipment', 'maxlateness'
      )}),
    )
  save_on_top = True
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:input_demand_change", "permissions": "input.change_demand"},
    {"name": 'supplypath', "label": _("supply path"), "view": "supplypath_demand"},
    {"name": 'constraint', "label": _("why short or late?"), "view": "output_constraint_demand"},
    {"name": 'plan', "label": _("plan"), "view": "output_demand_pegging"},
    {"name": 'comments', "label": _("comments"), "view": "admin:input_demand_comment"},
    #. Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:input_demand_history"},
    ]
data_site.register(Demand, Demand_admin)
