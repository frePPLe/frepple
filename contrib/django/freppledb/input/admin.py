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
from freppledb.input.models import Buffer, Customer, Demand, Item, Load, Flow, Skill, ResourceSkill
from freppledb.input.models import Calendar, CalendarBucket, OperationPlan, SubOperation, Supplier
from freppledb.input.models import ItemSupplier, ItemDistribution, DistributionOrder, PurchaseOrder
from freppledb.common.adminforms import MultiDBModelAdmin, MultiDBTabularInline

import freppledb.input.views
import freppledb.output.views.pegging
import freppledb.output.views.demand
import freppledb.output.views.buffer
import freppledb.output.views.constraint
import freppledb.output.views.operation
import freppledb.output.views.resource
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
    (_('Repeating pattern'), {
      'fields': (('starttime', 'endtime'), ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')),
      }),
    )
CalendarBucket_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view":  CalendarBucket_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": CalendarBucket_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": CalendarBucket_admin.history_view, "permission": ''},
  ]
data_site.register(CalendarBucket, CalendarBucket_admin)


class Calendar_admin(MultiDBModelAdmin):
  model = Calendar
  save_on_top = True
  inlines = [ CalendarBucket_inline, ]
  exclude = ('source',)
Calendar_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view":  Calendar_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Calendar_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Calendar_admin.history_view, "permission": ''},
  ]
data_site.register(Calendar, Calendar_admin)


class Location_admin(MultiDBModelAdmin):
  model = Location
  raw_id_fields = ('available', 'owner',)
  save_on_top = True
  exclude = ('source',)
Location_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Calendar_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Location_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Location_admin.history_view, "permission": ''},
  ]
data_site.register(Location, Location_admin)


class Customer_admin(MultiDBModelAdmin):
  model = Customer
  raw_id_fields = ('owner',)
  save_on_top = True
  exclude = ('source',)
Customer_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Customer_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Customer_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Customer_admin.history_view, "permission": ''},
  ]
data_site.register(Customer, Customer_admin)


class ItemSupplier_inline(MultiDBTabularInline):
  model = ItemSupplier
  fk_name = 'item'
  raw_id_fields = ('supplier','location')
  extra = 0
  exclude = ('source',)



class Supplier_admin(MultiDBModelAdmin):
  model = Supplier
  raw_id_fields = ('owner',)
  save_on_top = True
  exclude = ('source',)
Supplier_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Supplier_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Supplier_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Supplier_admin.history_view, "permission": ''},
  ]
data_site.register(Supplier, Supplier_admin)




class Item_admin(MultiDBModelAdmin):
  model = Item
  save_on_top = True
  raw_id_fields = ('operation', 'owner',)
  inlines = [ ItemSupplier_inline, ]
  exclude = ('source',)
Item_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Item_admin.change_view, "permission": ''},
    {"name": 'supplypath', "label": _("supply path"), "view": freppledb.input.views.UpstreamItemPath, "permission": ''},
    {"name": 'whereused', "label": _("where used"),"view": freppledb.input.views.DownstreamItemPath, "permission": ''},
    {"name": 'plan', "label": _("plan"), "view": freppledb.output.views.demand.OverviewReport, "permission": ''},
    {"name": 'plandetail', "label": _("plandetails"), "view": freppledb.output.views.demand.DetailReport, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Item_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Item_admin.history_view, "permission": ''},
  ]
data_site.register(Item, Item_admin)


class ItemSupplier_admin(MultiDBModelAdmin):
  model = ItemSupplier
  save_on_top = True
  raw_id_fields = ('item', 'supplier')
  exclude = ('source',)
ItemSupplier_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": ItemSupplier_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": ItemSupplier_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": ItemSupplier_admin.history_view, "permission": ''},
  ]
data_site.register(ItemSupplier, ItemSupplier_admin)


class ItemDistribution_admin(MultiDBModelAdmin):
  model = ItemDistribution
  save_on_top = True
  raw_id_fields = ('item',)
  exclude = ('source',)
ItemDistribution_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": ItemDistribution_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": ItemDistribution_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": ItemDistribution_admin.history_view, "permission": ''},
  ]
data_site.register(ItemDistribution, ItemDistribution_admin)


class SubOperation_inline(MultiDBTabularInline):
  model = SubOperation
  fk_name = 'operation'
  extra = 1
  raw_id_fields = ('suboperation',)
  exclude = ('source',)


class Flow_inline(MultiDBTabularInline):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  extra = 0
  exclude = ('source',)


class Load_inline(MultiDBTabularInline):
  model = Load
  raw_id_fields = ('operation', 'resource', 'skill')
  fields = ('resource', 'operation', 'quantity', 'effective_start', 'effective_end', 'skill', 'setup')
  sfieldsets = (
    (None, {'fields': ['resource', 'operation', 'quantity', 'effective_start', 'effective_end', 'skill', 'setup']}),
    (_('Alternates'), {'fields': ('name', 'alternate', 'priority', 'search')}),
    )
  extra = 0
  exclude = ('source',)


