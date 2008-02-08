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

from datetime import date, datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.core import serializers
from django.utils.simplejson.decoder import JSONDecoder
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from input.models import *
from utils.report import *


class uploadjson:
  '''
  This class allows us to process json-formatted post requests.

  The current implementation is only temporary until a more generic REST interface
  becomes available in Django: see http://code.google.com/p/django-rest-interface/
  '''
  @staticmethod
  @staff_member_required
  def post(request):
    try:
      # Validate the upload form
      if request.method != 'POST':
        raise Exception('Only POST method allowed')

      # Validate uploaded file is present
      if len(request.FILES)!=1 or 'data' not in request.FILES or request.FILES['data']['content-type'] != 'application/json':
        raise Exception('Invalid uploaded data')

      # Parse the uploaded file
      for i in JSONDecoder().decode(request.FILES['data']['content']):
        try:
          entity = i['entity']

          # CASE 1: The maximum calendar of a resource is being edited
          if entity == 'resource.maximum':
            # Create a message
            try:
              msg = "capacity change for '%s' between %s and %s to %s" % \
                    (i['name'],i['startdate'],i['enddate'],i['value'])
            except:
              msg = "capacity change"
            # a) Verify permissions
            if not request.user.has_perm('input.change_resource'):
              raise Exception('No permission to change resources')
            # b) Find the calendar
            res = Resource.objects.get(name = i['name'])
            if not res.maximum:
              raise Exception('Resource "%s" has no max calendar' % res.name)
            # c) Update the calendar
            start = datetime.strptime(i['startdate'],'%Y-%m-%d')
            end = datetime.strptime(i['enddate'],'%Y-%m-%d')
            res.maximum.setvalue(
              start,
              end,
              float(i['value']) / (end - start).days,
              user = request.user)

          # CASE 2: The forecast quantity is being edited
          elif entity == 'forecast.total':
            # Create a message
            try:
              msg = "forecast change for '%s' between %s and %s to %s" % \
                      (i['name'],i['startdate'],i['enddate'],i['value'])
            except:
              msg = "forecast change"
            # a) Verify permissions
            if not request.user.has_perm('input.change_forecastdemand'):
              raise Exception('No permission to change forecast demand')
            # b) Find the forecast
            start = datetime.strptime(i['startdate'],'%Y-%m-%d')
            end = datetime.strptime(i['enddate'],'%Y-%m-%d')
            fcst = Forecast.objects.get(name = i['name'])
            # c) Update the forecast
            fcst.setTotal(start,end,i['value'])

          # All the rest is garbage
          else:
            msg = "unknown action"
            raise Exception("Unknown action type '%s'" % entity)

        except Exception, e:
          request.user.message_set.create(message='Error processing %s: %s' % (msg,e))

      # Processing went fine...
      return HttpResponse("OK")

    except Exception, e:
      print 'Error processing uploaded data: %s %s' % (type(e),e)
      return HttpResponseForbidden('Error processing uploaded data: %s' % e)


