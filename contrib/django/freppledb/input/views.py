#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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

import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.db.models.fields import CharField
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.utils.encoding import iri_to_uri, force_text
from django.utils.text import capfirst

from freppledb.input.models import Resource, Operation, Location, SetupMatrix
from freppledb.input.models import Buffer, Customer, Demand, Item, Load, Flow, Skill
from freppledb.input.models import Calendar, CalendarBucket, OperationPlan, SubOperation
from freppledb.input.models import ResourceSkill, Supplier, searchmode
from freppledb.common.report import GridReport, GridFieldBool, GridFieldLastModified
from freppledb.common.report import GridFieldDateTime, GridFieldTime, GridFieldText
from freppledb.common.report import GridFieldNumber, GridFieldInteger, GridFieldCurrency
from freppledb.common.report import GridFieldChoice, GridFieldDuration
from freppledb.admin import data_site


@staff_member_required
def search(request):
  term = request.GET.get('term')
  result = []

  # Loop over all models in the data_site
  # We are interested in models satisfying these criteria:
  #  - primary key is of type text
  #  - user has change permissions
  for cls, admn in data_site._registry.items():
    if admn.has_change_permission(request) and isinstance(cls._meta.pk, CharField):
      query = cls.objects.using(request.database).filter(pk__icontains=term).order_by('pk').values_list('pk')
      count = len(query)
      if count > 0:
        result.append( {'value': None, 'label': (ungettext(
           '%(name)s - %(count)d match',
           '%(name)s - %(count)d matches', count) % {'name': force_text(cls._meta.verbose_name), 'count': count}).capitalize()
           })
        result.extend([ {
          'label': cls._meta.object_name.lower(),
          'value': i[0],
          'app': cls._meta.app_label
          } for i in query[:10] ])

  # Construct reply
  return HttpResponse(
     mimetype='application/json; charset=%s' % settings.DEFAULT_CHARSET,
     content=json.dumps(result).encode(settings.DEFAULT_CHARSET)
     )