class ResourceSkill_inline(MultiDBTabularInline):
  model = ResourceSkill
  fk_name = 'resource'
  raw_id_fields = ('skill',)
  extra = 1
  exclude = ('source',)


class Operation_admin(MultiDBModelAdmin):
  model = Operation
  raw_id_fields = ('location',)
  save_on_top = True
  inlines = [ SubOperation_inline, Flow_inline, Load_inline, ]
  fieldsets = (
    (None, {'fields': ('name', 'type', 'location', 'description', ('category', 'subcategory'))}),
    (_('Planning parameters'), {
      'fields': ('fence', 'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum', 'cost', 'duration', 'duration_per', 'search'),
        'classes': ('collapse',)
       }),
    )
Operation_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Operation_admin.change_view, "permission": ''},
    {"name": 'supplypath', "label": _("supply path"), "view":  freppledb.input.views.UpstreamOperationPath, "permission": ''},
    {"name": 'whereused', "label": _("where used"),"view": freppledb.input.views.DownstreamOperationPath, "permission": ''},
    {"name": 'plan', "label": _("plan"), "view": freppledb.output.views.operation.OverviewReport, "permission": ''},
    {"name": 'plandetail', "label": _("plandetails"), "view": freppledb.output.views.operation.DetailReport, "permission": ''},
    {"name": 'constraint', "label": _("constrained demand"), "view": freppledb.output.views.constraint.ReportByOperation, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Operation_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Operation_admin.history_view, "permission": ''},
  ]
data_site.register(Operation, Operation_admin)


class SubOperation_admin(MultiDBModelAdmin):
  model = SubOperation
  raw_id_fields = ('operation', 'suboperation',)
  save_on_top = True
  exclude = ('source',)
data_site.register(SubOperation, SubOperation_admin)


class Buffer_admin(MultiDBModelAdmin):
  raw_id_fields = ('location', 'item', 'minimum_calendar', 'producing', 'owner', )
  fieldsets = (
    (None, {
      'fields': (('name'), ('item', 'location'), 'description', 'owner', ('category', 'subcategory'))}),
    (_('Inventory'), {
      'fields': ('onhand',)}),
    (_('Planning parameters'), {
      'fields': ('type', 'minimum', 'minimum_calendar', 'producing'),
      'classes': ('collapse',)},),
    (_('Planning parameters for procurement buffers'), {
      'fields': ('leadtime', 'fence', 'min_inventory', 'max_inventory', 'min_interval', 'max_interval', 'size_minimum', 'size_multiple', 'size_maximum'),
      'classes': ('collapse',)},),
    )
  save_on_top = True
  inlines = [ Flow_inline, ]
Buffer_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Buffer_admin.change_view, "permission": ''},
    {"name": 'supplypath', "label": _("supply path"), "view": freppledb.input.views.UpstreamBufferPath, "permission": ''},
    {"name": 'whereused', "label": _("where used"),"view": freppledb.input.views.DownstreamBufferPath, "permission": ''},
    {"name": 'plan', "label": _("plan"), "view": freppledb.output.views.buffer.OverviewReport, "permission": ''},
    {"name": 'plandetail', "label": _("plandetails"), "view": freppledb.output.views.buffer.DetailReport, "permission": ''},
    {"name": 'constraint', "label": _("constrained demand"), "view": freppledb.output.views.constraint.ReportByBuffer, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Buffer_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Buffer_admin.history_view, "permission": ''},
  ]
data_site.register(Buffer, Buffer_admin)


class SetupRule_inline(MultiDBTabularInline):
  model = SetupRule
  extra = 3
  exclude = ('source',)


class SetupMatrix_admin(MultiDBModelAdmin):
  model = SetupMatrix
  save_on_top = True
  inlines = [ SetupRule_inline, ]
  exclude = ('source',)
SetupMatrix_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": SetupMatrix_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": SetupMatrix_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": SetupMatrix_admin.history_view, "permission": ''},
  ]
data_site.register(SetupMatrix, SetupMatrix_admin)


class Skill_admin(MultiDBModelAdmin):
  model = Skill
  save_on_top = True
  exclude = ('source',)
Skill_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Skill_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Skill_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Skill_admin.history_view, "permission": ''},
  ]
data_site.register(Skill, Skill_admin)


class ResourceSkill_admin(MultiDBModelAdmin):
  model = ResourceSkill
  raw_id_fields = ('resource', 'skill')
  save_on_top = True
  exclude = ('source',)
ResourceSkill_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": ResourceSkill_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": ResourceSkill_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": ResourceSkill_admin.history_view, "permission": ''},
  ]
data_site.register(ResourceSkill, ResourceSkill_admin)


class Resource_admin(MultiDBModelAdmin):
  model = Resource
  raw_id_fields = ('maximum_calendar', 'location', 'setupmatrix', 'owner')
  save_on_top = True
  inlines = [ Load_inline, ResourceSkill_inline, ]
  exclude = ('source',)