class pathreport:
  '''
  A report showing the upstream supply path or following downstream a
  where-used path.
  The supply path report shows all the materials, operations and resources
  used to make a certain item.
  The where-used report shows all the materials and operations that use
  a specific item.
  '''

  @staticmethod
  def getPath(type, entity, downstream):
    '''
    A generator function that recurses upstream or downstream in the supply
    chain.
    @todo The current code only supports 1 level of super- or sub-operations.
    @todo When the supply chain contains loops this function wont work fine.
    '''
    from decimal import Decimal
    from django.core.exceptions import ObjectDoesNotExist
    if type == 'buffer':
      # Find the buffer
      try: root = [ (0, Buffer.objects.get(name=entity), None, None, None, Decimal(1)) ]
      except ObjectDoesNotExist: raise Http404, "buffer %s doesn't exist" % entity
    elif type == 'item':
      # Find the item
      try:
        root = [ (0, r, None, None, None, Decimal(1)) for r in Buffer.objects.filter(item=entity) ]
      except ObjectDoesNotExist: raise Http404, "item %s doesn't exist" % entity
    elif type == 'operation':
      # Find the operation
      try: root = [ (0, None, None, Operation.objects.get(name=entity), None, Decimal(1)) ]
      except ObjectDoesNotExist: raise Http404, "operation %s doesn't exist" % entity
    elif type == 'resource':
      # Find the resource
      try: root = Resource.objects.get(name=entity)
      except ObjectDoesNotExist: raise Http404, "resource %s doesn't exist" % entity
      root = [ (0, None, None, i.operation, None, Decimal(1)) for i in root.loads.all() ]
    else:
      raise Http404, "invalid entity type %s" % type

    # Note that the root to start with can be either buffer or operation.
    while len(root) > 0:
      level, curbuffer, curprodflow, curoperation, curconsflow, curqty = root.pop()
      yield {
        'buffer': curbuffer,
        'producingflow': curprodflow,
        'operation': curoperation,
        'level': abs(level),
        'consumingflow': curconsflow,
        'cumquantity': curqty,
        }

      if downstream:
        # Find all operations consuming from this buffer...
        if curbuffer:
          start = [ (i, i.operation) for i in curbuffer.flows.filter(quantity__lt=0).select_related(depth=1) ]
        else:
          start = [ (None, curoperation) ]
        for cons_flow, curoperation in start:
          if not cons_flow and not curoperation: continue
          # ... and pick up the buffer they produce into
          ok = False

          # Push the next buffer on the stack, based on current operation
          for prod_flow in curoperation.flows.filter(quantity__gt=0).select_related(depth=1):
            ok = True
            root.append( (level+1, prod_flow.thebuffer, prod_flow, curoperation, cons_flow, curqty / prod_flow.quantity * (cons_flow and cons_flow.quantity * -1 or 1)) )

          # Push the next buffer on the stack, based on super-operations
          for x in curoperation.superoperations.select_related(depth=1):
            for prod_flow in x.suboperation.flows.filter(quantity__gt=0):
              ok = True
              root.append( (level+1, prod_flow.thebuffer, prod_flow, curoperation, cons_flow, curqty / prod_flow.quantity * (cons_flow and cons_flow.quantity * -1 or 1)) )

          # Push the next buffer on the stack, based on sub-operations
          for x in curoperation.suboperations.select_related(depth=1):
            for prod_flow in x.operation.flows.filter(quantity__gt=0):
              ok = True
              root.append( (level+1, prod_flow.thebuffer, prod_flow, curoperation, cons_flow, curqty / prod_flow.quantity * (cons_flow and cons_flow.quantity * -1 or 1)) )

          if not ok and cons_flow:
            # No producing flow found: there are no more buffers downstream
            root.append( (level+1, None, None, curoperation, cons_flow, curqty * cons_flow.quantity * -1) )

      else:
        # Find all operations producing into this buffer...
        if curbuffer:
          if curbuffer.producing:
            start = [ (i, i.operation) for i in curbuffer.producing.flows.filter(quantity__gt=0).select_related(depth=1) ]
          else:
            start = []
        else:
          start = [ (None, curoperation) ]
        for prod_flow, curoperation in start:
          if not prod_flow and not curoperation: continue
          # ... and pick up the buffer they produce into
          ok = False

          # Push the next buffer on the stack, based on current operation
          for cons_flow in curoperation.flows.filter(quantity__lt=0).select_related(depth=1):
            ok = True
            root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          # Push the next buffer on the stack, based on super-operations
          for x in curoperation.superoperations.select_related(depth=1):
            for cons_flow in x.suboperation.flows.filter(quantity__lt=0):
              ok = True
              root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          # Push the next buffer on the stack, based on sub-operations
          for x in curoperation.suboperations.select_related(depth=1):
            for cons_flow in x.operation.flows.filter(quantity__lt=0):
              ok = True
              root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          if not ok and prod_flow:
            # No consuming flow found: there are no more buffers upstream
            ok = True
            root.append( (level-1, None, prod_flow, prod_flow.operation, None, curqty / prod_flow.quantity) )


  @staticmethod
  @staff_member_required
  def viewdownstream(request, type, entity):
    return render_to_response('input/path.html', RequestContext(request,{
       'title': _('Where-used report for %(type)s %(entity)s') % {'type':_(type), 'entity':entity},
       'supplypath': pathreport.getPath(type, entity, True),
       'type': type,
       'entity': entity,
       'downstream': True,
       }))


  @staticmethod
  @staff_member_required
  def viewupstream(request, type, entity):
    return render_to_response('input/path.html', RequestContext(request,{
       'title': _('Supply path report for %(type)s %(entity)s') % {'type':_(type), 'entity':entity},
       'supplypath': pathreport.getPath(type, entity, False),
       'type': type,
       'entity': entity,
       'downstream': False,
       }))


