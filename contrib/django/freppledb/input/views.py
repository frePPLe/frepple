#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from decimal import Decimal
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.utils.encoding import iri_to_uri, force_unicode
from django.utils.text import capfirst

from freppledb.input.models import Resource, Operation, Location, SetupMatrix
from freppledb.input.models import Buffer, Customer, Demand, Item, Load, Flow, Skill
from freppledb.input.models import Calendar, CalendarBucket, OperationPlan, SubOperation
from freppledb.input.models import ResourceSkill
from freppledb.common.report import GridReport, GridFieldBool, GridFieldLastModified
from freppledb.common.report import GridFieldDateTime, GridFieldTime, GridFieldText
from freppledb.common.report import GridFieldNumber, GridFieldInteger, GridFieldCurrency
from freppledb.common.report import GridFieldChoice


@staff_member_required
def search(request):
  term = request.GET.get('term')
  result = []
  
  # Search demands
  if term and request.user.has_perm('input.change_demand'):
    query = Demand.objects.using(request.database).filter(name__icontains=term).order_by('name').values_list('name')
    count = len(query)
    if count > 0:
      result.append( {'value': None, 'label': (ungettext(
         '%(name)s - %(count)d match', 
         '%(name)s - %(count)d matches', count) % {'name': force_unicode(_('demand')), 'count': count}).capitalize()
         })
      result.extend([ {'label':'demand', 'value':i[0]} for i in query[:10] ])
  
  # Search customers
  if term and request.user.has_perm('input.change_customer'):
    query = Customer.objects.using(request.database).filter(name__icontains=term).order_by('name').values_list('name')
    count = len(query)
    if count > 0:
      result.append( {'value': None, 'label': (ungettext(
         '%(name)s - %(count)d match', 
         '%(name)s - %(count)d matches', count) % {'name': force_unicode(_('customer')), 'count': count}).capitalize()
         })
      result.extend([ {'label':'customer', 'value':i[0]} for i in query[:10] ])
    
  # Search items
  if term and request.user.has_perm('input.change_item'):
    query = Item.objects.using(request.database).filter(name__icontains=term).order_by('name').values_list('name')
    count = len(query)
    if count > 0:
      result.append( {'value': None, 'label': (ungettext(
         '%(name)s - %(count)d match', 
         '%(name)s - %(count)d matches', count) % {'name': force_unicode(_('item')), 'count': count}).capitalize()
         })
      result.extend([ {'label':'item', 'value':i[0]} for i in query[:10] ])
  
  # Search buffers
  if term and request.user.has_perm('input.change_buffer'):
    query = Buffer.objects.using(request.database).filter(name__icontains=term).order_by('name').values_list('name')
    count = len(query)
    if count > 0:
      result.append( {'value': None, 'label': (ungettext(
         '%(name)s - %(count)d match', 
         '%(name)s - %(count)d matches', count) % {'name': force_unicode(_('buffer')), 'count': count}).capitalize()
         })
      result.extend([ {'label':'buffer', 'value':i[0]} for i in query[:10] ])
    
  # Search resources
  if term and request.user.has_perm('input.change_resource'):
    query = Resource.objects.using(request.database).filter(name__icontains=term).order_by('name').values_list('name')
    count = len(query)
    if count > 0:
      result.append( {'value': None, 'label': (ungettext(
         '%(name)s - %(count)d match', 
         '%(name)s - %(count)d matches', count) % {'name': force_unicode(_('resource')), 'count': count}).capitalize()
         })
      result.extend([ {'label':'resource', 'value':i[0]} for i in query[:10] ])
    
  # Search operations
  if term and request.user.has_perm('input.change_operation'):
    query = Operation.objects.using(request.database).filter(name__icontains=term).order_by('name').values_list('name')
    count = len(query)
    if count > 0:
      result.append( {'value': None, 'label': (ungettext(
         '%(name)s - %(count)d match', 
         '%(name)s - %(count)d matches', count) % {'name': force_unicode(_('operation')), 'count': count}).capitalize()
         })
      result.extend([ {'label':'operation', 'value':i[0]} for i in query[:10] ])
    
  # Construct reply
  return HttpResponse(
     mimetype = 'application/json; charset=%s' % settings.DEFAULT_CHARSET,
     content = json.dumps(result, encoding=settings.DEFAULT_CHARSET, ensure_ascii=False)
     )


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
  def getPath(request, objecttype, entity, downstream):
    '''
    A function that recurses upstream or downstream in the supply chain.

    todo: The current code doesn't handle suboperations correctly
    '''

    def addOperation(G, oper, request):
      countsubops = oper.suboperations.select_related(depth=1).using(request.database).count()
      if countsubops > 0:
        subG = G.add_subgraph(name="cluster_O%s" % oper.name, label=oper.name, tooltip=oper.name, rankdir='LR')
        subG.edge_attr['color']='black'
        subG.node_attr['fontsize'] = '8'            
        for x in oper.suboperations.select_related(depth=1).using(request.database).order_by('priority'):
          subG.add_node("O%s" % x.suboperation.name, label=x.suboperation.name, tooltip=x.suboperation.name, shape='rectangle', color='aquamarine')
        return True
      else:
        G.add_node("O%s" % oper.name, label=oper.name, tooltip=oper.name, shape='rectangle', color='aquamarine')
        return False

    from django.core.exceptions import ObjectDoesNotExist
    if objecttype == 'buffer':
      # Find the buffer
      try: root = [ (0, Buffer.objects.using(request.database).get(name=entity), None, None, None, Decimal(1)) ]
      except ObjectDoesNotExist: raise Http404("buffer %s doesn't exist" % entity)
    elif objecttype == 'item':
      # Find the item
      try:
        it = Item.objects.using(request.database).get(name=entity)
        if it.operation:
          root = [ (0, None, None, it.operation, None, Decimal(1)) ]
        else:
          root = [ (0, r, None, None, None, Decimal(1)) for r in Buffer.objects.filter(item=entity).using(request.database) ]
      except ObjectDoesNotExist: raise Http404("item %s doesn't exist" % entity)
    elif objecttype == 'operation':
      # Find the operation
      try: root = [ (0, None, None, Operation.objects.using(request.database).get(name=entity), None, Decimal(1)) ]
      except ObjectDoesNotExist: raise Http404("operation %s doesn't exist" % entity)
    elif objecttype == 'resource':
      # Find the resource
      try: root = Resource.objects.using(request.database).get(name=entity)
      except ObjectDoesNotExist: raise Http404("resource %s doesn't exist" % entity)
      root = [ (0, None, None, i.operation, None, Decimal(1)) for i in root.loads.using(request.database).all() ]
    else:
      raise Http404("invalid entity type %s" % objecttype)

    # Result data structures
    bufs = set()
    ops = set()
    path = []

    # Check the availability of pygraphviz
    try: 
      import pygraphviz
      G = pygraphviz.AGraph(strict=True, directed=True, 
            rankdir="LR", href="javascript:parent.info()", splines='true',
            bgcolor='white', tooltip=" ")  
      G._get_prog("dot")
    except: 
      # Silently fail
      G = None
    
    # Initialize the graph
    if G != None:
      G.edge_attr['color']='black'
      G.node_attr['style'] = 'filled'
      G.node_attr['fontsize'] = '8'

    # Note that the root to start with can be either buffer or operation.
    while len(root) > 0:
      level, curbuffer, curprodflow, curoperation, curconsflow, curqty = root.pop()
      path.append({
        'buffer': curbuffer,
        'producingflow': curprodflow,
        'operation': curoperation,
        'level': abs(level),
        'consumingflow': curconsflow,
        'cumquantity': curqty,
        })

      if G != None:
        if curprodflow: 
          G.add_node("B%s" % curprodflow.thebuffer.name, label=curprodflow.thebuffer.name, tooltip=curprodflow.thebuffer.name, shape='trapezium', color='goldenrod')
          clusterop = addOperation(G, curprodflow.operation, request)
          if curprodflow.quantity > 0:            
            if clusterop: G.edge_attr['lhead'] = "cluster_O%s" % curprodflow.operation.name
            G.add_edge("O%s" % curprodflow.operation.name, "B%s" % curprodflow.thebuffer.name, tooltip=str(curprodflow.quantity), weight='100', label=str(curprodflow.quantity))
          else:
            if clusterop: G.edge_attr['ltail'] = "cluster_O%s" % curprodflow.operation.name
            G.add_edge("B%s" % curprodflow.thebuffer.name, "O%s" % curprodflow.operation.name, tooltip=str(curprodflow.quantity), weight='100', ltail="cluster_O%s" % curprodflow.operation.name,  label=str(curprodflow.quantity))
        if curconsflow: 
          G.add_node("B%s" % curconsflow.thebuffer.name, label=curconsflow.thebuffer.name, tooltip=curconsflow.thebuffer.name, shape='trapezium', color='goldenrod')
          clusterop = addOperation(G, curconsflow.operation, request)
          if curconsflow.quantity > 0:
            if clusterop: G.edge_attr['lhead'] = "cluster_O%s" % curconsflow.operation.name
            G.add_edge("O%s" % curconsflow.operation.name, "B%s" % curconsflow.thebuffer.name, tooltip=str(curconsflow.quantity), weight='100', label=str(curconsflow.quantity))
          else:
            if clusterop: G.edge_attr['ltail'] = "cluster_O%s" % curconsflow.operation.name
            G.add_edge("B%s" % curconsflow.thebuffer.name, "O%s" % curconsflow.operation.name, tooltip=str(curconsflow.quantity), weight='100', label=str(curconsflow.quantity)) 

      # Avoid infinite loops when the supply chain contains cycles
      if curbuffer:
        if curbuffer in bufs: continue
      else:
        if curoperation and curoperation in ops: continue

      if curprodflow: 
        ops.add(curprodflow.operation)          
      if curconsflow: 
        ops.add(curconsflow.operation)
      if curbuffer: 
        bufs.add(curbuffer)          
      if curoperation: 
        ops.add(curoperation)        
        if G != None:
          clusterop = addOperation(G, curoperation, request)
          for i in curoperation.loads.all():
            G.add_node("R%s" % i.resource.name, tooltip=i.resource.name, label=i.resource.name, shape='hexagon', color='lightblue')
            G.add_edge("O%s" % curoperation.name, "R%s" % i.resource.name, label=str(i.quantity), tooltip=str(i.quantity), style='dashed', dir='none', weight='100')

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
            if not len(start):
              # Not generic... 
              start = [ (i, i.operation) for i in curbuffer.flows.filter(quantity__gt=0).select_related(depth=1).using(request.database) ]
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
              if cons_flow.operation in ops: continue
              ok = True
              root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          # Push the next buffer on the stack, based on sub-operations
          for x in curoperation.suboperations.select_related(depth=1).using(request.database):
            for cons_flow in x.suboperation.flows.filter(quantity__lt=0).using(request.database):
              if cons_flow.operation in ops: continue
              ok = True
              root.append( (level-1, cons_flow.thebuffer, prod_flow, cons_flow.operation, cons_flow, curqty / (prod_flow and prod_flow.quantity or 1) * cons_flow.quantity * -1) )

          if not ok and prod_flow:
            # No consuming flow found: there are no more buffers upstream
            ok = True
            root.append( (level-1, None, prod_flow, prod_flow.operation, None, curqty / prod_flow.quantity) )
          if not ok:
            # An operation without any flows (on itself, any of its suboperations or any of its superoperations)
            for x in curoperation.suboperations.using(request.database):
              if not x.suboperation in ops: root.append( (level-1, None, None, x.suboperation, None, curqty) )
            for x in curoperation.superoperations.using(request.database):
              if not x.operation in ops: root.append( (level-1, None, None, x.operation, None, curqty) )
    
    # Layout the graph
    #G.write("test.dot")
    if G != None: G.layout(prog='dot')
    
    # Final result
    return render_to_response('input/path.html', RequestContext(request,{
       'title': capfirst(force_unicode(_(objecttype)) + " " + entity),
       'supplypath': path,
       'model': objecttype,
       'object_id': entity,
       'downstream': downstream,
       'active_tab': downstream and 'whereused' or 'supplypath',
       'graphdata': G!=None and G.draw(format="svg") or ""
       }))    
          
    
  @staticmethod
  @staff_member_required
  def viewdownstream(request, model, object_id):
    return pathreport.getPath(request, model, object_id, True)

  @staticmethod
  @staff_member_required
  def viewupstream(request, model, object_id):
    return pathreport.getPath(request, model, object_id, False)


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


