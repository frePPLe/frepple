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
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_protect
from django.utils import simplejson
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import iri_to_uri, force_unicode

from freppledb.input.models import Resource, Forecast, Operation, Location, SetupMatrix
from freppledb.input.models import Buffer, Customer, Demand, Parameter, Item, Load, Flow
from freppledb.input.models import Calendar, CalendarBucket, OperationPlan, SubOperation
from freppledb.input.models import Bucket, BucketDetail
from freppledb.common.report import GridReport, BoolGridField, LastModifiedGridField, DateTimeGridField
from freppledb.common.report import TextGridField, NumberGridField, IntegerGridField, CurrencyGridField


class uploadjson:
  '''
  This class allows us to process json-formatted post requests.

  The current implementation is only temporary until a more generic REST interface
  becomes available in Django: see http://code.google.com/p/django-rest-interface/
  '''
  @staticmethod
  @csrf_protect
  @staff_member_required
  def post(request):
    try:
      # Validate the upload form
      if request.method != 'POST' or not request.is_ajax():
        raise Exception(_('Only ajax POST method allowed'))

      # Validate uploaded file is present
      if len(request.FILES)!=1 or 'data' not in request.FILES \
        or request.FILES['data'].content_type != 'application/json' \
        or request.FILES['data'].size > 1000000:
          raise Exception('Invalid uploaded data')

      # Parse the uploaded data and go over each record
      for i in simplejson.JSONDecoder().decode(request.FILES['data'].read()):
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
            res = Resource.objects.using(request.database).get(name = i['name'])
            if not res.maximum_calendar:
              raise Exception('Resource "%s" has no maximum calendar' % res.name)
            # c) Update the calendar
            start = datetime.strptime(i['startdate'],'%Y-%m-%d')
            end = datetime.strptime(i['enddate'],'%Y-%m-%d')
            res.maximum_calendar.setvalue(
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
            fcst = Forecast.objects.using(request.database).get(name = i['name'])
            # c) Update the forecast
            fcst.setTotal(start,end,i['value'])

          # All the rest is garbage
          else:
            msg = "unknown action"
            raise Exception(_("Unknown action type '%(msg)s'") % {'msg':entity})

        except Exception as e:
          messages.add_message(request, messages.ERROR, 'Error processing %s: %s' % (msg,e))

      # Processing went fine...
      return HttpResponse("OK",mimetype='text/plain')

    except Exception as e:
      print('Error processing uploaded data: %s %s' % (type(e),e))
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
  def getPath(request, type, entity, downstream):
    '''
    A generator function that recurses upstream or downstream in the supply
    chain.

    todo: The current code only supports 1 level of super- or sub-operations.
    '''
    from django.core.exceptions import ObjectDoesNotExist
    if type == 'buffer':
      # Find the buffer
      try: root = [ (0, Buffer.objects.using(request.database).get(name=entity), None, None, None, Decimal(1)) ]
      except ObjectDoesNotExist: raise Http404("buffer %s doesn't exist" % entity)
    elif type == 'item':
      # Find the item
      try:
        root = [ (0, r, None, None, None, Decimal(1)) for r in Buffer.objects.filter(item=entity).using(request.database) ]
      except ObjectDoesNotExist: raise Http404("item %s doesn't exist" % entity)
    elif type == 'operation':
      # Find the operation
      try: root = [ (0, None, None, Operation.objects.using(request.database).get(name=entity), None, Decimal(1)) ]
      except ObjectDoesNotExist: raise Http404("operation %s doesn't exist" % entity)
    elif type == 'resource':
      # Find the resource
      try: root = Resource.objects.using(request.database).get(name=entity)
      except ObjectDoesNotExist: raise Http404("resource %s doesn't exist" % entity)
      root = [ (0, None, None, i.operation, None, Decimal(1)) for i in root.loads.using(request.database).all() ]
    else:
      raise Http404("invalid entity type %s" % type)

    # Note that the root to start with can be either buffer or operation.
    visited = []
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

      # Avoid infinite loops when the supply chain contains cycles
      if curbuffer:
        if curbuffer in visited: continue
        else: visited.append(curbuffer)
      else:
        if curoperation and curoperation in visited: continue
        else: visited.append(curoperation)

      if downstream:
        # DOWNSTREAM: Find all operations consuming from this buffer...
        if curbuffer:
          start = [ (i, i.operation) for i in curbuffer.flows.filter(quantity__lt=0).select_related(depth=1).using(request.database) ]
        else:
          start = [ (None, curoperation) ]
        for cons_flow, curoperation in start:
          if not cons_flow and not curoperation: continue
          # ... and pick up the buffer they produce into
          ok = False

          # Push the next buffer on the stack, based on current operation
          for prod_flow in curoperation.flows.filter(quantity__gt=0).select_related(depth=1).using(request.database):
            ok = True
            root.append( (level+1, prod_flow.thebuffer, prod_flow, curoperation, cons_flow, curqty / prod_flow.quantity * (cons_flow and cons_flow.quantity * -1 or 1)) )

          # Push the next buffer on the stack, based on super-operations
          for x in curoperation.superoperations.select_related(depth=1).using(request.database):
            for prod_flow in x.operation.flows.filter(quantity__gt=0).using(request.database):
              ok = True
              root.append( (level+1, prod_flow.thebuffer, prod_flow, curoperation, cons_flow, curqty / prod_flow.quantity * (cons_flow and cons_flow.quantity * -1 or 1)) )

          # Push the next buffer on the stack, based on sub-operations
          for x in curoperation.suboperations.select_related(depth=1).using(request.database):
            for prod_flow in x.suboperation.flows.filter(quantity__gt=0).using(request.database):
              ok = True
              root.append( (level+1, prod_flow.thebuffer, prod_flow, curoperation, cons_flow, curqty / prod_flow.quantity * (cons_flow and cons_flow.quantity * -1 or 1)) )

          if not ok and cons_flow:
            # No producing flow found: there are no more buffers downstream
            root.append( (level+1, None, None, curoperation, cons_flow, curqty * cons_flow.quantity * -1) )
          if not ok:
            # An operation without any flows (on itself, any of its suboperations or any of its superoperations)
            for x in curoperation.suboperations.using(request.database):
              root.append( (level+1, None, None, x.suboperation, None, curqty) )
            for x in curoperation.superoperations.using(request.database):
              root.append( (level+1, None, None, x.operation, None, curqty) )

      else:
        # UPSTREAM: Find all operations producing into this buffer...
        if curbuffer:
          if curbuffer.producing:
            start = [ (i, i.operation) for i in curbuffer.producing.flows.filter(quantity__gt=0).select_related(depth=1).using(request.database) ]
          else:
            start = []
        else:
          start = [ (None, curoperation) ]
        for prod_flow, curoperation in start:
          if not prod_flow and not curoperation: continue
          # ... and pick up the buffer they produce into
          ok = False

          # Push the next buffer on the stack, based on current operation
          for cons_flow in curoperation.flows.filter(quantity__lt=0).select_related(depth=1).using(request.database):
            ok = True
            root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          # Push the next buffer on the stack, based on super-operations
          for x in curoperation.superoperations.select_related(depth=1).using(request.database):
            for cons_flow in x.operation.flows.filter(quantity__lt=0).using(request.database):
              ok = True
              root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          # Push the next buffer on the stack, based on sub-operations
          for x in curoperation.suboperations.select_related(depth=1).using(request.database):
            for cons_flow in x.suboperation.flows.filter(quantity__lt=0).using(request.database):
              ok = True
              root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          if not ok and prod_flow:
            # No consuming flow found: there are no more buffers upstream
            ok = True
            root.append( (level-1, None, prod_flow, prod_flow.operation, None, curqty / prod_flow.quantity) )
          if not ok:
            # An operation without any flows (on itself, any of its suboperations or any of its superoperations)
            for x in curoperation.suboperations.using(request.database):
              root.append( (level-1, None, None, x.suboperation, None, curqty) )
            for x in curoperation.superoperations.using(request.database):
              root.append( (level-1, None, None, x.operation, None, curqty) )

  @staticmethod
  @staff_member_required
  def viewdownstream(request, type, entity):
    return render_to_response('input/path.html', RequestContext(request,{
       'title': _('Where-used report for %(type)s %(entity)s') % {'type':_(type), 'entity':entity},
       'supplypath': pathreport.getPath(request, type, entity, True),
       'type': type,
       'entity': entity,
       'downstream': True,
       }))


  @staticmethod
  @staff_member_required
  def viewupstream(request, type, entity):
    return render_to_response('input/path.html', RequestContext(request,{
       'title': _('Supply path report for %(type)s %(entity)s') % {'type':_(type), 'entity':entity},
       'supplypath': pathreport.getPath(request, type, entity, False),
       'type': type,
       'entity': entity,
       'downstream': False,
       }))


@staff_member_required
def location_calendar(request, location):
  # Check to find a location availability calendar
  loc = Location.objects.using(request.database).get(pk=location)
  if loc:
    cal = loc.available
  if cal:
    # Go to the calendar
    return HttpResponseRedirect('%s/admin/input/calendar/%s/' % (request.prefix, iri_to_uri(cal.name)) )
  # Generate a message
  try:
    url = request.META.get('HTTP_REFERER')
    messages.add_message(request, messages.ERROR,
      force_unicode(_('No availability calendar found')))
    return HttpResponseRedirect(url)
  except: raise Http404


class ParameterList(GridReport):
  '''
  A list report to show all configurable parameters.
  '''
  template = 'input/parameterlist.html'
  title = _("Parameter List")
  basequeryset = Parameter.objects.all()
  model = Parameter
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values('name','value','description','lastmodified')

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('value', title=_('value')),
    TextGridField('description', title=_('description')),
    LastModifiedGridField('lastmodified'),
    )