class BufferList(ListReport):
  '''
  A list report to show buffers.
  '''
  template = 'input/bufferlist.html'
  title = _("Buffer List")
  basequeryset = Buffer.objects.all()
  model = Buffer
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('location', {
      'title': _('location'),
      'filter': FilterText(field='location__name'),
      }),
    ('item', {
      'title': _('item'),
      'filter': FilterText(field='item__name'),
      }),
    ('onhand', {
      'title': _('onhand'),
      'filter': FilterNumber(size=5, operator="lt"),
      }),
    ('type', {
      'title': _('type'),
      'filter': FilterText(),
      }),
    ('minimum', {
      'title': _('minimum'),
      'filter': FilterText(field='minimum__name'),
      }),
    ('producing', {
      'title': _('producing'),
      'filter': FilterText(field='producing__name'),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class ResourceList(ListReport):
  '''
  A list report to show resources.
  '''
  template = 'input/resourcelist.html'
  title = _("Resource List")
  basequeryset = Resource.objects.all()
  model = Resource
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('location', {
      'title': _('location'),
      'filter': FilterText(field='location__name'),
      }),
    ('type', {
      'title': _('type'),
      'filter': FilterText(),
      }),
    ('maximum', {
      'title': _('maximum'),
      'filter': FilterText(field='maximum__name'),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class LocationList(ListReport):
  '''
  A list report to show locations.
  '''
  template = 'input/locationlist.html'
  title = _("Location List")
  basequeryset = Location.objects.all()
  model = Location
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('available', {
      'title': _('available'),
      'filter': FilterText(field='available__name'),
      }),
    ('owner', {
      'title': _('owner'),
      'filter': FilterText(field='owner__name'),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class CustomerList(ListReport):
  '''
  A list report to show locations.
  '''
  template = 'input/customerlist.html'
  title = _("Customer List")
  basequeryset = Customer.objects.all()
  model = Customer
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('owner', {
      'title': _('owner'),
      'filter': FilterText(field='owner__name'),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class ItemList(ListReport):
  '''
  A list report to show items.
  '''
  template = 'input/itemlist.html'
  title = _("Item List")
  basequeryset = Item.objects.all()
  model = Item
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(field='operation__name'),
      }),
    ('owner', {
      'title': _('owner'),
      'filter': FilterText(field='owner__name'),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class LoadList(ListReport):
  '''
  A list report to show loads.
  '''
  template = 'input/loadlist.html'
  title = _("Load List")
  basequeryset = Load.objects.all()
  model = Load
  rows = (
    ('id', {
      'title': _('identifier'),
      'filter': FilterNumber(),
      }),
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(field='operation__name'),
      }),
    ('resource', {
      'title': _('resource'),
      'filter': FilterText(field='resource__name'),
      }),
    ('usagefactor', {
      'title': _('usagefactor'),
      'filter': FilterNumber(),
      }),
    ('effective_start', {
      'title': _('effective start'),
      'filter': FilterDate(),
      }),
    ('effective_end', {
      'title': _('effective end'),
      'filter': FilterDate(),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class FlowList(ListReport):
  '''
  A list report to show flows.
  '''
  template = 'input/flowlist.html'
  title = _("Flow List")
  basequeryset = Flow.objects.all()
  model = Flow
  rows = (
    ('id', {
      'title': _('identifier'),
      'filter': FilterNumber(),
      }),
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(field='operation__name'),
      }),
    ('thebuffer', {
      'title': _('buffer'),
      'filter': FilterText(field='thebuffer__name'),
      }),
    ('type', {
      'title': _('type'),
      'filter': FilterText(),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('effective_start', {
      'title': _('effective start'),
      'filter': FilterDate(),
      }),
    ('effective_end', {
      'title': _('effective end'),
      'filter': FilterDate(),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class DemandList(ListReport):
  '''
  A list report to show demands.
  '''
  template = 'input/demandlist.html'
  title = _("Demand List")
  basequeryset = Demand.objects.all()
  model = Demand
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('item', {
      'title': _('item'),
      'filter': FilterText(field="item_name"),
      }),
    ('customer', {
      'title': _('customer'),
      'filter': FilterText(field="customer__name"),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('due', {
      'title': _('due'),
      'filter': FilterDate(),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(),
      }),
    ('priority', {
      'title': _('priority'),
      'filter': FilterNumber(),
      }),
    ('owner', {
      'title': _('owner'),
      'filter': FilterText(field='owner__name'),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class ForecastList(ListReport):
  '''
  A list report to show forecasts.
  '''
  template = 'input/forecastlist.html'
  title = _("Forecast List")
  basequeryset = Forecast.objects.all()
  model = Forecast
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('item', {
      'title': _('item'),
      'filter': FilterText(field="item_name"),
      }),
    ('customer', {
      'title': _('customer'),
      'filter': FilterText(field="customer__name"),
      }),
    ('calendar', {
      'title': _('calendar'),
      'filter': FilterText(field="calendar__name"),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('due', {
      'title': _('due'),
      'filter': FilterDate(),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(),
      }),
    ('priority', {
      'title': _('priority'),
      'filter': FilterNumber(),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class DatesList(ListReport):
  '''
  A list report to show dates.
  '''
  template = 'input/dateslist.html'
  title = _("Date List")
  basequeryset = Dates.objects.all()
  model = Dates
  rows = (
    ('day', {
      'title': _('day'),
      'filter': FilterDate(),
      }),
    ('dayofweek', {
      'title': _('day of week'),
      'filter': FilterNumber(),
      }),
    ('week', {
      'title': _('week'),
      'filter': FilterText(),
      }),
    ('month', {
      'title': _('month'),
      'filter': FilterText(),
      }),
    ('quarter', {
      'title': _('quarter'),
      'filter': FilterText(),
      }),
    ('year', {
      'title': _('year'),
      'filter': FilterText(),
      }),
    ('default', {
      'title': _('default'),
      'filter': FilterText(),
      }),
    ('week_start', {
      'title': _('week start'),
      'filter': FilterDate(),
      }),
    ('month_start', {
      'title': _('month start'),
      'filter': FilterDate(),
      }),
    ('quarter_start', {
      'title': _('month start'),
      'filter': FilterDate(),
      }),
    ('year_start', {
      'title': _('year start'),
      'filter': FilterDate(),
      }),
    ('default_start', {
      'title': _('default start'),
      'filter': FilterDate(),
      }),
    )


class CalendarList(ListReport):
  '''
  A list report to show calendars.
  '''
  template = 'input/calendarlist.html'
  title = _("Calendar List")
  basequeryset = Calendar.objects.all()
  model = Calendar
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(),
      }),
    ('category', {
      'title': _('category'),
      'filter': FilterText(),
      }),
    ('subcategory', {
      'title': _('subcategory'),
      'filter': FilterText(),
      }),
    ('currentvalue', {
      'title': _('current value'),
      'sort': False,
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class OperationList(ListReport):
  '''
  A list report to show operations.
  '''
  template = 'input/operationlist.html'
  title = _("Operation List")
  basequeryset = Operation.objects.all()
  model = Operation
  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    ('type', {
      'title': _('type'),
      'filter': FilterText(),
      }),
    ('location', {
      'title': _('location'),
      'filter': FilterText(field='location__name'),
      }),
    ('fence', {
      'title': _('fence'),
      'filter': FilterNumber(),
      }),
    ('pretime', {
      'title': _('pre-op time'),
      'filter': FilterNumber(),
      }),
    ('posttime', {
      'title': _('post-op time'),
      'filter': FilterNumber(),
      }),
    ('sizeminimum', {
      'title': _('size minimum'),
      'filter': FilterNumber(),
      }),
    ('sizemultiple', {
      'title': _('size multiple'),
      'filter': FilterNumber(),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class SubOperationList(ListReport):
  '''
  A list report to show suboperations.
  '''
  template = 'input/suboperationlist.html'
  title = _("Suboperation List")
  basequeryset = SubOperation.objects.all()
  model = SubOperation
  rows = (
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(field='operation__name'),
      }),
    ('suboperation', {
      'title': _('suboperation'),
      'filter': FilterText(field='suboperation__name'),
      }),
    ('priority', {
      'title': _('priority'),
      'filter': FilterNumber(),
      }),
    ('effective_start', {
      'title': _('effective start'),
      'filter': FilterDate(),
      }),
    ('effective_end', {
      'title': _('effective end'),
      'filter': FilterDate(),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )


class OperationPlanList(ListReport):
  '''
  A list report to show operationplans.
  '''
  template = 'input/operationplanlist.html'
  title = _("Operationplan List")
  basequeryset = OperationPlan.objects.all()
  model = OperationPlan
  rows = (
    ('identifier', {
      'title': _('identifier'),
      'filter': FilterNumber(),
      }),
    ('operation', {
      'title': _('operation'),
      'filter': FilterText(field='operation__name'),
      }),
    ('startdate', {
      'title': _('start date'),
      'filter': FilterDate(),
      }),
    ('enddate', {
      'title': _('end date'),
      'filter': FilterDate(),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('locked', {
      'title': _('locked'),
      'filter': FilterBool(),
      }),
    ('lastmodified', {
      'title': _('last modified'),
      'filter': FilterDate(),
      }),
    )
