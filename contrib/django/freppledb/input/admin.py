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
from freppledb.admin import data_site
from freppledb.common.adminforms import MultiDBModelAdmin, MultiDBTabularInline


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
data_site.register(CalendarBucket, CalendarBucket_admin)


class Calendar_admin(MultiDBModelAdmin):
  model = Calendar
  save_on_top = True
  inlines = [ CalendarBucket_inline, ]
  exclude = ('source',)
data_site.register(Calendar, Calendar_admin)


class Location_admin(MultiDBModelAdmin):
  model = Location
  raw_id_fields = ('available', 'owner',)
  save_on_top = True
  exclude = ('source',)
data_site.register(Location, Location_admin)


class Customer_admin(MultiDBModelAdmin):
  model = Customer
  raw_id_fields = ('owner',)
  save_on_top = True
  exclude = ('source',)
data_site.register(Customer, Customer_admin)


class Supplier_admin(MultiDBModelAdmin):
  model = Supplier
  raw_id_fields = ('owner',)
  save_on_top = True
  exclude = ('source',)
data_site.register(Supplier, Supplier_admin)


class Item_admin(MultiDBModelAdmin):
  model = Item
  save_on_top = True
  raw_id_fields = ('operation', 'owner',)
  exclude = ('source',)
data_site.register(Item, Item_admin)


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
      'fields': ('type', 'minimum', 'minimum_calendar', 'producing', 'carrying_cost'),
      'classes': ('collapse',)},),
    (_('Planning parameters for procurement buffers'), {
      'fields': ('leadtime', 'fence', 'min_inventory', 'max_inventory', 'min_interval', 'max_interval', 'size_minimum', 'size_multiple', 'size_maximum'),
      'classes': ('collapse',)},),
    )
  save_on_top = True
  inlines = [ Flow_inline, ]
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
data_site.register(SetupMatrix, SetupMatrix_admin)


class Skill_admin(MultiDBModelAdmin):
  model = Skill
  save_on_top = True
  exclude = ('source',)
data_site.register(Skill, Skill_admin)


class ResourceSkill_admin(MultiDBModelAdmin):
  model = ResourceSkill
  raw_id_fields = ('resource', 'skill')
  save_on_top = True
  exclude = ('source',)
data_site.register(ResourceSkill, ResourceSkill_admin)


class Resource_admin(MultiDBModelAdmin):
  model = Resource
  raw_id_fields = ('maximum_calendar', 'location', 'setupmatrix', 'owner')
  save_on_top = True
  inlines = [ Load_inline, ResourceSkill_inline, ]
  exclude = ('source',)
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
data_site.register(Load, Load_admin)



class OperationPlan_admin(MultiDBModelAdmin):
  model = OperationPlan
  raw_id_fields = ('operation', 'owner',)
  save_on_top = True
  exclude = ('source',)
data_site.register(OperationPlan, OperationPlan_admin)


class Demand_admin(MultiDBModelAdmin):
  model = Demand
  raw_id_fields = ('customer', 'item', 'operation', 'owner',)
  fieldsets = (
    (None, {'fields': ('name', 'item', 'customer', 'description', 'category', 'subcategory', 'due', 'quantity', 'priority', 'status', 'owner')}),
    (_('Planning parameters'), {'fields': ('operation', 'minshipment', 'maxlateness'), 'classes': ('collapse')}),
    )
  save_on_top = True
data_site.register(Demand, Demand_admin)
