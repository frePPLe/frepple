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

from input.models import Buffer, Flow, Operation, Plan, Resource, Item, Forecast


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
       'title': _('%s %s %s' % ("Where-used report for",type, entity)),
       'supplypath': pathreport.getPath(type, entity, True),
       'type': type,
       'entity': entity,
       'downstream': True,
       }))


  @staticmethod
  @staff_member_required
  def viewupstream(request, type, entity):
    return render_to_response('input/path.html', RequestContext(request,{
       'title': _('%s %s %s' % ("Supply path report for",type, entity)),
       'supplypath': pathreport.getPath(type, entity, False),
       'type': type,
       'entity': entity,
       'downstream': False,
       }))
