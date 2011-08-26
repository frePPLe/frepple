#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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

from datetime import datetime

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.util import ErrorList

from freppledb.input.models import Resource, Forecast, Operation, Location, SetupMatrix
from freppledb.input.models import Buffer, Customer, Demand, Parameter, Item, Load, Flow
from freppledb.input.models import Calendar, CalendarBucket, OperationPlan, SubOperation
from freppledb.input.models import Bucket, BucketDetail, SetupRule, ForecastDemand
from freppledb.admin import site
from freppledb.common import MultiDBModelAdmin, MultiDBTabularInline


class ParameterForm(forms.ModelForm):
  class Meta:
    model = Parameter

  def clean(self):
    cleaned_data = self.cleaned_data
    name = cleaned_data.get("name")
    value = cleaned_data.get("value")
    # Currentdate parameter must be a date+time value
    if name == "currentdate":
      try: datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
      except:
        self._errors["value"] = ErrorList([_("Invalid date: expecting YYYY-MM-DD HH:MM:SS")])
        del cleaned_data["value"]
    return cleaned_data


class Parameter_admin(MultiDBModelAdmin):
  model = Parameter
  save_on_top = True
  form = ParameterForm
site.register(Parameter,Parameter_admin)


class CalendarBucket_inline(MultiDBTabularInline):
  model = CalendarBucket
  extra = 3


class CalendarBucket_admin(MultiDBModelAdmin):
  model = CalendarBucket
  raw_id_fields = ('calendar',)
  save_on_top = True
site.register(CalendarBucket,CalendarBucket_admin)


class Calendar_admin(MultiDBModelAdmin):
  model = Calendar
  save_on_top = True
  inlines = [ CalendarBucket_inline, ]
site.register(Calendar,Calendar_admin)


class Location_admin(MultiDBModelAdmin):
  model = Location
  raw_id_fields = ('available', 'owner',)
  save_on_top = True
site.register(Location,Location_admin)


class Customer_admin(MultiDBModelAdmin):
  model = Customer
  raw_id_fields = ('owner',)
  save_on_top = True
site.register(Customer,Customer_admin)


class Item_admin(MultiDBModelAdmin):
  model = Item
  save_on_top = True
  raw_id_fields = ('operation', 'owner',)
site.register(Item,Item_admin)


class SubOperation_inline(MultiDBTabularInline):
  model = SubOperation
  fk_name = 'operation'
  extra = 1
  raw_id_fields = ('suboperation',)


class Flow_inline(MultiDBTabularInline):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  extra = 1


class Load_inline(MultiDBTabularInline):
  model = Load
  raw_id_fields = ('operation', 'resource',)
  extra = 1


class Operation_admin(MultiDBModelAdmin):
  model = Operation
  raw_id_fields = ('location',)
  save_on_top = True
  inlines = [ SubOperation_inline, Flow_inline, Load_inline, ]
  fieldsets = (
          (None, {'fields': ('name', 'type', 'location', 'description', ('category', 'subcategory'))}),
          (_('Planning parameters'), {
             'fields': ('fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum', 'cost', 'duration', 'duration_per','search'),
             'classes': ('collapse',)
             }),
      )
site.register(Operation,Operation_admin)


class SubOperation_admin(MultiDBModelAdmin):
  model = SubOperation
  raw_id_fields = ('operation', 'suboperation',)
  save_on_top = True
site.register(SubOperation,SubOperation_admin)


class Buffer_admin(MultiDBModelAdmin):
  raw_id_fields = ('location', 'item', 'minimum_calendar', 'producing', 'owner', )
  fieldsets = (
            (None,{
              'fields': (('name'), ('item', 'location'), 'description', 'owner', ('category', 'subcategory'))}),
            (_('Inventory'), {
              'fields': ('onhand',)}),
            (_('Planning parameters'), {
              'fields': ('type','minimum','minimum_calendar','producing','carrying_cost'),
              'classes': ('collapse',)},),
            (_('Planning parameters for procurement buffers'), {
              'fields': ('leadtime','fence','min_inventory','max_inventory','min_interval','max_interval','size_minimum','size_multiple','size_maximum'),
              'classes': ('collapse',)},),
        )
  save_on_top = True
  inlines = [ Flow_inline, ]
site.register(Buffer,Buffer_admin)


class SetupRule_inline(MultiDBTabularInline):
  model = SetupRule
  extra = 3


class SetupMatrix_admin(MultiDBModelAdmin):
  model = SetupMatrix
  save_on_top = True
  inlines = [ SetupRule_inline, ]
site.register(SetupMatrix,SetupMatrix_admin)


class Resource_admin(MultiDBModelAdmin):
  model = Resource
  raw_id_fields = ('maximum_calendar', 'location', 'setupmatrix', 'owner')
  save_on_top = True
  inlines = [ Load_inline, ]
site.register(Resource,Resource_admin)


class Flow_admin(MultiDBModelAdmin):
  model = Flow
  raw_id_fields = ('operation', 'thebuffer',)
  save_on_top = True
site.register(Flow,Flow_admin)


class Load_admin(MultiDBModelAdmin):
  model = Load
  raw_id_fields = ('operation', 'resource',)
  save_on_top = True
site.register(Load,Load_admin)


class OperationPlan_admin(MultiDBModelAdmin):
  model = OperationPlan
  raw_id_fields = ('operation',)
  save_on_top = True
site.register(OperationPlan,OperationPlan_admin)


class Demand_admin(MultiDBModelAdmin):
  model = Demand
  raw_id_fields = ('customer', 'item', 'operation', 'owner',)
  fieldsets = (
            (None, {'fields': ('name', 'item', 'customer', 'description', 'category','subcategory', 'due', 'quantity', 'priority','owner')}),
            (_('Planning parameters'), {'fields': ('operation', 'minshipment', 'maxlateness'), 'classes': ('collapse')}),
        )
  save_on_top = True
site.register(Demand,Demand_admin)


class ForecastDemand_inline(MultiDBTabularInline):
  model = ForecastDemand
  extra = 5


class Forecast_admin(MultiDBModelAdmin):
  model = Forecast
  raw_id_fields = ('customer', 'item', 'calendar', 'operation')
  fieldsets = (
            (None, {'fields': ('name', 'item', 'customer', 'calendar', 'description', 'category','subcategory', 'priority')}),
            (_('Planning parameters'), {'fields': ('discrete', 'operation', 'minshipment', 'maxlateness'), 'classes': ('collapse')}),
        )
  radio_fields = {'priority': admin.HORIZONTAL, }
  inlines = [ ForecastDemand_inline, ]
  save_on_top = True
site.register(Forecast,Forecast_admin)


class BucketDetail_inline(MultiDBTabularInline):
  model = BucketDetail
  extra = 3


class BucketDetail_admin(MultiDBModelAdmin):
  model = BucketDetail
  save_on_top = True
site.register(BucketDetail,BucketDetail_admin)


class Bucket_admin(MultiDBModelAdmin):
  model = Bucket
  save_on_top = True
  inlines = [ BucketDetail_inline, ]
site.register(Bucket,Bucket_admin)
