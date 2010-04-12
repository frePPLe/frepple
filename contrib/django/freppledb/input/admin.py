#
# Copyright (C) 2007 by Johan De Taeye
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

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from freppledb.input.models import *
from freppledb.admin import site


class Plan_admin(admin.ModelAdmin):
  model = Plan
  save_on_top = True
site.register(Plan,Plan_admin)


class Bucket_inline(admin.TabularInline):
  model = Bucket
  extra = 3


class Calendar_admin(admin.ModelAdmin):
  model = Calendar
  save_on_top = True
  save_as = True
  inlines = [ Bucket_inline, ]
site.register(Calendar,Calendar_admin)


class Location_admin(admin.ModelAdmin):
  model = Location
  raw_id_fields = ('available', 'owner',)
  save_on_top = True
  save_as = True
site.register(Location,Location_admin)


class Customer_admin(admin.ModelAdmin):
  model = Customer
  raw_id_fields = ('owner',)
  save_on_top = True
  save_as = True
site.register(Customer,Customer_admin)


class Item_admin(admin.ModelAdmin):
  model = Item
  save_as = True
  save_on_top = True
  raw_id_fields = ('operation', 'owner',)
site.register(Item,Item_admin)


class SubOperation_inline(admin.TabularInline):
  model = SubOperation
  fk_name = 'operation'
  extra = 1
  raw_id_fields = ('suboperation',)


class Flow_inline(admin.TabularInline):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  extra = 1


class Load_inline(admin.TabularInline):
  model = Load
  raw_id_fields = ('operation', 'resource',)
  extra = 1
  

class Operation_admin(admin.ModelAdmin):
  model = Operation
  raw_id_fields = ('location',)
  save_on_top = True
  save_as = True
  inlines = [ SubOperation_inline, ]
  # TODO inlines = [ SubOperation_inline, Flow_inline, Load_inline, ]
  fieldsets = (
          (None, {'fields': ('name', 'type', 'location', 'description', ('category', 'subcategory'))}),
          (_('Planning parameters'), {
             'fields': ('fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum', 'cost', 'duration', 'duration_per','search'),
             'classes': ('collapse',)
             }),
      )
site.register(Operation,Operation_admin)


class SubOperation_admin(admin.ModelAdmin):
  model = SubOperation
  raw_id_fields = ('operation', 'suboperation',)
  save_on_top = True
site.register(SubOperation,SubOperation_admin)


class Buffer_admin(admin.ModelAdmin):
  raw_id_fields = ('location', 'item', 'minimum', 'producing', )
  fieldsets = (
            (None,{
              'fields': (('name'), ('item', 'location'), 'description', ('category', 'subcategory'))}),
            (_('Inventory'), {
              'fields': ('onhand',)}),
            (_('Planning parameters'), {
              'fields': ('type','minimum','producing','carrying_cost'),
              'classes': ('collapse',)},),
            (_('Planning parameters for procurement buffers'), {
              'fields': ('leadtime','fence','min_inventory','max_inventory','min_interval','max_interval','size_minimum','size_multiple','size_maximum'),
              'classes': ('collapse',)},),
        )
  save_as = True
  save_on_top = True
  #TODO inlines = [ Flow_inline, ]
site.register(Buffer,Buffer_admin)


class SetupRule_inline(admin.TabularInline):
  model = SetupRule
  extra = 3


class SetupMatrix_admin(admin.ModelAdmin):
  model = SetupMatrix
  save_as = True
  save_on_top = True
  inlines = [ SetupRule_inline, ]
site.register(SetupMatrix,SetupMatrix_admin)


class Resource_admin(admin.ModelAdmin):
  model = Resource
  raw_id_fields = ('maximum', 'location', 'setupmatrix')
  save_as = True
  save_on_top = True
  # TODO inlines = [ Load_inline, ]
site.register(Resource,Resource_admin)


class Flow_admin(admin.ModelAdmin):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  save_on_top = True
  save_as = True
site.register(Flow,Flow_admin)


class Load_admin(admin.ModelAdmin):
  model = Load
  raw_id_fields = ('operation', 'resource',)
  save_on_top = True
  save_as = True
site.register(Load,Load_admin)


class OperationPlan_admin(admin.ModelAdmin):
  model = OperationPlan
  raw_id_fields = ('operation',)
  save_on_top = True
  save_as = True
site.register(OperationPlan,OperationPlan_admin)


class Demand_admin(admin.ModelAdmin):
  model = Demand
  raw_id_fields = ('customer', 'item', 'operation', 'owner',)
  fieldsets = (
            (None, {'fields': ('name', 'item', 'customer', 'description', 'category','subcategory', 'due', 'quantity', 'priority','owner')}),
            (_('Planning parameters'), {'fields': ('operation', 'minshipment', 'maxlateness'), 'classes': ('collapse')}),
        )
  radio_fields = {'priority': admin.HORIZONTAL, }
  save_on_top = True
  save_as = True
site.register(Demand,Demand_admin)


class ForecastDemand_inline(admin.TabularInline):
  model = ForecastDemand
  extra = 5


class Forecast_admin(admin.ModelAdmin):
  model = Forecast
  raw_id_fields = ('customer', 'item', 'calendar', 'operation')
  fieldsets = (
            (None, {'fields': ('name', 'item', 'customer', 'calendar', 'description', 'category','subcategory', 'priority')}),
            (_('Planning parameters'), {'fields': ('discrete', 'operation', 'minshipment', 'maxlateness'), 'classes': ('collapse')}),
        )
  radio_fields = {'priority': admin.HORIZONTAL, }
  inlines = [ ForecastDemand_inline, ]
  save_on_top = True
  save_as = True
site.register(Forecast,Forecast_admin)


class Dates_admin(admin.ModelAdmin):
  model = Dates
  fieldsets = (
      (None, {'fields': (('day','day_start','day_end'),
                         'dayofweek',
                         ('week','week_start','week_end'),
                         ('month','month_start','month_end'),
                         ('quarter','quarter_start','quarter_end'),
                         ('year','year_start','year_end'),
                         ('standard','standard_start','standard_end'),
                         )}),
      )
site.register(Dates,Dates_admin)
