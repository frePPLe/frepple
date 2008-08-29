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
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from freppledb.input.models import *


site = admin.sites.AdminSite()


class Plan_admin(admin.ModelAdmin):
  model = Plan
site.register(Plan,Plan_admin)


class Dates_admin(admin.ModelAdmin):
  model = Dates
  fieldsets = (
      (None, {'fields': (('day','day_start','day_end'),
                         'dayofweek',
                         ('week','week_start','week_end'),
                         ('month','month_start','month_end'),
                         ('quarter','quarter_start','quarter_end'),
                         ('year','year_start','year_end'),
                         ('default','default_start','default_end'),
                         )}),
      )
site.register(Dates,Dates_admin)


class Bucket_inline(admin.TabularInline):
  model = Bucket
  extra = 3


class Calendar_admin(admin.ModelAdmin):
  model = Calendar
  save_as = True
  inlines = [ Bucket_inline, ]
site.register(Calendar,Calendar_admin)


class Location_admin(admin.ModelAdmin):
  model = Location
  raw_id_fields = ('available', 'owner',)
  save_as = True
site.register(Location,Location_admin)


class Customer_admin(admin.ModelAdmin):
  model = Customer
  raw_id_fields = ('owner',)
  save_as = True
site.register(Customer,Customer_admin)


class Item_admin(admin.ModelAdmin):
  model = Item
  save_as = True
  raw_id_fields = ('operation', 'owner',)
site.register(Item,Item_admin)


class SubOperation_inline(admin.TabularInline):
  model = SubOperation
  fk_name = 'operation'
  extra = 3
  raw_id_fields = ('suboperation',)


class Operation_admin(admin.ModelAdmin):
  model = Operation
  raw_id_fields = ('location',)
  save_as = True
  inlines = [ SubOperation_inline, ]
  fieldsets = (
          (None, {'fields': ('name', 'type', 'location')}),
          (_('Planning parameters'), {
             'fields': ('fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'cost', 'duration', 'duration_per'),
             'classes': ('collapse',)
             }),
      )
site.register(Operation,Operation_admin)


class SubOperation_admin(admin.ModelAdmin):
  model = SubOperation
  raw_id_fields = ('operation', 'suboperation',)
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
site.register(Buffer,Buffer_admin)


class Resource_admin(admin.ModelAdmin):
  model = Resource
  raw_id_fields = ('maximum', 'location',)
  save_as = True
site.register(Resource,Resource_admin)


class Flow_admin(admin.ModelAdmin):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  save_as = True
site.register(Flow,Flow_admin)


class Load_admin(admin.ModelAdmin):
  model = Load
  raw_id_fields = ('operation', 'resource',)
  save_as = True
site.register(Load,Load_admin)


class OperationPlan_admin(admin.ModelAdmin):
  model = OperationPlan
  raw_id_fields = ('operation',)
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
  save_as = True
site.register(Forecast,Forecast_admin)


# Register also the models from the Auth application.
# The admin users can then create, change and delete users and user groups.
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

site.register(Group, GroupAdmin)
site.register(User, UserAdmin)