class BufferList(GridReport):
  '''
  A list report to show buffers.
  '''
  template = 'input/bufferlist.html'
  title = _("Buffer List")
  basequeryset = Buffer.objects.all()
  model = Buffer
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','description','category','subcategory','location','item','onhand',
      'owner','type','minimum','minimum_calendar','producing','carrying_cost','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('location', title=_('location'), field_name='location__name', formatter='location'),
    TextGridField('item', title=_('item'), field_name='item__name', formatter='item'),
    NumberGridField('onhand', title=_('onhand')),
    TextGridField('owner', title=_('owner'), field_name='owner__name', formatter='buffer'),
    TextGridField('type', title=_('type')),
    NumberGridField('minimum', title=_('minimum')),
    TextGridField('minimum_calendar', title=_('minimum calendar'), field_name='minimum_calendar__name', formatter='calendar'),
    TextGridField('producing', title=_('producing'), field_name='producing__name', formatter='operation'),
    CurrencyGridField('carrying_cost', title=_('carrying cost')),
    LastModifiedGridField('lastmodified'),
    )


class SetupMatrixList(GridReport):
  '''
  A list report to show setup matrices.
  '''
  template = 'input/setupmatrixlist.html'
  title = _("Setup Matrix List")
  basequeryset = SetupMatrix.objects.all()
  model = SetupMatrix
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values('name','lastmodified')

  rows = (
    TextGridField('name', title=_('name'), key=True),
    LastModifiedGridField('lastmodified'),
    )