class PathReport(GridReport):
  '''
  A report showing the upstream supply path or following downstream a
  where-used path.
  The supply path report shows all the materials, operations and resources
  used to make a certain item.
  The where-used report shows all the materials and operations that use
  a specific item.
  '''
  template = 'input/path.html'
  title = _("Supply path")
  filterable = False
  frozenColumns = 0
  editable = False
  default_sort = None
  multiselect = False
  rows = (
    GridFieldText('depth', title=_('depth'), editable=False, sortable=False),
    GridFieldText('operation', title=_('operation'), formatter='operation', editable=False, sortable=False),
    GridFieldNumber('quantity', title=_('quantity'), editable=False, sortable=False),
    GridFieldText('location', title=_('location'), editable=False, sortable=False),
    GridFieldText('type', title=_('type'), editable=False, sortable=False),
    GridFieldDuration('duration', title=_('duration'), editable=False, sortable=False),
    GridFieldDuration('duration_per', title=_('duration per unit'), editable=False, sortable=False),
    GridFieldText('resources', editable=False, sortable=False, extra='formatter:reslistfmt'),
    GridFieldText('buffers', editable=False, sortable=False, hidden=True),
    GridFieldText('suboperation', editable=False, sortable=False, hidden=True),
    GridFieldText('numsuboperations', editable=False, sortable=False, hidden=True),
    GridFieldText('parentoper', editable=False, sortable=False, hidden=True),
    GridFieldText('realdepth', editable=False, sortable=False, hidden=True),
    GridFieldText('id', editable=False, sortable=False, hidden=True),
    GridFieldText('parent', editable=False, sortable=False, hidden=True),
    GridFieldText('leaf', editable=False, sortable=False, hidden=True),
    GridFieldText('expanded', editable=False, sortable=False, hidden=True),
    )

  # Attributes to be specified by the subclasses
  objecttype = None
  downstream = None


  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    return reportclass.objecttype.objects.filter(name__exact=args[0]).values('name')


  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    return {
      'title': capfirst(
        force_text(reportclass.objecttype._meta.verbose_name) + " " + args[0] +
        ": " + force_text(reportclass.downstream and _("Where Used") or _("Supply Path"))
        ),
      'downstream': reportclass.downstream,
      'active_tab': reportclass.downstream and 'whereused' or 'supplypath',
      'model': reportclass.objecttype.__name__.lower
      }


  @classmethod
  def query(reportclass, request, basequery):
    '''
    A function that recurses upstream or downstream in the supply chain.
    '''
    from django.core.exceptions import ObjectDoesNotExist
    entity = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=True)[1]
    entity = entity[0]
    if reportclass.objecttype == Buffer:
      # Find the buffer
      try:
        buf = Buffer.objects.using(request.database).get(name=entity)
        if reportclass.downstream:
          root = [
            (0, None, i.operation, 1, 0, None, 0, True)
            for i in buf.flows.filter(quantity__lt=0).select_related(depth=1).using(request.database)
            ]
        else:
          if buf.producing:
            root = [ (0, None, buf.producing, 1, 0, None, 0, False) ]
          else:
            root = []
      except ObjectDoesNotExist:
        raise Http404("buffer %s doesn't exist" % entity)
    elif reportclass.objecttype == Item:
      # Find the item
      try:
        it = Item.objects.using(request.database).get(name=entity)
        if it.operation:
          root = [ (0, None, it.operation, 1, 0, None, 0, False) ]
        else:
          root = [
            (0, None, r.producing, 1, 0, None, 0, False)
            for r in Buffer.objects.filter(item=entity).using(request.database)
            if r.producing
            ]
      except ObjectDoesNotExist:
        raise Http404("item %s doesn't exist" % entity)
    elif reportclass.objecttype == Operation:
      # Find the operation
      try:
        root = [ (0, None, Operation.objects.using(request.database).get(name=entity), 1, 0, None, 0, True) ]
      except ObjectDoesNotExist:
        raise Http404("operation %s doesn't exist" % entity)
    elif reportclass.objecttype == Resource:
      # Find the resource
      try:
        root = Resource.objects.using(request.database).get(name=entity)
      except ObjectDoesNotExist:
        raise Http404("resource %s doesn't exist" % entity)
      root = [ (0, None, i.operation, 1, 0, None, 0, True) for i in root.loads.using(request.database).all() ]
    else:
      raise Http404("invalid entity type")

    # Recurse over all operations
    counter = 1
    #operations = set()
    while len(root) > 0:
      # Pop the current node from the stack
      level, parent, curoperation, curqty, issuboperation, parentoper, realdepth, pushsuper = root.pop()
      curnode = counter
      counter += 1

      # If an operation has parent operations we forget about the current operation
      # and use only the parent
      if pushsuper:
        hasParents = False
        for x in curoperation.superoperations.using(request.database).order_by("-priority"):
          root.append( (level, parent, x.operation, curqty, issuboperation, parentoper, realdepth, False) )
          hasParents = True
        if hasParents:
          continue

      # Avoid showing the same operation twice.
      # This feature is disabled by default a) because it is not intuitive to understand
      # where operations are skipped, and b) because the quantity of each occurrence might
      # be different.
      # In some models the duplication is confusing and you can enable this feature.
      #if curoperation in operations: continue
      #operations.add(curoperation)

      # Find the next level
      hasChildren = False
      subcount = 0
      if reportclass.downstream:
        # Downstream recursion
        for x in curoperation.flows.filter(quantity__gt=0).select_related(depth=1).using(request.database):
          curflows = x.thebuffer.flows.filter(quantity__lt=0).select_related(depth=1).using(request.database)
          for y in curflows:
            hasChildren = True
            root.append( (level - 1, curnode, y.operation, - curqty * y.quantity, subcount, None, realdepth - 1, pushsuper) )
        for x in curoperation.suboperations.using(request.database).order_by("-priority"):
          subcount += curoperation.type == "routing" and 1 or -1
          root.append( (level - 1, curnode, x.suboperation, curqty, subcount, curoperation, realdepth, False) )
          hasChildren = True
      else:
        # Upstream recursion
        curprodflow = None
        for x in curoperation.flows.filter(quantity__gt=0).select_related(depth=1).using(request.database):
          curprodflow = x
        curflows = curoperation.flows.filter(quantity__lt=0).select_related(depth=1).using(request.database)
        for y in curflows:
          if y.thebuffer.producing:
            hasChildren = True
            root.append( (
              level + 1, curnode, y.thebuffer.producing,
              curprodflow and (-curqty * y.quantity) / curprodflow.quantity or (-curqty * y.quantity),
              subcount, None, realdepth + 1, True
              ) )
        for x in curoperation.suboperations.using(request.database).order_by("-priority"):
          subcount += curoperation.type == "routing" and 1 or -1
          root.append( (level + 1, curnode, x.suboperation, curqty, subcount, curoperation, realdepth, False) )
          hasChildren = True

      # Process the current node
      yield {
        'depth': abs(level),
        'id': curnode,
        'operation': curoperation.name,
        'type': curoperation.type,
        'location': curoperation.location and curoperation.location.name or '',
        'duration': curoperation.duration,
        'duration_per': curoperation.duration_per,
        'quantity': curqty,
        'suboperation': issuboperation,
        'buffers': [ (x.thebuffer.name, float(x.quantity)) for x in curoperation.flows.using(request.database) ],
        'resources': [ (x.resource.name, float(x.quantity)) for x in curoperation.loads.using(request.database) ],
        'parentoper': parentoper and parentoper.name,
        'parent': parent,
        'leaf': hasChildren and 'false' or 'true',
        'expanded': 'true',
        'numsuboperations': subcount,
        'realdepth': realdepth
        }


