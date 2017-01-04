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
from freppledb.input.models import Skill, Buffer, Customer, Demand
from freppledb.input.models import Item, OperationResource, OperationMaterial
from freppledb.input.models import Calendar, CalendarBucket, ManufacturingOrder, SubOperation
from freppledb.input.models import ResourceSkill, Supplier, ItemSupplier, searchmode
from freppledb.input.models import ItemDistribution, DistributionOrder, PurchaseOrder
from freppledb.input.models import OperationPlan
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
  title = _("supply path")
  filterable = False
  frozenColumns = 0
  editable = False
  default_sort = None
  multiselect = False
  help_url = 'user-guide/user-interface/supply-path-where-used.html'

  rows = (
    GridFieldText('depth', title=_('depth'), editable=False, sortable=False),
    GridFieldText('operation', title=_('operation'), editable=False, sortable=False, formatter='detail', extra='"role":"input/operation"'),
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
        ": " + force_text(reportclass.downstream and _("where used") or _("supply path"))
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
    # a buffer for this item and location combination.
    buf = None
    # Find a buffer record
    for b in Buffer.objects.using(db).filter(item=item, location=location):
      buf = b
    if not buf:
      # Create a buffer record
      buf = Buffer(
        name='%s @ %s' % (item, location),
        item=Item.objects.using(db).get(name=item),
        location=Location.objects.using(db).get(name=location)
        )
    return reportclass.findReplenishment(buf, db, 0, 1, 0, False)


  @classmethod
  def findUsage(reportclass, buffer, db, level, curqty, realdepth, pushsuper):
    result = [
      (level - 1, None, i.operation, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
      for i in buffer.item.operationmaterials.filter(quantity__lt=0).filter(operation__location__name=buffer.location.name).only('operation').using(db)
      ]
    for i in ItemDistribution.objects.using(db).filter(
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft,
        origin__name=buffer.location.name
        ):
      i.item = buffer.item
      result.append( (level - 1, None, i, curqty, 0, None, realdepth - 1, pushsuper, i.location.name if i.location else None) )
    return result


  @classmethod
  def findReplenishment(reportclass, buffer, db, level, curqty, realdepth, pushsuper):
    # If a producing operation is set on the buffer, we use that and skip the
    # automated search described below.
    # If no producing operation is set, we look for item distribution and
    # item supplier models for the item and location combination. (As a special
    # case in case only a single location exists in the model, a match on the
    # item is sufficient).
    result = []
    if Location.objects.using(db).count() > 1:
      # Multiple locations
      for i in ItemSupplier.objects.using(db).filter(
        Q(location__isnull=True) | Q(location__name=buffer.location.name),
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft
        ):
          i.item = buffer.item
          i.location = buffer.location
          result.append(
            (level, None, i, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
            )
      for i in ItemDistribution.objects.using(db).filter(
        Q(location__isnull=True) | Q(location__name=buffer.location.name),
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft
        ):
          i.item = buffer.item
          i.location = buffer.location
          result.append(
            (level, None, i, curqty, 0, None, realdepth, pushsuper, i.location.name if i.location else None)
            )
      for i in Operation.objects.using(db).filter(
        Q(location__isnull=True) | Q(location__name=buffer.location.name),
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft
        ):
          i.item = buffer.item
          i.location = buffer.location
          result.append(
            (level, None, i, curqty, 0, None, realdepth, pushsuper, i.location.name if i.location else None)
            )
    else:
      # Single location
      for i in ItemSupplier.objects.using(db).filter(
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft
        ):
        i.item = buffer.item
        i.location = buffer.location
        result.append(
          (level, None, i, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
          )
      for i in Operation.objects.using(db).filter(
        item__lft__lte=buffer.item.lft, item__rght__gt=buffer.item.lft
        ):
          i.item = buffer.item
          i.location = buffer.location
          result.append(
            (level, None, i, curqty, 0, None, realdepth, pushsuper, buffer.location.name if buffer.location else None)
            )
    return result


  @classmethod
  def query(reportclass, request, basequery):
    '''
    A function that recurses upstream or downstream in the supply chain.
    '''
    # Update item and location hierarchies
    Item.rebuildHierarchy(database=request.database)
    Location.rebuildHierarchy(database=request.database)

    entity = basequery.query.get_compiler(basequery.db).as_sql(with_col_aliases=False)[1]
    entity = entity[0]
    root = reportclass.getRoot(request, entity)

    # Recurse over all operations
    # TODO the current logic isn't generic enough. A lot of buffers may not be explicitly
    # defined, and are created on the fly by deliveries, itemsuppliers or itemdistributions.
    # Currently we don't account for such situations.
    # TODO usage search doesn't find item distributions from that location
    counter = 1
    operations = set()
    while len(root) > 0:
      # Pop the current node from the stack
      level, parent, curoperation, curqty, issuboperation, parentoper, realdepth, pushsuper, location = root.pop()
      curnode = counter
      counter += 1
      if isinstance(location, str):
        curlocation = Location.objects.all().using(request.database).get(name=location)

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
      # This feature is enabled by default. Without it we cannot correctly display
      # supply paths with loops (which are normally a modeling error).
      # The use of this feature has some drawbacks  a) because it is not intuitive 
      # to understand where operations are skipped in the path, and b) because
      # the quantity of each occurrence might be different.
      # You may choose can disable this feature by commenting out the next 3 lines.
      if curoperation in operations: 
        continue
      operations.add(curoperation)

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
          if curoperation.resource:
            resources = [ (curoperation.resource.name, float(curoperation.resource_qty)) ]
          else:
            resources = None
          try:
            downstr = Buffer.objects.using(request.database).get(name="%s @ %s" % (curoperation.item.name, curoperation.location.name))
            root.extend( reportclass.findUsage(downstr, request.database, level, curqty, realdepth + 1, True) )
          except Buffer.DoesNotExist:
            downstr = Buffer(name="%s @ %s" % (curoperation.item.name, curoperation.location.name), item=curoperation.item, location=curlocation)
            root.extend( reportclass.findUsage(downstr, request.database, level, curqty, realdepth + 1, True) )
        elif isinstance(curoperation, ItemDistribution):
          name = 'Ship %s from %s to %s' % (curoperation.item.name, curoperation.origin.name, curoperation.location.name)
          optype = "distribution"
          duration = curoperation.leadtime
          duration_per = None
          buffers = [
            ("%s @ %s" % (curoperation.item.name, curoperation.origin.name), -1),
            ("%s @ %s" % (curoperation.item.name, curoperation.location.name), 1)
            ]
          if curoperation.resource:
            resources = [ (curoperation.resource.name, float(curoperation.resource_qty)) ]
          else:
            resources = None
          try:
            downstr = Buffer.objects.using(request.database).get(name="%s @ %s" % (curoperation.item.name, location))
            root.extend( reportclass.findUsage(downstr, request.database, level, curqty, realdepth + 1, True) )
          except Buffer.DoesNotExist:
            downstr = Buffer(name="%s @ %s" % (curoperation.item.name, location), item=curoperation.item, location=curlocation)
            root.extend( reportclass.findUsage(downstr, request.database, level, curqty, realdepth + 1, True) )
        else:
          name = curoperation.name
          optype = curoperation.type
          duration = curoperation.duration
          duration_per = curoperation.duration_per
          buffers = [ ('%s @ %s' % (x.item.name, curoperation.location.name), float(x.quantity)) for x in curoperation.operationmaterials.only('item', 'quantity').using(request.database) ]
          resources = [ (x.resource.name, float(x.quantity)) for x in curoperation.operationresources.only('resource', 'quantity').using(request.database) ]
          for x in curoperation.operationmaterials.filter(quantity__gt=0).only('item').using(request.database):
            curflows = x.item.operationmaterials.filter(quantity__lt=0, operation__location=curoperation.location.name).only('operation', 'quantity').using(request.database)
            for y in curflows:
              hasChildren = True
              root.append( (level - 1, curnode, y.operation, - curqty * y.quantity, subcount, None, realdepth - 1, pushsuper, x.operation.location.name if x.operation.location else None) )
            try:
              downstr = Buffer.objects.using(request.database).get(name="%s @ %s" % (x.item.name, location))
              root.extend( reportclass.findUsage(downstr, request.database, level-1, curqty, realdepth - 1, True) )
            except Buffer.DoesNotExist:
              downstr = Buffer(name="%s @ %s" % (curoperation.item.name, location), item=x.item, location=curlocation)
              root.extend( reportclass.findUsage(downstr, request.database, level-1, curqty, realdepth - 1, True) )
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
          if curoperation.resource:
            resources = [ (curoperation.resource.name, float(curoperation.resource_qty)) ]
          else:
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
          if curoperation.resource:
            resources = [ (curoperation.resource.name, float(curoperation.resource_qty)) ]
          else:
            resources = None
          try:
            upstr = Buffer.objects.using(request.database).get(name="%s @ %s" % (curoperation.item.name, curoperation.origin.name))
            root.extend( reportclass.findReplenishment(upstr, request.database, level + 2, curqty, realdepth + 1, True) )
          except Buffer.DoesNotExist:
            upstr = Buffer(name="%s @ %s" % (curoperation.item.name, curoperation.origin.name), item=curoperation.item, location=curoperation.origin)
            root.extend( reportclass.findReplenishment(upstr, request.database, level + 2, curqty, realdepth + 1, True) )
        else:
          curprodflow = None
          name = curoperation.name
          optype = curoperation.type
          duration = curoperation.duration
          duration_per = curoperation.duration_per
          buffers = [ ('%s @ %s' % (x.item.name, curoperation.location.name), float(x.quantity)) for x in curoperation.operationmaterials.only('item', 'quantity').using(request.database) ]
          resources = [ (x.resource.name, float(x.quantity)) for x in curoperation.operationresources.only('resource', 'quantity').using(request.database) ]
          for x in curoperation.operationmaterials.filter(quantity__gt=0).only('quantity').using(request.database):
            curprodflow = x
          curflows = curoperation.operationmaterials.filter(quantity__lt=0).only('item', 'quantity').using(request.database)
          for y in curflows:
            b = Buffer(
              name='%s @ %s' % (y.item.name, curoperation.location.name),
              item=y.item,
              location=curoperation.location
              )
            root.extend( reportclass.findReplenishment(b, request.database, level + 2, curqty, realdepth + 1, True) )
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
      locs = set()
      result = []
      it = Item.objects.using(request.database).get(name=entity)
      if reportclass.downstream:
        # Find all buffers where the item is being stored and walk downstream
        for b in Buffer.objects.filter(item=it).using(request.database):
          locs.add(b.location.name)
          result.extend( reportclass.findUsage(b, request.database, 0, 1, 0, True) )
        # Add item locations that can be replenished
        for itmdist in ItemDistribution.objects.using(request.database).filter(
          item__lft__lte=it.lft, item__rght__gt=it.lft
          ):
            if itmdist.location.name in locs:
              continue
            locs.add(itmdist.location.name)
            itmdist.item = it
            result.append(
              (0, None, itmdist, 1, 0, None, 0, False, itmdist.location.name)
              )
        # Add item locations that can be replenished
        for itmsup in Operation.objects.using(request.database).filter(          
          item__lft__lte=it.lft, item__rght__gt=it.lft
          ):
            if itmsup.location.name in locs:
              continue
            locs.add(itmsup.location.name)
            itmsup.item = it            
            result.append(
              (0, None, itmsup, 1, 0, None, 0, False, itmsup.location.name)
              )        
        return result
      else:
        # Find the supply path of all buffers of this item
        for b in Buffer.objects.filter(item=entity).using(request.database):
          result.extend( reportclass.findReplenishment(b, request.database, 0, 1, 0, True) )
        # Add item locations that can be replenished
        for itmdist in ItemDistribution.objects.using(request.database).filter(
          item__lft__lte=it.lft, item__rght__gt=it.lft
          ):
            if itmdist.location.name in locs:
              continue
            locs.add(itmdist.location.name)
            itmdist.item = it
            result.append(
              (0, None, itmdist, 1, 0, None, 0, False, itmdist.location.name)
              )
        # Add item locations that can be replenished
        for itmsup in Operation.objects.using(request.database).filter(          
          item__lft__lte=it.lft, item__rght__gt=it.lft
          ):
            if itmsup.location.name in locs:
              continue
            locs.add(itmsup.location.name)
            itmsup.item = it            
            result.append(
              (0, None, itmsup, 1, 0, None, 0, False, itmsup.location.name)
              )        
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
        return reportclass.findUsage(buf, request.database, 0, 1, 0, True)
      else:
        return reportclass.findReplenishment(buf, request.database, 0, 1, 0, True)
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
      for i in root.operationresources.using(request.database).all()
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
  help_url = 'user-guide/modeling-wizard/master-data/buffers.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/buffer", "editable":false'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldNumber('onhand', title=_('onhand')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra='"role":"input/buffer"'),
    GridFieldChoice('type', title=_('type'), choices=Buffer.types),
    GridFieldNumber('minimum', title=_('minimum')),
    GridFieldText('minimum_calendar', title=_('minimum calendar'), field_name='minimum_calendar__name', formatter='detail', extra='"role":"input/calendar"'),
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
  help_url = 'user-guide/model-reference/setup-matrices.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/setupmatrix"'),
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
  help_url = 'user-guide/modeling-wizard/manufacturing-capacity/resources.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/resource"'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra='"role":"input/resource"'),
    GridFieldChoice('type', title=_('type'), choices=Resource.types),
    GridFieldNumber('maximum', title=_('maximum')),
    GridFieldText('maximum_calendar', title=_('maximum calendar'), field_name='maximum_calendar__name', formatter='detail', extra='"role":"input/calendar"'),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldDuration('maxearly', title=_('maxearly')),
    GridFieldText('setupmatrix', title=_('setup matrix'), field_name='setupmatrix__name', formatter='detail', extra='"role":"input/setupmatrix"'),
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
  help_url = 'user-guide/modeling-wizard/master-data/locations.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/location"'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('available', title=_('available'), field_name='available__name', formatter='detail', extra='"role":"input/calendar"'),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra='"role":"input/location"'),
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
  help_url = 'user-guide/modeling-wizard/master-data/customers.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/customer"'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra='"role":"input/customer"'),
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
  help_url = 'user-guide/modeling-wizard/purchasing/suppliers.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/supplier"'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra='"role":"input/supplier"'),
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
  help_url = 'user-guide/modeling-wizard/purchasing/item-suppliers.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='"role":"input/itemsupplier"'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('supplier', title=_('supplier'), field_name='supplier__name', formatter='detail', extra='"role":"input/supplier"'),
    GridFieldDuration('leadtime', title=_('lead time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldDuration('fence', title=_('fence')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', formatter='detail', extra='"role":"input/resource"'),
    GridFieldNumber('resource_qty', title=_('resource quantity')),
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
  help_url = 'user-guide/modeling-wizard/distribution/item-distributions.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='"role":"input/itemdistribution"'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('origin', title=_('origin'), field_name='origin__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldDuration('leadtime', title=_('lead time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldCurrency('cost', title=_('cost')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldDuration('fence', title=_('fence')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', formatter='detail', extra='"role":"input/resource"'),
    GridFieldNumber('resource_qty', title=_('resource quantity')),
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
  help_url = 'user-guide/modeling-wizard/master-data/items.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/item"'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
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
  help_url = 'user-guide/model-reference/skills.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/skill"'),
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
  help_url = 'user-guide/model-reference/resource-skills.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='"role":"input/resourceskill"'),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', formatter='detail', extra='"role":"input/resource"'),
    GridFieldText('skill', title=_('skill'), field_name='skill__name', formatter='detail', extra='"role":"input/skill"'),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class OperationResourceList(GridReport):
  '''
  A list report to show operationresources.
  '''
  title = _("operation resources")
  basequeryset = OperationResource.objects.all()
  model = OperationResource
  frozenColumns = 1
  help_url = 'user-guide/modeling-wizard/manufacturing-capacity/operation-resources.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='"role":"input/operationresource"'),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('resource', title=_('resource'), field_name='resource__name', formatter='detail', extra='"role":"input/resource"'),
    GridFieldText('skill', title=_('skill'), field_name='skill__name', formatter='detail', extra='"role":"input/skill"'),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldText('setup', title=_('setup')),
    GridFieldChoice('search', title=_('search mode'), choices=searchmode),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class OperationMaterialList(GridReport):
  '''
  A list report to show operationmaterials.
  '''
  title = _("operation materials")
  basequeryset = OperationMaterial.objects.all()
  model = OperationMaterial
  frozenColumns = 1
  help_url = 'user-guide/modeling-wizard/manufacturing-bom/operation-materials.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='"role":"input/operationmaterial"'),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldChoice('type', title=_('type'), choices=OperationMaterial.types),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldChoice('search', title=_('search mode'), choices=searchmode),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class DemandList(GridReport):
  '''
  A list report to show sales orders.
  '''
  title = _("sales orders")
  basequeryset = Demand.objects.all()
  model = Demand
  frozenColumns = 1
  help_url = 'user-guide/modeling-wizard/master-data/sales-orders.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/demand"'),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('customer', title=_('customer'), field_name='customer__name', formatter='detail', extra='"role":"input/customer"'),
    GridFieldChoice('status', title=_('status'), choices=Demand.demandstatus),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldDateTime('due', title=_('due')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldText('operation', title=_('delivery operation'), field_name='operation__name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldText('owner', title=_('owner'), field_name='owner__name', formatter='detail', extra='"role":"input/demand"'),
    GridFieldDuration('maxlateness', title=_('maximum lateness')),
    GridFieldNumber('minshipment', title=_('minimum shipment')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  if 'freppledb.openbravo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'openbravo_incr_export', "label": _("export to %(erp)s") % {'erp': 'openbravo'}, "function": "ERPconnection.SODepExport(jQuery('#grid'),'SO','openbravo')"},
      ]
  elif 'freppledb.odoo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'odoo_incr_export', "label": _("export to %(erp)s") % {'erp': 'odoo'}, "function": "ERPconnection.SODepExport(jQuery('#grid'),'SO','odoo')"},
      ]
  else:
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
  help_url = 'user-guide/model-reference/calendars.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/calendar"'),
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
  help_url = 'user-guide/model-reference/calendars.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), formatter='detail', extra='"role":"input/calendarbucket"'),
    GridFieldText('calendar', title=_('calendar'), field_name='calendar__name', formatter='detail', extra='"role":"input/calendar"'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
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
  help_url = 'user-guide/modeling-wizard/manufacturing-bom/operations.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('description', title=_('description')),
    GridFieldText('category', title=_('category')),
    GridFieldText('subcategory', title=_('subcategory')),
    GridFieldChoice('type', title=_('type'), choices=Operation.types),
    GridFieldText('item', title=_('item'), formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldDuration('duration', title=_('duration')),
    GridFieldDuration('duration_per', title=_('duration per unit')),
    GridFieldDuration('fence', title=_('release fence')),
    GridFieldDuration('posttime', title=_('post-op time')),
    GridFieldNumber('sizeminimum', title=_('size minimum')),
    GridFieldNumber('sizemultiple', title=_('size multiple')),
    GridFieldNumber('sizemaximum', title=_('size maximum')),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
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
  help_url = 'user-guide/model-reference/suboperations.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldText('suboperation', title=_('suboperation'), field_name='suboperation__name', formatter='detail', extra='"role":"input/operation"'),
    GridFieldInteger('priority', title=_('priority')),
    GridFieldDateTime('effective_start', title=_('effective start')),
    GridFieldDateTime('effective_end', title=_('effective end')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class ManufacturingOrderList(GridReport):
  '''
  A list report to show manufacturing orders.
  '''
  title = _("manufacturing orders")
  basequeryset = ManufacturingOrder.objects.all()
  model = ManufacturingOrder
  frozenColumns = 1
  help_url = 'user-guide/modeling-wizard/manufacturing-bom/manufacturing-orders.html'

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    return ManufacturingOrder.objects.all().extra(select={
      'demand': "(select string_agg(value || ' : ' || key, ', ') from (select key, value from json_each_text(operationplan.plan) order by key desc) peg)"
      })

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra="role:'input/manufacturingorder'"),
    GridFieldText('reference', title=_('reference'),
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldText('operation', title=_('operation'), field_name='operation__name', formatter='detail', extra="role:'input/operation'"),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldChoice('status', title=_('status'), choices=OperationPlan.orderstatus),
    GridFieldInteger('owner', title=_('owner'), extra='"formatoptions":{"defaultValue":""}'),
    GridFieldNumber('criticality', title=_('criticality'), editable=False),
    GridFieldDuration('delay', title=_('delay'), editable=False),
    GridFieldText('demand', title=_('demands'), editable=False, sortable=False, formatter='demanddetail', extra='"role":"input/demand"'),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  if 'freppledb.openbravo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'openbravo_incr_export', "label": _("export to %(erp)s") % {'erp': 'openbravo'}, "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'OP','openbravo')"},
      ]
  elif 'freppledb.odoo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'odoo_incr_export', "label": _("export to %(erp)s") % {'erp': 'odoo'}, "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'OP','odoo')"},
      ]
  else:
    actions = [
      {"name": 'proposed', "label": _("change status to %(status)s") % {'status': _("proposed")}, "function": "grid.setStatus('proposed')"},
      {"name": 'approved', "label": _("change status to %(status)s") % {'status': _("approved")}, "function": "grid.setStatus('approved')"},
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
  help_url = 'user-guide/modeling-wizard/distribution/distribution-orders.html'

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    return DistributionOrder.objects.all().extra(select={
      'demand': "(select string_agg(value || ' : ' || key, ', ') from (select key, value from json_each_text(operationplan.plan) order by key desc) peg)"
      })

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='role:"input/distributionorder"'),
    GridFieldText('reference', title=_('reference'),
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldChoice('status', title=_('status'), choices=DistributionOrder.orderstatus,
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldText('origin', title=_('origin'), field_name='origin__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('destination', title=_('destination'), field_name='destination__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldText('demand', title=_('demands'), editable=False, sortable=False, formatter='demanddetail', extra='"role":"input/demand"'),
    GridFieldNumber('criticality', title=_('criticality'), editable=False),
    GridFieldDuration('delay', title=_('delay'), editable=False),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  if 'freppledb.openbravo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'openbravo_incr_export', "label": _("export to %(erp)s") % {'erp': 'openbravo'}, "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'DO','openbravo')"},
    ]
  elif 'freppledb.odoo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'odoo_incr_export', "label": _("export to %(erp)s") % {'erp': 'odoo'}, "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'DO','odoo')"},
    ]
  else:
    actions = [
      {"name": 'proposed', "label": _("change status to %(status)s") % {'status': _("proposed")}, "function": "grid.setStatus('proposed')"},
      {"name": 'approved', "label": _("change status to %(status)s") % {'status': _("approved")}, "function": "grid.setStatus('approved')"},
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
  help_url = 'user-guide/modeling-wizard/purchasing/purchase-orders.html'

  @ classmethod
  def basequeryset(reportclass, request, args, kwargs):
    return PurchaseOrder.objects.all().extra(select={
      'demand': "coalesce((select string_agg(value || ' : ' || key, ', ') from (select key, value from json_each_text(operationplan.plan) order by key desc) peg), '')"
      })

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='role:"input/purchaseorder"'),
    GridFieldText('reference', title=_('reference'),
      editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldChoice('status', title=_('status'),
      choices=PurchaseOrder.orderstatus, editable='freppledb.openbravo' not in settings.INSTALLED_APPS
      ),
    GridFieldText('item', title=_('item'), field_name='item__name', formatter='detail', extra='"role":"input/item"'),
    GridFieldText('location', title=_('location'), field_name='location__name', formatter='detail', extra='"role":"input/location"'),
    GridFieldText('supplier', title=_('supplier'), field_name='supplier__name', formatter='detail', extra='"role":"input/supplier"'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldNumber('quantity', title=_('quantity')),
    GridFieldText('demand', title=_('demands'), editable=False, sortable=False, formatter='demanddetail', extra='"role":"input/demand"'),
    GridFieldNumber('criticality', title=_('criticality'), editable=False),
    GridFieldDuration('delay', title=_('delay'), editable=False),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )

  if 'freppledb.openbravo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'openbravo_incr_export', "label": _("export to %(erp)s") % {'erp': 'openbravo'}, "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'PO','openbravo')"},
      ]
  elif 'freppledb.odoo' in settings.INSTALLED_APPS:
    actions = [
      {"name": 'odoo_incr_export', "label": _("export to %(erp)s") % {'erp': 'odoo'}, "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'PO','odoo')"},
      ]
  else:
    actions = [
      {"name": 'proposed', "label": _("change status to %(status)s") % {'status': _("proposed")}, "function": "grid.setStatus('proposed')"},
      {"name": 'approved', "label": _("change status to %(status)s") % {'status': _("approved")}, "function": "grid.setStatus('approved')"},
      {"name": 'confirmed', "label": _("change status to %(status)s") % {'status': _("confirmed")}, "function": "grid.setStatus('confirmed')"},
      {"name": 'closed', "label": _("change status to %(status)s") % {'status': _("closed")}, "function": "grid.setStatus('closed')"},
      ]