class BufferList(GridReport):
  '''
  A list report to show buffers.
  '''
  template = 'input/bufferlist.html'
  title = _("Buffer List")
  basequeryset = Buffer.objects.all()
  model = Buffer
  frozenColumns = 1

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='buffer'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='location'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='item'),
    GridFieldNumber('onhand', title=_('onhand')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='buffer'),
    GridFieldChoice('type', title=_('type'), choices=Buffer.types),
    GridFieldNumber('minimum', title=_('minimum')),
    GridFieldText('minimum_calendar', title=_('minimum calendar'), field_name='minimum_calendar__name', formatter='calendar'),
    GridFieldText('producing', title=_('producing'), field_name='producing__name', formatter='operation'),
    GridFieldNumber('carrying_cost', title=_('carrying cost')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldText('name', title=_('name'), key=True),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='resource'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='location'),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='resource'),
    GridFieldChoice('type', title=_('type'), choices=Resource.types),
    GridFieldNumber('maximum', title=_('maximum')),
    GridFieldText('maximum_calendar', title=_('maximum calendar'), field_name='maximum_calendar__name', formatter='calendar'),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldNumber('maxearly', title=_('maxearly')),
    GridFieldText('setupmatrix', title=_('setup matrix'), formatter='setupmatrix'),
    GridFieldText('setup', title=_('setup')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='location'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('available', title=_('available'), field_name='available__name', formatter='calendar'),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='location'),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='customer'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='customer'),
    GridFieldLastModified('lastmodified'),
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
  editable = True

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='item'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    GridFieldText('owner', title=_('owner'), field_name='owner__name'),
    GridFieldCurrency('price', title=_('price')),
    GridFieldLastModified('lastmodified'),
    )