Resource_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Resource_admin.change_view, "permission": ''},
    {"name": 'supplypath', "label": _("supply path"), "view": freppledb.input.views.UpstreamResourcePath, "permission": ''},
    {"name": 'whereused', "label": _("where used"),"view": freppledb.input.views.DownstreamResourcePath, "permission": ''},
    {"name": 'plan', "label": _("plan"), "view": freppledb.output.views.resource.OverviewReport, "permission": ''},
    {"name": 'gantt', "label": _("gantt chart"), "view": freppledb.output.views.resource.GanttReport, "permission": ''},
    {"name": 'plandetail', "label": _("plandetails"), "view": freppledb.output.views.resource.DetailReport, "permission": ''},
    {"name": 'constraint', "label": _("constrained demand"), "view": freppledb.output.views.constraint.ReportByResource, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Resource_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Resource_admin.history_view, "permission": ''},
  ]
data_site.register(Resource, Resource_admin)


class Flow_admin(MultiDBModelAdmin):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  save_on_top = True
  fieldsets = (
    (None, {'fields': ('thebuffer', 'operation', 'type', 'quantity', ('effective_start', 'effective_end'))}),
    (_('Alternates'), {
       'fields': ('name', 'alternate', 'priority', 'search'),
       }),
    )
Flow_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Flow_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Item_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Flow_admin.history_view, "permission": ''},
  ]
data_site.register(Flow, Flow_admin)


class Load_admin(MultiDBModelAdmin):
  model = Load
  raw_id_fields = ('operation', 'resource', 'skill')
  save_on_top = True
  fieldsets = (
    (None, {'fields': ('resource', 'operation', 'quantity', 'skill', 'setup', ('effective_start', 'effective_end'))}),
    (_('Alternates'), {
       'fields': ('name', 'alternate', 'priority', 'search'),
       }),
    )
Load_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Load_admin.change_view, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Load_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Load_admin.history_view, "permission": ''},
  ]
data_site.register(Load, Load_admin)


class OperationPlan_admin(MultiDBModelAdmin):
  model = OperationPlan
  raw_id_fields = ('operation', 'owner',)
  save_on_top = True
  exclude = ('source', 'criticality')
data_site.register(OperationPlan, OperationPlan_admin)
OperationPlan_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": OperationPlan_admin.change_view, "permission": ''},
    {"name": 'supplypath', "label": _("supply path"), "view": freppledb.input.views.UpstreamOperationPath, "permission": ''},
    {"name": 'whereused', "label": _("where used"),"view": freppledb.input.views.DownstreamOperationPath, "permission": ''},
    {"name": 'plan', "label": _("plan"), "view": freppledb.output.views.operation.OverviewReport, "permission": ''},
    {"name": 'plandetail', "label": _("plandetails"), "view": freppledb.output.views.operation.DetailReport, "permission": ''},
    {"name": 'constraint', "label": _("constrained operation"), "view": freppledb.output.views.constraint.ReportByOperation, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": OperationPlan_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": OperationPlan_admin.history_view, "permission": ''},
  ]

class DistributionOrder_admin(MultiDBModelAdmin):
  model = DistributionOrder
  raw_id_fields = ('item',)
  save_on_top = True
  exclude = ('source', 'criticality')
data_site.register(DistributionOrder, DistributionOrder_admin)


class PurchaseOrder_admin(MultiDBModelAdmin):
  model = PurchaseOrder
  raw_id_fields = ('item', 'supplier',)
  save_on_top = True
  exclude = ('source', 'criticality')
data_site.register(PurchaseOrder, PurchaseOrder_admin)


class Demand_admin(MultiDBModelAdmin):
  model = Demand
  raw_id_fields = ('customer', 'item', 'operation', 'owner',)
  fieldsets = (
    (None, {'fields': (
      'name', 'item', 'location', 'customer', 'description', 'category',
      'subcategory', 'due', 'quantity', 'priority', 'status', 'owner'
      )}),
    (_('Planning parameters'), {'fields': (
      'operation', 'minshipment', 'maxlateness'
      ), 'classes': ('collapse') }),
    )
  save_on_top = True
Demand_admin.tabs = [
    {"name": 'edit', "label": _("edit"), "view": Demand_admin.change_view, "permission": ''},
    {"name": 'supplypath', "label": _("supply path"), "view": freppledb.input.views.UpstreamDemandPath, "permission": ''},
    {"name": 'constraint', "label": _("why short or late?"),"view": freppledb.output.views.constraint.ReportByDemand, "permission": ''},
    {"name": 'plan', "label": _("plan"), "view": freppledb.output.views.pegging.ReportByDemand, "permission": ''},
    {"name": 'comments', "label": _("comments"), "view": Demand_admin.comment_view, "permission": ''},
    {"name": 'history', "label": _("history"), "view": Demand_admin.history_view, "permission": ''},
  ]
data_site.register(Demand, Demand_admin)