class UpstreamItemPath(PathReport):
  downstream = False
  objecttype = Item


class UpstreamBufferPath(PathReport):
  downstream = False
  objecttype = Buffer


class UpstreamResourcePath(PathReport):
  downstream = False
  objecttype = Resource


class UpstreamOperationPath(PathReport):
  downstream = False
  objecttype = Operation


class DownstreamItemPath(PathReport):
  downstream = True
  objecttype = Item


class DownstreamBufferPath(PathReport):
  downstream = True
  objecttype = Buffer


class DownstreamResourcePath(PathReport):
  downstream = True
  objecttype = Resource


class DownstreamOperationPath(PathReport):
  downstream = True
  objecttype = Operation


@staff_member_required
def location_calendar(request, location):
  # Check to find a location availability calendar
  loc = Location.objects.using(request.database).get(pk=location)
  if loc:
    cal = loc.available
  if cal:
    # Go to the calendar
    return HttpResponseRedirect('%s/data/input/calendar/%s/' % (request.prefix, iri_to_uri(cal.name)) )
  # Generate a message
  try:
    url = request.META.get('HTTP_REFERER')
    messages.add_message(
      request, messages.ERROR,
      force_text(_('No availability calendar found'))
      )
    return HttpResponseRedirect(url)
  except:
    raise Http404


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
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldDuration('maxearly', title=_('maxearly')),
    GridFieldText('setupmatrix', title=_('setup matrix'), formatter='setupmatrix'),
    GridFieldText('setup', title=_('setup')),
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class SupplierList(GridReport):
  '''
  A list report to show supplier.
  '''
  template = 'input/supplierlist.html'
  title = _("Supplier List")
  basequeryset = Supplier.objects.all()
  model = Supplier
  frozenColumns = 1

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='supplier'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='supplier'),
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldChoice('search', title=_('search mode'), choices=searchmode),
    GridFieldText('source', title=_('source')),
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
    GridFieldChoice('search', title=_('search mode'), choices=searchmode),
    GridFieldText('source', title=_('source')),
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
    GridFieldChoice('status', title=_('status'), choices=Demand.demandstatus),
    GridFieldDuration('maxlateness', title=_('maximum lateness')),
    GridFieldNumber('minshipment', title=_('minimum shipment')),
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldInteger('id', title=_('identifier'), formatter='calendarbucket'),
    GridFieldText('calendar', title=_('calendar'), field_name='calendar__name', formatter='calendar'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date'), editable=False),
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
    GridFieldText('source', title=_('source')),  # Not really right, since the engine doesn't read or store it
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
    GridFieldDuration('duration', title=_('duration')),
    GridFieldDuration('duration_per', title=_('duration per unit')),
    GridFieldDuration('fence', title=_('release fence')),
    GridFieldDuration('posttime', title=_('post-op time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldNumber('sizemaximum', title=_('size maximum')),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldChoice('search', title=_('search mode'), choices=searchmode),
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
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
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )
