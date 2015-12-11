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

import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.db.models.fields import CharField
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.utils.encoding import force_text
from django.utils.text import capfirst

from freppledb.input.models import Resource, Operation, Location, SetupMatrix
from freppledb.input.models import Buffer, Customer, Demand, Item, Load, Flow, Skill
from freppledb.input.models import Calendar, CalendarBucket, OperationPlan, SubOperation
from freppledb.input.models import ResourceSkill, Supplier, ItemSupplier, searchmode
from freppledb.input.models import ItemDistribution, DistributionOrder, PurchaseOrder
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
    if request.user.has_perm("%s.view_%s" % (cls._meta.app_label, cls._meta.object_name.lower())) and isinstance(cls._meta.pk, CharField):
      query = cls.objects.using(request.database).filter(pk__icontains=term).order_by('pk').values_list('pk')
      count = len(query)
      if count > 0:
        result.append( {'value': None, 'label': (ungettext(
           '%(name)s - %(count)d match',
           '%(name)s - %(count)d matches', count) % {'name': force_text(cls._meta.verbose_name), 'count': count}).capitalize()
           })
        result.extend([ {
          'url': "/data/%s/%s/" % (cls._meta.app_label, cls._meta.object_name.lower()),
          'value': i[0]
          } for i in query[:10] ])

  # Construct reply
  return HttpResponse(
     content_type='application/json; charset=%s' % settings.DEFAULT_CHARSET,
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
    GridFieldText('operation', title=_('operation'), editable=False, sortable=False, formatter='detail', extra="role:'input/operation'"),
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
    if reportclass.downstream:
      request.session['lasttab'] = 'whereused'
    else:
      request.session['lasttab'] = 'supplypath'
    return {
      'title': capfirst(
        force_text(reportclass.objecttype._meta.verbose_name) + " " + args[0] +
        ": " + force_text(reportclass.downstream and _("Where Used") or _("Supply Path"))
        ),
      'downstream': reportclass.downstream,
      'active_tab': reportclass.downstream and 'whereused' or 'supplypath',
      'model': reportclass.objecttype._meta
      }


  @classmethod
  def getRoot(reportclass, request, entity):
    raise Http404("invalid entity type")


  @classmethod
  def findDeliveries(reportclass, item, location, db):
    # Automatically detect delivery operations. This is done by looking for
    # a buffer for this item and location combination. (Special case is when
    # there is only a single location in the model, in which case only a match
    # on the item is sufficient.)
    # If this buffer results in a single buffer, we call the method to pick up
    # its replenishing operations.
    buf = None
    if location:
      for b in Buffer.objects.using(db).filter(item=item, location=location):
        if buf:
          # More than 1 buffer found
          return []
        else:
          # First buffer found
          buf = b
    else:
      if Location.objects.using(db).count() > 1:
        return []
      # Special case: only 1 location exists, and a match on the item is enough
      for b in Buffer.objects.using(db).filter(item=item):
        if buf:
          # More than 1 buffer found
          return []
        else:
          # First buffer found
          buf = b
    return reportclass.findReplenishment(buf, db, 0, 1, 0, False)


  @classmethod
  def findUsage(reportclass, buffer, db, level, curqty, realdepth, pushsuper):
    result = [
      (level + 1, None, i.operation, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
      for i in buffer.flows.filter(quantity__lt=0).only('operation').using(db)
      ]
    result.extend([
      (level + 1, None, i, curqty, 0, None, realdepth, pushsuper, i.location.name if i.location else None)
      for i in ItemDistribution.objects.using(db).filter(
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft,
        origin__lft__lte=buffer.location.lft, origin__rght__gt=buffer.location.lft
        )
      ])
    return result


  @classmethod
  def findReplenishment(reportclass, buffer, db, level, curqty, realdepth, pushsuper):
    # If a producing operation is set on the buffer, we use that and skip the
    # automated search described below.
    # If no producing operation is set, we look for item distribution and
    # item supplier models for the item and location combination. (As a special
    # case in case only a single location exists in the model, a match on the
    # item is sufficient).
    if buffer.producing:
      return [ (level, None, buffer.producing, curqty, 0, None, realdepth, pushsuper, buffer.producing.location.name if buffer.producing.location else None) ]
    result = []
    if Location.objects.using(db).count() > 1:
      # Multiple locations
      result.extend([
        (level, None, i, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
        for i in ItemSupplier.objects.using(db).filter(
          Q(location__isnull=True) | (Q(location__lft__lte=buffer.location.lft) & Q(location__rght__gt=buffer.location.lft)),
          item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft
          )
        ])
      # TODO if the itemdistribution is at an aggregate location level, we should loop over all child locations
      result.extend([
        (level, None, i, curqty, 0, None, realdepth, pushsuper, i.origin.name if i.origin else None)
        for i in ItemDistribution.objects.using(db).filter(
          item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft,
          location__lft__lte=buffer.location.lft, location__rght__gt=buffer.location.lft
          )
        ])
    else:
      # Single location, and itemdistributions obviously aren't defined here
      result.extend([
        (level, None, i, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
        for i in ItemSupplier.objects.using(db).filter(
          item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.rght
          )
        ])
    return result


  @classmethod
  def query(reportclass, request, basequery):
    '''
    A function that recurses upstream or downstream in the supply chain.
    '''
    entity = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)[1]
    entity = entity[0]
    root = reportclass.getRoot(request, entity)

    # Update item and location hierarchies
    Item.rebuildHierarchy(database=request.database)
    Location.rebuildHierarchy(database=request.database)

    # Recurse over all operations
    # TODO the current logic isn't generic enough. A lot of buffers may not be explicitly
    # defined, and are created on the fly by deliveries, itemsuppliers or itemdistributions.
    # Currently we don't account for such situations.
    # TODO usage search doesn't find item distributions from that location
    counter = 1
    #operations = set()
    while len(root) > 0:
      # Pop the current node from the stack
      level, parent, curoperation, curqty, issuboperation, parentoper, realdepth, pushsuper, location = root.pop()
      curnode = counter
      counter += 1

      # If an operation has parent operations we forget about the current operation
      # and use only the parent
      if pushsuper and not isinstance(curoperation, (ItemSupplier, ItemDistribution)):
        hasParents = False
        for x in curoperation.superoperations.using(request.database).only('operation').order_by("-priority"):
          root.append( (level, parent, x.operation, curqty, issuboperation, parentoper, realdepth, False, location) )
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
        if isinstance(curoperation, ItemSupplier):
          name = 'Purchase %s @ %s from %s' % (curoperation.item.name, location, curoperation.supplier.name)
          optype = "purchase"
          duration = curoperation.leadtime
          duration_per = None
          buffers = [ ("%s @ %s" % (curoperation.item.name, curoperation.location.name), 1), ]
          resources = None
          try:
            downstr = Buffer.objects.using(request.database).get(name="%s @ %s" % (curoperation.item.name, curoperation.location.name))
            root.extend( reportclass.findUsage(downstr, request.database, level, curqty, realdepth + 1, False, location) )
          except Buffer.DoesNotExist:
            pass
        elif isinstance(curoperation, ItemDistribution):
          name = 'Ship %s from %s to %s' % (curoperation.item.name, curoperation.origin.name, curoperation.location.name)
          optype = "distribution"
          duration = curoperation.leadtime
          duration_per = None
          buffers = [
            ("%s @ %s" % (curoperation.item.name, curoperation.origin.name), -1),
            ("%s @ %s" % (curoperation.item.name, curoperation.location.name), 1)
            ]
          resources = None
        else:
          name = curoperation.name
          optype = curoperation.type
          duration = curoperation.duration
          duration_per = curoperation.duration_per
          buffers = [ (x.thebuffer.name, float(x.quantity)) for x in curoperation.flows.only('thebuffer', 'quantity').using(request.database) ]
          resources = [ (x.resource.name, float(x.quantity)) for x in curoperation.loads.only('resource', 'quantity').using(request.database) ]
          for x in curoperation.flows.filter(quantity__gt=0).only('thebuffer').using(request.database):
            curflows = x.thebuffer.flows.filter(quantity__lt=0).only('operation', 'quantity').using(request.database)
            for y in curflows:
              hasChildren = True
              root.append( (level - 1, curnode, y.operation, - curqty * y.quantity, subcount, None, realdepth - 1, pushsuper, x.thebuffer.location.name if x.thebuffer.location else None) )
          for x in curoperation.suboperations.using(request.database).only('suboperation').order_by("-priority"):
            subcount += curoperation.type == "routing" and 1 or -1
            root.append( (level - 1, curnode, x.suboperation, curqty, subcount, curoperation, realdepth, False, location) )
            hasChildren = True
      else:
        # Upstream recursion
        if isinstance(curoperation, ItemSupplier):
          name = 'Purchase %s @ %s from %s' % (curoperation.item.name, location, curoperation.supplier.name)
          optype = "purchase"
          duration = curoperation.leadtime
          duration_per = None
          buffers = [ ("%s @ %s" % (curoperation.item.name, location), 1), ]
          resources = None
        elif isinstance(curoperation, ItemDistribution):
          name = 'Ship %s from %s to %s' % (curoperation.item.name, curoperation.origin.name, location)
          optype = "distribution"
          duration = curoperation.leadtime
          duration_per = None
          buffers = [
            ("%s @ %s" % (curoperation.item.name, curoperation.origin.name), -1),
            ("%s @ %s" % (curoperation.item.name, curoperation.location.name), 1)
            ]
          resources = None
          try:
            upstr = Buffer.objects.using(request.database).get(name="%s @ %s" % (curoperation.item.name, curoperation.origin.name))
            root.extend( reportclass.findReplenishment(upstr, request.database, level + 2, curqty, realdepth + 1, False) )
          except Buffer.DoesNotExist:
            pass
        else:
          curprodflow = None
          name = curoperation.name
          optype = curoperation.type
          duration = curoperation.duration
          duration_per = curoperation.duration_per
          buffers = [ (x.thebuffer.name, float(x.quantity)) for x in curoperation.flows.only('thebuffer', 'quantity').using(request.database) ]
          resources = [ (x.resource.name, float(x.quantity)) for x in curoperation.loads.only('resource', 'quantity').using(request.database) ]
          for x in curoperation.flows.filter(quantity__gt=0).only('quantity').using(request.database):
            curprodflow = x
          curflows = curoperation.flows.filter(quantity__lt=0).only('thebuffer', 'quantity').using(request.database)
          for y in curflows:
            if y.thebuffer.producing:
              hasChildren = True
              root.append( (
                level + 1, curnode, y.thebuffer.producing,
                curprodflow and (-curqty * y.quantity) / curprodflow.quantity or (-curqty * y.quantity),
                subcount, None, realdepth + 1, True, y.thebuffer.location
                ) )
            else:
              root.extend( reportclass.findReplenishment(y.thebuffer, request.database, level + 2, curqty, realdepth + 1, False) )
          for x in curoperation.suboperations.using(request.database).only('suboperation').order_by("-priority"):
            subcount += curoperation.type == "routing" and 1 or -1
            root.append( (level + 1, curnode, x.suboperation, curqty, subcount, curoperation, realdepth, False, location) )
            hasChildren = True

      # Process the current node
      yield {
        'depth': abs(level),
        'id': curnode,
        'operation': name,
        'type': optype,
        'location': curoperation.location and curoperation.location.name or '',
        'duration': duration,
        'duration_per': duration_per,
        'quantity': curqty,
        'suboperation': issuboperation,
        'buffers': buffers,
        'resources': resources,
        'parentoper': parentoper and parentoper.name,
        'parent': parent,
        'leaf': hasChildren and 'false' or 'true',
        'expanded': 'true',
        'numsuboperations': subcount,
        'realdepth': realdepth
        }


class UpstreamDemandPath(PathReport):
  downstream = False
  objecttype = Demand

  @classmethod
  def getRoot(reportclass, request, entity):
    from django.core.exceptions import ObjectDoesNotExist

    try:
      dmd = Demand.objects.using(request.database).get(name=entity)
    except ObjectDoesNotExist:
      raise Http404("demand %s doesn't exist" % entity)

    if dmd.operation:
      # Delivery operation on the demand
      return [ (0, None, dmd.operation, 1, 0, None, 0, False, None) ]
    elif dmd.item.operation:
      # Delivery operation on the item
      return [ (0, None, dmd.item.operation, 1, 0, None, 0, False, None) ]
    else:
      # Autogenerated delivery operation
      try:
        return reportclass.findDeliveries(dmd.item, dmd.location, request.database)
      except:
        raise Http404("No supply path defined for demand %s" % entity)


class UpstreamItemPath(PathReport):
  downstream = False
  objecttype = Item

  @classmethod
  def getRoot(reportclass, request, entity):
    from django.core.exceptions import ObjectDoesNotExist
    try:
      it = Item.objects.using(request.database).get(name=entity)
      if reportclass.downstream:
        # Find all buffers where the item is being stored and walk downstream
        result = []
        for b in Buffer.objects.filter(item=it).using(request.database):
          result.extend( reportclass.findUsage(b, request.database, 0, 1, 0, False) )
        return result
      else:
        if it.operation:
          # Delivery operation on the item
          return [ (0, None, it.operation, 1, 0, None, 0, False, None) ]
        else:
          # Find the supply path of all buffers of this item
          result = []
          for b in Buffer.objects.filter(item=entity).using(request.database):
            result.extend( reportclass.findReplenishment(b, request.database, 0, 1, 0, False) )
          return result
    except ObjectDoesNotExist:
      raise Http404("item %s doesn't exist" % entity)


class UpstreamBufferPath(PathReport):
  downstream = False
  objecttype = Buffer

  @classmethod
  def getRoot(reportclass, request, entity):
    from django.core.exceptions import ObjectDoesNotExist
    try:
      buf = Buffer.objects.using(request.database).get(name=entity)
      if reportclass.downstream:
        return reportclass.findUsage(buf, request.database, 0, 1, 0, False)
      else:
        return reportclass.findReplenishment(buf, request.database, 0, 1, 0, False)
    except ObjectDoesNotExist:
      raise Http404("buffer %s doesn't exist" % entity)


class UpstreamResourcePath(PathReport):
  downstream = False
  objecttype = Resource

  @classmethod
  def getRoot(reportclass, request, entity):
    from django.core.exceptions import ObjectDoesNotExist
    try:
      root = Resource.objects.using(request.database).get(name=entity)
    except ObjectDoesNotExist:
      raise Http404("resource %s doesn't exist" % entity)
    return [
      (0, None, i.operation, 1, 0, None, 0, True, i.operation.location.name if i.operation.location else None)
      for i in root.loads.using(request.database).all()
      ]


class UpstreamOperationPath(PathReport):
  downstream = False
  objecttype = Operation

  @classmethod
  def getRoot(reportclass, request, entity):
    from django.core.exceptions import ObjectDoesNotExist
    try:
      oper = Operation.objects.using(request.database).get(name=entity)
      return [ (0, None, oper, 1, 0, None, 0, True, oper.location.name if oper.location else None) ]
    except ObjectDoesNotExist:
      raise Http404("operation %s doesn't exist" % entity)


class DownstreamItemPath(UpstreamItemPath):
  downstream = True
  objecttype = Item


class DownstreamDemandPath(UpstreamDemandPath):
  downstream = True
  objecttype = Demand


class DownstreamBufferPath(UpstreamBufferPath):
  downstream = True
  objecttype = Buffer


class DownstreamResourcePath(UpstreamResourcePath):
  downstream = True
  objecttype = Resource


class DownstreamOperationPath(UpstreamOperationPath):
  downstream = True
  objecttype = Operation


class BufferList(GridReport):
  '''
  A list report to show buffers.
  '''

  title = _("buffers")
  basequeryset = Buffer.objects.all()
  model = Buffer
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/buffer'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra="role:'input/location'"),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra="role:'input/item'"),
    GridFieldNumber('onhand', title=_('onhand')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra="role:'input/buffer'"),
    GridFieldChoice('type', title=_('type'), choices=Buffer.types),
    GridFieldNumber('minimum', title=_('minimum')),
    GridFieldText('minimum_calendar', title=_('minimum calendar'), field_name='minimum_calendar__name', formatter='detail', extra="role:'input/calendar'"),
    GridFieldText('producing', title=_('producing'), field_name='producing__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class SetupMatrixList(GridReport):
  '''
  A list report to show setup matrices.
  '''
  title = _("setup matrices")
  basequeryset = SetupMatrix.objects.all()
  model = SetupMatrix
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/setupmatrix'"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class ResourceList(GridReport):
  '''
  A list report to show resources.
  '''
  title = _("resources")
  basequeryset = Resource.objects.all()
  model = Resource
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/resource'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra="role:'input/location'"),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra="role:'input/resource'"),
    GridFieldChoice('type', title=_('type'), choices=Resource.types),
    GridFieldNumber('maximum', title=_('maximum')),
    GridFieldText('maximum_calendar', title=_('maximum calendar'), field_name='maximum_calendar__name', formatter='detail', extra="role:'input/calendar'"),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldDuration('maxearly', title=_('maxearly')),
    GridFieldText('setupmatrix', title=_('setup matrix'), formatter='detail', extra="role:'input/setupmatrix'"),
    GridFieldText('setup', title=_('setup')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class LocationList(GridReport):
  '''
  A list report to show locations.
  '''
  title = _("locations")
  basequeryset = Location.objects.all()
  model = Location
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/location'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('available', title=_('available'), field_name='available__name', formatter='detail', extra="role:'input/calendar'"),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra="role:'input/location'"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class CustomerList(GridReport):
  '''
  A list report to show customers.
  '''
  title = _("customers")
  basequeryset = Customer.objects.all()
  model = Customer
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/customer'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra="role:'input/customer'"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class SupplierList(GridReport):
  '''
  A list report to show supplier.
  '''
  title = _("suppliers")
  basequeryset = Supplier.objects.all()
  model = Supplier
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/supplier'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra="role:'input/supplier'"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class ItemSupplierList(GridReport):
  '''
  A list report to show item suppliers.
  '''
  title = _("item suppliers")
  basequeryset = ItemSupplier.objects.all()
  model = ItemSupplier
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra="role:'input/itemsupplier'"),
    GridFieldText('item', title=_('item'), formatter='detail', extra="role:'input/item'"),
    GridFieldText('location', title=_('location'), formatter='detail', extra="role:'input/location'"),
    GridFieldText('supplier', title=_('supplier'), formatter='detail', extra="role:'input/supplier'"),
    GridFieldDuration('leadtime', title=_('lead time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldNumber('priority', title=_('priority')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class ItemDistributionList(GridReport):
  '''
  A list report to show item distribution.
  '''
  title = _("item distributions")
  basequeryset = ItemDistribution.objects.all()
  model = ItemDistribution
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra="role:'input/itemdistribution'"),
    GridFieldText('item', title=_('item'), formatter='detail', extra="role:'input/item'"),
    GridFieldText('location', title=_('location'), formatter='detail', extra="role:'input/location'"),
    GridFieldText('origin', title=_('origin'), formatter='detail', extra="role:'input/location'"),
    GridFieldDuration('leadtime', title=_('lead time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldNumber('priority', title=_('priority')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class ItemList(GridReport):
  '''
  A list report to show items.
  '''
  title = _("items")
  basequeryset = Item.objects.all()
  model = Item
  frozenColumns = 1
  editable = True

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/item'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldText('owner', title=_('owner'), field_name='owner__name'),
    GridFieldCurrency('price', title=_('price')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class SkillList(GridReport):
  '''
  A list report to show skills.
  '''
  title = _("skills")
  basequeryset = Skill.objects.all()
  model = Skill
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/skill'"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class ResourceSkillList(GridReport):
  '''
  A list report to show resource skills.
  '''
  title = _("resource skills")
  basequeryset = ResourceSkill.objects.all()
  model = ResourceSkill
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra="role:'input/resourceskill'"),
    GridFieldText('resource', title=_('resource'), formatter='detail', extra="role:'input/resource'"),
    GridFieldText('skill', title=_('skill'), formatter='detail', extra="role:'input/skill'"),
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
  title = _("loads")
  basequeryset = Load.objects.all()
  model = Load
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra="role:'input/load'"),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', formatter='detail', extra="role:'input/resource'"),
    GridFieldText('skill', title=_('skill'), formatter='detail', extra="role:'input/skill'"),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name')),
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
  title = _("flows")
  basequeryset = Flow.objects.all()
  model = Flow
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra="role:'input/flow'"),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldText('thebuffer', title=_('buffer'), field_name='thebuffer__name', formatter='detail', extra="role:'input/buffer'"),
    GridFieldChoice('type', title=_('type'), choices=Flow.types),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name')),
    GridFieldNumber('priority', title=_('priority')),
    GridFieldChoice('search', title=_('search mode'), choices=searchmode),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

class DemandList(GridReport):
  '''
  A list report to show demands.
  '''
  title = _("sales orders")
  basequeryset = Demand.objects.all()
  model = Demand
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/demand'"),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra="role:'input/item'"),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra="role:'input/location'"),
    GridFieldText('customer', title=_('customer'), field_name='customer__name', formatter='detail', extra="role:'input/customer'"),
    GridFieldChoice('status', title=_('status'), choices=Demand.demandstatus),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldDateTime('due', title=_('due')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldText('operation', title=_('delivery operation'), formatter='detail', extra="role:'input/operation'"),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldText('owner', title=_('owner'), formatter='detail', extra="role:'input/demand'"),
    GridFieldDuration('maxlateness', title=_('maximum lateness')),
    GridFieldNumber('minshipment', title=_('minimum shipment')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  actions = [
    {"name": 'inquiry', "label": _("change status to %(status)s") % {'status': _("inquiry")}, "function": "grid.setStatus('inquiry')"},
    {"name": 'quote', "label": _("change status to %(status)s") % {'status': _("quote")}, "function": "grid.setStatus('quote')"},
    {"name": 'open', "label": _("change status to %(status)s") % {'status': _("open")}, "function": "grid.setStatus('open')"},
    {"name": 'closed', "label": _("change status to %(status)s") % {'status': _("closed")}, "function": "grid.setStatus('closed')"},
    {"name": 'canceled', "label": _("change status to %(status)s") % {'status': _("canceled")}, "function": "grid.setStatus('canceled')"},
    ]

class CalendarList(GridReport):
  '''
  A list report to show calendars.
  '''
  title = _("calendars")
  basequeryset = Calendar.objects.all()
  model = Calendar
  frozenColumns = 1
  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/calendar'"),
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
  title = _("calendar buckets")
  basequeryset = CalendarBucket.objects.all()
  model = CalendarBucket
  frozenColumns = 3
  rows = (
    GridFieldInteger('id', title=_('identifier'), formatter='detail', extra="role:'input/calendarbucket'"),
    GridFieldText('calendar', title=_('calendar'), field_name='calendar__name', formatter='detail', extra="role:'input/calendar'"),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date'), editable=False),
    GridFieldNumber('value', title=_('value')),
    GridFieldInteger('priority', title=_('priority')),
    #. Translators: Translation included with Django
    GridFieldBool('monday', title=_('Monday')),
    #. Translators: Translation included with Django
    GridFieldBool('tuesday', title=_('Tuesday')),
    #. Translators: Translation included with Django
    GridFieldBool('wednesday', title=_('Wednesday')),
    #. Translators: Translation included with Django
    GridFieldBool('thursday', title=_('Thursday')),
    #. Translators: Translation included with Django
    GridFieldBool('friday', title=_('Friday')),
    #. Translators: Translation included with Django
    GridFieldBool('saturday', title=_('Saturday')),
    #. Translators: Translation included with Django
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
  title = _("operations")
  basequeryset = Operation.objects.all()
  model = Operation
  frozenColumns = 1

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra="role:'input/operation'"),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldChoice('type', title=_('type'), choices=Operation.types),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra="role:'input/location'"),
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
  title = _("suboperations")
  basequeryset = SubOperation.objects.all()
  model = SubOperation
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldText('suboperation', title=_('suboperation'), field_name='suboperation__name', formatter='detail', extra="role:'input/operation'"),
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
  title = _("operationplans")
  basequeryset = OperationPlan.objects.all()
  model = OperationPlan
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldChoice('status', title=_('status'), choices=OperationPlan.orderstatus),
    GridFieldInteger('owner', title=_('owner'), extra="formatoptions:{defaultValue:''}"),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  actions = [
    {"name": 'proposed', "label": _("change status to %(status)s") % {'status': _("proposed")}, "function": "grid.setStatus('proposed')"},
    {"name": 'confirmed', "label": _("change status to %(status)s") % {'status': _("confirmed")}, "function": "grid.setStatus('confirmed')"},
    {"name": 'closed', "label": _("change status to %(status)s") % {'status': _("closed")}, "function": "grid.setStatus('closed')"},
    ]


class DistributionOrderList(GridReport):
  '''
  A list report to show distribution orders.
  '''
  title = _("distribution orders")
  basequeryset = DistributionOrder.objects.all()
  model = DistributionOrder
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('reference', title=_('reference'),
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldChoice('status', title=_('status'), choices=DistributionOrder.orderstatus,
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra="role:'input/item'"),
    GridFieldText('origin', title=_('origin'), field_name='origin__name', formatter='detail', extra="role:'input/location'"),
    GridFieldText('destination', title=_('destination'), field_name='destination__name', formatter='detail', extra="role:'input/location'"),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldBool('consume_material', title=_('consume material')),
    GridFieldNumber('criticality', title=_('criticality'), editable=False),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  if 'freppledb.openbravo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'openbravo_incr_export', "label": _("incremental export to openbravo"), "function": "openbravo.IncrementalExport(jQuery('#grid'),'DO')"},
    ]
  else:
    actions = [
      {"name": 'proposed', "label": _("change status to %(status)s") % {'status': _("proposed")}, "function": "grid.setStatus('proposed')"},
      {"name": 'confirmed', "label": _("change status to %(status)s") % {'status': _("confirmed")}, "function": "grid.setStatus('confirmed')"},
      {"name": 'closed', "label": _("change status to %(status)s") % {'status': _("closed")}, "function": "grid.setStatus('closed')"},
      ]


class PurchaseOrderList(GridReport):
  '''
  A list report to show purchase orders.
  '''
  title = _("purchase orders")
  basequeryset = PurchaseOrder.objects.all()
  model = PurchaseOrder
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('reference', title=_('reference'),
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldChoice('status', title=_('status'),
      choices=PurchaseOrder.orderstatus, editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra="role:'input/item'"),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra="role:'input/location'"),
    GridFieldText('supplier', title=_('supplier'), formatter='detail', extra="role:'input/supplier'"),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldNumber('criticality', title=_('criticality'), editable=False),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  if 'freppledb.openbravo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'openbravo_incr_export', "label": _("incremental export to openbravo"), "function": "openbravo.IncrementalExport(jQuery('#grid'),'PO')"},
    ]
  else:
    actions = [
      {"name": 'proposed', "label": _("change status to %(status)s") % {'status': _("proposed")}, "function": "grid.setStatus('proposed')"},
      {"name": 'confirmed', "label": _("change status to %(status)s") % {'status': _("confirmed")}, "function": "grid.setStatus('confirmed')"},
      {"name": 'closed', "label": _("change status to %(status)s") % {'status': _("closed")}, "function": "grid.setStatus('closed')"},
      ]