class SkillList(GridReport):
  '''
  A list report to show skills.
  '''
  template = 'input/skilllist.html'
  title = _("Skill List")
  basequeryset = Skill.objects.all()
  model = Skill
  frozenColumns = 1

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='skill'),
    GridFieldLastModified('lastmodified'),
    )


class ResourceSkillList(GridReport):
  '''
  A list report to show resource skills.
  '''
  template = 'input/resourceskilllist.html'
  title = _("Resource skill List")
  basequeryset = ResourceSkill.objects.all()
  model = ResourceSkill
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='resourceskill'),
    GridFieldText('resource', title=_('resource'), formatter='resource'),
    GridFieldText('skill', title=_('skill'), formatter='skill'),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldNumber('priority', title=_('priority')),	
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='load'),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', formatter='resource'),
    GridFieldText('skill', title=_('skill'), formatter='skill'),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('name', title=_('name')),
    GridFieldText('alternate', title=_('alternate')),
    GridFieldNumber('priority', title=_('priority')),
    GridFieldText('setup', title=_('setup')),
    GridFieldText('search', title=_('search mode')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='flow'),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    GridFieldText('thebuffer', title=_('buffer'), field_name='thebuffer__name', formatter='buffer'),
    GridFieldChoice('type', title=_('type'), choices=Flow.types),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('name', title=_('name')),
    GridFieldText('alternate', title=_('alternate')),
    GridFieldNumber('priority', title=_('priority')),
    GridFieldText('search', title=_('search mode')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='demand'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='item'),
    GridFieldText('customer', title=_('customer'), field_name='customer__name', formatter='customer'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldDateTime('due', title=_('due')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldText('operation', title=_('delivery operation'), formatter='operation'),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldText('owner', title=_('owner'), formatter='demand'),
    GridFieldNumber('maxlateness', title=_('maximum lateness')),
    GridFieldNumber('minshipment', title=_('minimum shipment')),
    GridFieldLastModified('lastmodified'),
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
    GridFieldText('name', title=_('name'), key=True, formatter='calendar'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldNumber('defaultvalue', title=_('default value')),
    GridFieldLastModified('lastmodified'),
    )


class CalendarBucketList(GridReport):
  '''
  A list report to show calendar buckets.
  '''
  template = 'input/calendarbucketlist.html'
  title = _("Calendar Bucket List")
  basequeryset = CalendarBucket.objects.all()
  model = CalendarBucket
  frozenColumns = 3
  rows = (
    GridFieldInteger('id', title=_('identifier')),
    GridFieldText('calendar', title=_('calendar'), field_name='calendar__name', formatter='calendar'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date'),editable=False),
    GridFieldNumber('value', title=_('value')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldBool('monday', title=_('Monday')),
    GridFieldBool('tuesday', title=_('Tuesday')),
    GridFieldBool('wednesday', title=_('Wednesday')),
    GridFieldBool('thursday', title=_('Thursday')),
    GridFieldBool('friday', title=_('Friday')),
    GridFieldBool('saturday', title=_('Saturday')),
    GridFieldBool('sunday', title=_('Sunday')),
    GridFieldTime('starttime', title=_('start time')),
    GridFieldTime('endtime', title=_('end time')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='operation'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldChoice('type', title=_('type'), choices=Operation.types),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='location'),
    GridFieldNumber('duration', title=_('duration')),
    GridFieldNumber('duration_per', title=_('duration per unit')),
    GridFieldNumber('fence', title=_('release fence')),
    GridFieldNumber('pretime', title=_('pre-op time')),
    GridFieldNumber('posttime', title=_('post-op time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldNumber('sizemaximum', title=_('size maximum')),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldText('search', title=_('search mode')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    GridFieldText('suboperation', title=_('suboperation'), field_name='suboperation__name', formatter='operation'),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldLastModified('lastmodified'),
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

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='operation'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldBool('locked', title=_('locked')),
    GridFieldInteger('owner', title=_('owner'), extra="formatoptions:{defaultValue:''}"),
    GridFieldLastModified('lastmodified'),
    )