class ResourceList(GridReport):
  '''
  A list report to show resources.
  '''
  template = 'input/resourcelist.html'
  title = _("Resource List")
  basequeryset = Resource.objects.all()
  model = Resource
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','description','category','subcategory','location','owner','type',
      'maximum','maximum_calendar','cost','maxearly','setupmatrix','setup','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('location', title=_('location'), field_name='location__name', formatter='location'),
    TextGridField('owner', title=_('owner'), field_name='owner__name', formatter='resource'),
    TextGridField('type', title=_('type')),
    NumberGridField('maximum', title=_('maximum')),
    TextGridField('maximum_calendar', title=_('maximum calendar'), field_name='maximum_calendar__name', formatter='calendar'),
    CurrencyGridField('cost', title=_('cost')),
    NumberGridField('maxearly', title=_('maxearly')),
    TextGridField('setupmatrix', title=_('setup matrix'), formatter='setupmatrix'),
    TextGridField('setup', title=_('setup')),
    LastModifiedGridField('lastmodified'),
    )


class LocationList(GridReport):
  '''
  A list report to show locations.
  '''
  template = 'input/locationlist.html'
  title = _("Location List")
  basequeryset = Location.objects.all()
  model = Location
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','description','category','subcategory','available','owner',
      'lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('available', title=_('available'), field_name='available__name', formatter='calendar'),
    TextGridField('owner', title=_('owner'), field_name='owner__name', formatter='location'),
    LastModifiedGridField('lastmodified'),
    )


class CustomerList(GridReport):
  '''
  A list report to show customers.
  '''
  template = 'input/customerlist.html'
  title = _("Customer List")
  basequeryset = Customer.objects.all()
  model = Customer
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','description','category','subcategory','owner','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('owner', title=_('owner'), field_name='owner__name', formatter='customer'),
    LastModifiedGridField('lastmodified'),
    )


class ItemList(GridReport):
  '''
  A list report to show items.
  '''
  template = 'input/itemlist.html'
  title = _("Item List")
  basequeryset = Item.objects.all()
  model = Item
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','description','category','subcategory','operation','owner',
      'price','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('operation', title=_('operation'), field_name='operation__name'),
    TextGridField('owner', title=_('owner'), field_name='owner__name'),
    CurrencyGridField('price', title=_('price')),
    LastModifiedGridField('lastmodified'),
    )


class LoadList(GridReport):
  '''
  A list report to show loads.
  '''
  template = 'input/loadlist.html'
  title = _("Load List")
  basequeryset = Load.objects.all()
  model = Load
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'id','operation','resource','quantity','effective_start','effective_end',
      'name','alternate','priority','setup','search','lastmodified'
      )

  rows = (
    NumberGridField('id', title=_('identifier'), key=True),
    TextGridField('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    TextGridField('resource', title=_('resource'), field_name='resource__name', formatter='resource'),
    NumberGridField('quantity', title=_('quantity')),
    DateTimeGridField('effective_start', title=_('effective start')),
    DateTimeGridField('effective_end', title=_('effective end')),
    TextGridField('name', title=_('name')),
    TextGridField('alternate', title=_('alternate')),
    NumberGridField('priority', title=_('priority')),
    TextGridField('setup', title=_('setup')),
    TextGridField('search', title=_('search mode')),
    LastModifiedGridField('lastmodified'),
    )


class FlowList(GridReport):
  '''
  A list report to show flows.
  '''
  template = 'input/flowlist.html'
  title = _("Flow List")
  basequeryset = Flow.objects.all()
  model = Flow
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'id','operation','thebuffer','type','quantity','effective_start',
      'effective_end','name','alternate','priority','search','lastmodified'
      )

  rows = (
    NumberGridField('id', title=_('identifier'), key=True),
    TextGridField('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    TextGridField('thebuffer', title=_('buffer'), field_name='thebuffer__name', formatter='buffer'),
    TextGridField('type', title=_('type')),
    NumberGridField('quantity', title=_('quantity')),
    DateTimeGridField('effective_start', title=_('effective start')),
    DateTimeGridField('effective_end', title=_('effective end')),
    TextGridField('name', title=_('name')),
    TextGridField('alternate', title=_('alternate')),
    NumberGridField('priority', title=_('priority')),
    TextGridField('search', title=_('search mode')),
    LastModifiedGridField('lastmodified'),
    )


class DemandList(GridReport):
  '''
  A list report to show demands.
  '''
  template = 'input/demandlist.html'
  title = _("Demand List")
  basequeryset = Demand.objects.all()
  model = Demand
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','item','customer','description','category','subcategory',
      'due','quantity','operation','priority','owner','maxlateness',
      'minshipment','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('item', title=_('item_name'), field_name='item__name', formatter='item'),
    TextGridField('customer', title=_('customer'), field_name='customer__name', formatter='location'),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    DateTimeGridField('due', title=_('due')),
    NumberGridField('quantity', title=_('quantity')),
    TextGridField('operation', title=_('delivery operation'), formatter='operation'),
    NumberGridField('priority', title=_('priority')),
    TextGridField('owner', title=_('owner'), formatter='demand'),
    NumberGridField('maxlateness', title=_('maximum lateness')),
    NumberGridField('minshipment', title=_('minimum shipment')),
    LastModifiedGridField('lastmodified'),
    )


class ForecastList(GridReport):
  '''
  A list report to show forecasts.
  '''
  template = 'input/forecastlist.html'
  title = _("Forecast List")
  basequeryset = Forecast.objects.all()
  model = Forecast
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','item','customer','calendar','description','category',
      'subcategory','operation','priority','minshipment','maxlateness',
      'discrete','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('item', title=_('item'), field_name='item__name', formatter='item'),
    TextGridField('customer', title=_('customer'), field_name='customer__name', formatter='customer'),
    TextGridField('calendar', title=_('calendar'), field_name='calendar__name', formatter='calendar'),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    NumberGridField('priority', title=_('priority')),
    NumberGridField('maxlateness', title=_('maximum lateness')),
    NumberGridField('minshipment', title=_('minimum shipment')),
    BoolGridField('discrete', title=_('discrete')),
    LastModifiedGridField('lastmodified'),
    )


class CalendarList(GridReport):
  '''
  A list report to show calendars.
  '''
  template = 'input/calendarlist.html'
  title = _("Calendar List")
  basequeryset = Calendar.objects.all()
  model = Calendar
  frozenColumns = 1
  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('type', title=_('type')),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    NumberGridField('defaultvalue', title=_('default value')),
    NumberGridField('currentvalue', title=_('current value'), sortable=False),
    LastModifiedGridField('lastmodified'),
    )


class CalendarBucketList(GridReport):
  '''
  A list report to show calendar buckets.
  '''
  template = 'input/calendarbucketlist.html'
  title = _("Calendar Bucket List")
  basequeryset = CalendarBucket.objects.all()
  model = CalendarBucket
  frozenColumns = 1
  rows = (
    NumberGridField('id', title=_('identifier'), key=True),
    TextGridField('calendar', title=_('calendar'), field_name='calendar__name', formatter='calendar'),
    DateTimeGridField('startdate', title=_('start date')),
    DateTimeGridField('enddate', title=_('end date')),
    NumberGridField('value', title=_('value')),
    NumberGridField('priority', title=_('priority')),
    TextGridField('name', title=_('name')),
    LastModifiedGridField('lastmodified'),
    )


class OperationList(GridReport):
  '''
  A list report to show operations.
  '''
  template = 'input/operationlist.html'
  title = _("Operation List")
  basequeryset = Operation.objects.all()
  model = Operation
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'name','description','category','subcategory','type','location','duration','duration_per','fence','pretime','posttime','sizeminimum',
      'sizemultiple','sizemaximum','cost','search','lastmodified'
      )

  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    TextGridField('category', title=_('category')),
    TextGridField('subcategory', title=_('subcategory')),
    TextGridField('type', title=_('type')),
    TextGridField('location', title=_('location'), field_name='location__name', formatter='location'),
    NumberGridField('duration', title=_('duration')),
    NumberGridField('duration_per', title=_('duration_per')),
    NumberGridField('fence', title=_('fence')),
    NumberGridField('pretime', title=_('pre-op time')),
    NumberGridField('posttime', title=_('post-op time')),
    NumberGridField('sizeminimum', title=_('size minimum')),
    NumberGridField('sizemultiple', title=_('size multiple')),
    NumberGridField('sizemaximum', title=_('size maximum')),
    CurrencyGridField('cost', title=_('cost')),
    TextGridField('search', title=_('search mode')),
    LastModifiedGridField('lastmodified'),
    )


class SubOperationList(GridReport):
  '''
  A list report to show suboperations.
  '''
  template = 'input/suboperationlist.html'
  title = _("Suboperation List")
  basequeryset = SubOperation.objects.all()
  model = SubOperation
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'id','operation','suboperation','priority','effective_start','effective_end',
      'lastmodified'
      )

  rows = (
    NumberGridField('id', title=_('identifier'), key=True),
    TextGridField('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    TextGridField('suboperation', title=_('suboperation'), field_name='suboperation__name', formatter='operation'),
    NumberGridField('priority', title=_('priority')),
    DateTimeGridField('effective_start', title=_('effective start')),
    DateTimeGridField('effective_end', title=_('effective end')),
    LastModifiedGridField('lastmodified'),
    )


class OperationPlanList(GridReport):
  '''
  A list report to show operationplans.
  '''
  template = 'input/operationplanlist.html'
  title = _("Operationplan List")
  basequeryset = OperationPlan.objects.all()
  model = OperationPlan
  frozenColumns = 1

  @staticmethod
  def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
    return basequery.values(
      'id','operation','startdate','enddate','quantity','locked', 'owner', 
      'lastmodified'
      )

  rows = (
    NumberGridField('id', title=_('identifier'), key=True),
    TextGridField('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    DateTimeGridField('startdate', title=_('start date')),
    DateTimeGridField('enddate', title=_('end date')),
    NumberGridField('quantity', title=_('quantity')),
    BoolGridField('locked', title=_('locked')),
    IntegerGridField('owner', title=_('owner')),
    LastModifiedGridField('lastmodified'),
    )


class BucketList(GridReport):
  '''
  A list report to show dates.
  '''
  template = 'input/bucketlist.html'
  title = _("Bucket List")
  basequeryset = Bucket.objects.all()
  model = Bucket
  frozenColumns = 1
  rows = (
    TextGridField('name', title=_('name'), key=True),
    TextGridField('description', title=_('description')),
    LastModifiedGridField('lastmodified'),
    )


class BucketDetailList(GridReport):
  '''
  A list report to show dates.
  '''
  template = 'input/bucketdetaillist.html'
  title = _("Bucket Detail List")
  basequeryset = BucketDetail.objects.all()
  model = BucketDetail
  frozenColumns = 1
  rows = (
    NumberGridField('id', title=_('identifier'), key=True),
    TextGridField('bucket', title=_('bucket'), field_name='bucket__name'),
    DateTimeGridField('startdate', title=_('start date')),
    DateTimeGridField('enddate', title=_('end date')),
    LastModifiedGridField('lastmodified'),
    )
