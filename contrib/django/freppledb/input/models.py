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

from datetime import datetime, time

from django.db import models, DEFAULT_DB_ALIAS
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _

from freppledb.common.fields import JSONField
from freppledb.common.models import HierarchyModel, AuditModel


searchmode = (
  ('PRIORITY', _('priority')),
  ('MINCOST', _('minimum cost')),
  ('MINPENALTY', _('minimum penalty')),
  ('MINCOSTPENALTY', _('minimum cost plus penalty'))
)


class Calendar(AuditModel):
  # Database fields
  #. Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, primary_key=True)
  description = models.CharField(
    _('description'), max_length=500, null=True,
    blank=True
    )
  category = models.CharField(
    _('category'), max_length=300, null=True,
    blank=True, db_index=True
    )
  subcategory = models.CharField(
    _('subcategory'), max_length=300,
    null=True, blank=True, db_index=True
    )
  defaultvalue = models.DecimalField(
    _('default value'), max_digits=15,
    decimal_places=6, default='0.00', null=True, blank=True,
    help_text=_('Value to be used when no entry is effective')
    )

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'calendar'
    #. Translators: Translation included with Django
    verbose_name = _('calendar')
    #. Translators: Translation included with Django
    verbose_name_plural = _('calendars')
    ordering = ['name']


class CalendarBucket(AuditModel):

  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  #. Translators: Translation included with Django
  calendar = models.ForeignKey(Calendar, verbose_name=_('calendar'), related_name='buckets')
  startdate = models.DateTimeField(_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), null=True, blank=True, default=datetime(2030, 12, 31))
  value = models.DecimalField(
    _('value'), default='0.00', blank=True,
    max_digits=15, decimal_places=6
    )
  priority = models.IntegerField(_('priority'), default=0, blank=True, null=True)

  #. Translators: Translation included with Django
  monday = models.BooleanField(_('Monday'), blank=True, default=True)
  #. Translators: Translation included with Django
  tuesday = models.BooleanField(_('Tuesday'), blank=True, default=True)
  #. Translators: Translation included with Django
  wednesday = models.BooleanField(_('Wednesday'), blank=True, default=True)
  #. Translators: Translation included with Django
  thursday = models.BooleanField(_('Thursday'), blank=True, default=True)
  #. Translators: Translation included with Django
  friday = models.BooleanField(_('Friday'), blank=True, default=True)
  #. Translators: Translation included with Django
  saturday = models.BooleanField(_('Saturday'), blank=True, default=True)
  #. Translators: Translation included with Django
  sunday = models.BooleanField(_('Sunday'), blank=True, default=True)
  starttime = models.TimeField(_('start time'), blank=True, null=True, default=time(0, 0, 0))
  endtime = models.TimeField(_('end time'), blank=True, null=True, default=time(23, 59, 59))

  def __str__(self):
    return "%s" % self.id

  class Meta(AuditModel.Meta):
    ordering = ['calendar', 'id']
    db_table = 'calendarbucket'
    verbose_name = _('calendar bucket')
    verbose_name_plural = _('calendar buckets')


class Location(AuditModel, HierarchyModel):
  # Database fields
  description = models.CharField(
    _('description'), max_length=500, null=True, blank=True
    )
  category = models.CharField(
    _('category'), max_length=300, null=True, blank=True, db_index=True
    )
  subcategory = models.CharField(
    _('subcategory'), max_length=300, null=True, blank=True, db_index=True
    )
  available = models.ForeignKey(
    Calendar, verbose_name=_('available'),
    null=True, blank=True,
    help_text=_('Calendar defining the working hours and holidays of this location')
    )

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'location'
    verbose_name = _('location')
    verbose_name_plural = _('locations')
    ordering = ['name']


class Customer(AuditModel, HierarchyModel):
  # Database fields
  description = models.CharField(
    _('description'), max_length=500, null=True, blank=True
    )
  category = models.CharField(
    _('category'), max_length=300, null=True, blank=True, db_index=True
    )
  subcategory = models.CharField(
    _('subcategory'), max_length=300, null=True, blank=True, db_index=True
    )

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'customer'
    verbose_name = _('customer')
    verbose_name_plural = _('customers')
    ordering = ['name']


class Item(AuditModel, HierarchyModel):
  # Database fields
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  category = models.CharField(_('category'), max_length=300, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=300, null=True, blank=True, db_index=True)
  price = models.DecimalField(
    _('price'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("Selling price of the item")
    )

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'item'
    verbose_name = _('item')
    verbose_name_plural = _('items')
    ordering = ['name']


class Operation(AuditModel):
  # Types of operations
  types = (
    ('fixed_time', _('fixed_time')),
    ('time_per', _('time_per')),
    ('routing', _('routing')),
    ('alternate', _('alternate')),
    ('split', _('split')),
  )

  # Database fields
  #. Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, primary_key=True)
  type = models.CharField(_('type'), max_length=20, null=True, blank=True, choices=types, default='fixed_time')
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  category = models.CharField(_('category'), max_length=300, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=300, null=True, blank=True, db_index=True)
  item = models.ForeignKey(
    Item, verbose_name=_('item'), null=True, blank=True,
    db_index=True, related_name='operations'
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), db_index=True
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority among all alternates')
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  fence = models.DurationField(
    _('release fence'), null=True, blank=True,
    help_text=_("Operationplans within this time window from the current day are expected to be released to production ERP")
    )
  posttime = models.DurationField(
    _('post-op time'), null=True, blank=True,
    help_text=_("A delay time to be respected as a soft constraint after ending the operation")
    )
  sizeminimum = models.DecimalField(
    _('size minimum'), max_digits=15, decimal_places=6,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum quantity for operationplans")
    )
  sizemultiple = models.DecimalField(
    _('size multiple'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("A multiple quantity for operationplans")
    )
  sizemaximum = models.DecimalField(
    _('size maximum'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("A maximum quantity for operationplans")
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("Cost per operationplan unit")
    )
  duration = models.DurationField(
    _('duration'), null=True, blank=True,
    help_text=_("A fixed duration for the operation")
    )
  duration_per = models.DurationField(
    _('duration per unit'), null=True, blank=True,
    help_text=_("A variable duration for the operation")
    )
  search = models.CharField(
    _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select preferred alternate')
    )

  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    # Reset fields that are not used for specific operation types
    if self.type != 'time_per':
      self.duration_per = None
    if self.type != 'alternate':
      self.search = None
    if self.type is not None and self.type not in ['time_per', 'fixed_time', '']:
      self.duration = None

    # Call the real save() method
    super(Operation, self).save(*args, **kwargs)

  class Meta(AuditModel.Meta):
    db_table = 'operation'
    verbose_name = _('operation')
    verbose_name_plural = _('operations')
    ordering = ['name']


class SubOperation(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  operation = models.ForeignKey(
    Operation, verbose_name=_('operation'),
    related_name='suboperations', help_text=_("Parent operation")
    )
  priority = models.IntegerField(
    _('priority'), default=1,
    help_text=_("Sequence of this operation among the suboperations. Negative values are ignored.")
    )
  suboperation = models.ForeignKey(
    Operation, verbose_name=_('suboperation'),
    related_name='superoperations', help_text=_("Child operation")
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_("Validity start date")
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_("Validity end date")
    )

  def __str__(self):
    return self.operation.name \
      + "   " + str(self.priority) \
      + "   " + self.suboperation.name

  class Meta(AuditModel.Meta):
    db_table = 'suboperation'
    ordering = ['operation', 'priority', 'suboperation']
    verbose_name = _('suboperation')
    verbose_name_plural = _('suboperations')


class Buffer(AuditModel, HierarchyModel):
  # Types of buffers
  types = (
    ('default', _('Default')),
    ('infinite', _('Infinite')),
  )

  # Fields common to all buffer types
  description = models.CharField(
    _('description'), max_length=500, null=True, blank=True
    )
  category = models.CharField(
    _('category'), max_length=300, null=True, blank=True, db_index=True
    )
  subcategory = models.CharField(
    _('subcategory'), max_length=300, null=True, blank=True, db_index=True
    )
  type = models.CharField(
    _('type'), max_length=20, null=True, blank=True, choices=types,
    default='default'
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), 
    db_index=True, blank=False, null=False
    )
  item = models.ForeignKey(
    Item, verbose_name=_('item'), 
    db_index=True, blank=False, null=False
    )
  onhand = models.DecimalField(
    _('onhand'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    default="0.00", help_text=_('current inventory')
    )
  minimum = models.DecimalField(
    _('minimum'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    default="0.00", help_text=_('safety stock')
    )
  minimum_calendar = models.ForeignKey(
    Calendar, verbose_name=_('minimum calendar'),
    null=True, blank=True,
    help_text=_('Calendar storing a time-dependent safety stock profile')
    )
  min_interval = models.DurationField(
    _('min_interval'), null=True, blank=True,
    help_text=_('Batching window for grouping replenishments in batches')
    )

  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    self.name = "%s @ %s" % (self.item.name if self.item else "NULL", self.location.name if self.location else "NULL")
    # Call the real save() method
    super(Buffer, self).save(*args, **kwargs)

  class Meta(AuditModel.Meta):
    db_table = 'buffer'
    verbose_name = _('buffer')
    verbose_name_plural = _('buffers')
    ordering = ['name']
    unique_together = (('item', 'location'),)


class SetupMatrix(AuditModel):
  # Database fields
  name = models.CharField(_('name'), max_length=300, primary_key=True)

  # Methods
  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'setupmatrix'
    verbose_name = _('setup matrix')
    verbose_name_plural = _('setup matrices')
    ordering = ['name']


class SetupRule(AuditModel):
  '''
  A rule that is part of a setup matrix.
  '''
  # Database fields
  setupmatrix = models.ForeignKey(
    SetupMatrix, verbose_name=_('setup matrix'), related_name='rules'
    )
  priority = models.IntegerField(_('priority'))
  fromsetup = models.CharField(
    _('from setup'), max_length=300, blank=True, null=True,
    help_text=_("Name of the old setup (wildcard characters are supported)")
    )
  tosetup = models.CharField(
    _('to setup'), max_length=300, blank=True, null=True,
    help_text=_("Name of the new setup (wildcard characters are supported)")
    )
  duration = models.DurationField(
    _('duration'), null=True, blank=True,
    help_text=_("Duration of the changeover")
    )
  cost = models.DecimalField(
    _('cost'), max_digits=15, decimal_places=6, null=True, blank=True,
    help_text=_("Cost of the conversion")
    )

  def __str__(self):
    return "%s - %s" % (self.setupmatrix.name, self.priority)

  class Meta(AuditModel.Meta):
    ordering = ['priority']
    db_table = 'setuprule'
    unique_together = (('setupmatrix', 'priority'),)
    verbose_name = _('setup matrix rule')
    verbose_name_plural = _('setup matrix rules')


class Resource(AuditModel, HierarchyModel):
  # Types of resources
  types = (
    ('default', _('default')),
    ('buckets', _('buckets')),
    ('infinite', _('infinite')),
  )

  # Database fields
  description = models.CharField(
    _('description'), max_length=500, null=True, blank=True
    )
  category = models.CharField(
    _('category'), max_length=300, null=True, blank=True, db_index=True
    )
  subcategory = models.CharField(
    _('subcategory'), max_length=300, null=True, blank=True, db_index=True
    )
  type = models.CharField(
    _('type'), max_length=20, null=True, blank=True, choices=types, default='default'
    )
  maximum = models.DecimalField(
    _('maximum'), default="1.00", null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_('Size of the resource')
    )
  maximum_calendar = models.ForeignKey(
    Calendar, verbose_name=_('maximum calendar'),
    null=True, blank=True,
    help_text=_('Calendar defining the resource size varying over time')
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'),
    null=True, blank=True, db_index=True
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("Cost for using 1 unit of the resource for 1 hour"))
  maxearly = models.DurationField(
    _('max early'), null=True, blank=True,
    help_text=_('Time window before the ask date where we look for available capacity')
    )
  setupmatrix = models.ForeignKey(
    SetupMatrix, verbose_name=_('setup matrix'),
    null=True, blank=True, db_index=True,
    help_text=_('Setup matrix defining the conversion time and cost')
    )
  setup = models.CharField(
    _('setup'), max_length=300, null=True, blank=True,
    help_text=_('Setup of the resource at the start of the plan')
    )

  # Methods
  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    if self.type == 'infinite':
      # These fields are not relevant for infinite resources
      self.maximum = None
      self.maximum_calendar_id = None
      self.maxearly = None
    # Call the real save() method
    super(Resource, self).save(*args, **kwargs)

  class Meta(AuditModel.Meta):
    db_table = 'resource'
    verbose_name = _('resource')
    verbose_name_plural = _('resources')
    ordering = ['name']


class Skill(AuditModel):
  # Database fields
  name = models.CharField(
    #. Translators: Translation included with Django
    _('name'), max_length=300, primary_key=True,
    help_text=_('Unique identifier')
    )

  # Methods
  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'skill'
    verbose_name = _('skill')
    verbose_name_plural = _('skills')
    ordering = ['name']


class ResourceSkill(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  resource = models.ForeignKey(
    Resource, verbose_name=_('resource'), db_index=True, related_name='skills',
    blank=False, null=False
    )
  skill = models.ForeignKey(
    Skill, verbose_name=_('skill'), db_index=True, related_name='resources',
    blank=False, null=False
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority of this skill in a group of alternates')
    )

  class Meta(AuditModel.Meta):
    db_table = 'resourceskill'
    unique_together = (('resource', 'skill'),)
    verbose_name = _('resource skill')
    verbose_name_plural = _('resource skills')
    ordering = ['resource', 'skill']


class OperationMaterial(AuditModel):
  # Types of flow
  types = (
    ('start', _('Start')),
    ('end', _('End')),
    ('fixed_start', _('Fixed start')),
    ('fixed_end', _('Fixed end'))
  )

  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  operation = models.ForeignKey(
    Operation, verbose_name=_('operation'),
    db_index=True, related_name='operationmaterials',
    blank=False, null=False
    )
  item = models.ForeignKey(
    Item, verbose_name=_('item'),
    db_index=True, related_name='operationmaterials',
    blank=False, null=False
    )
  quantity = models.DecimalField(
    _('quantity'), default='1.00',
    max_digits=15, decimal_places=6,
    help_text=_('Quantity to consume or produce per operationplan unit')
    )
  type = models.CharField(
    _('type'), max_length=20, null=True, blank=True, choices=types, default='start',
    help_text=_('Consume/produce material at the start or the end of the operationplan'),
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  name = models.CharField(
    #. Translators: Translation included with Django
    _('name'), max_length=300, null=True, blank=True,
    help_text=_('Optional name of this operation material')
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority of this operation material in a group of alternates')
    )
  search = models.CharField(
    _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select preferred alternate')
    )

  def __str__(self):
    return '%s - %s' % (
      self.operation.name if self.operation else None,
      self.item.name if self.item else None
      )

  class Meta(AuditModel.Meta):
    db_table = 'operationmaterial'
    unique_together = (('operation', 'item', 'effective_start'),)
    verbose_name = _('operation material')
    verbose_name_plural = _('operation materials')


class OperationResource(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  operation = models.ForeignKey(
    Operation, verbose_name=_('operation'), 
    db_index=True, related_name='operationresources',
    blank=False, null=False
    )
  resource = models.ForeignKey(
    Resource, verbose_name=_('resource'), db_index=True,
    related_name='operationresources',
    blank=False, null=False
    )
  skill = models.ForeignKey(
    Skill, verbose_name=_('skill'), related_name='operationresources',
    null=True, blank=True, db_index=True
    )
  quantity = models.DecimalField(
    _('quantity'), default='1.00',
    max_digits=15, decimal_places=6
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  name = models.CharField(
    #. Translators: Translation included with Django
    _('name'), max_length=300, null=True, blank=True,
    help_text=_('Optional name of this load')
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority of this load in a group of alternates')
    )
  setup = models.CharField(
    _('setup'), max_length=300, null=True, blank=True,
    help_text=_('Setup required on the resource for this operation')
    )
  search = models.CharField(
    _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select preferred alternate')
    )

  def __str__(self):
    return '%s - %s' % (self.operation.name, self.resource.name)

  class Meta(AuditModel.Meta):
    db_table = 'operationresource'
    unique_together = (('operation', 'resource', 'effective_start'),)
    verbose_name = _('operation resource')
    verbose_name_plural = _('operation resources')


class Supplier(AuditModel, HierarchyModel):
  # Database fields
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  category = models.CharField(_('category'), max_length=300, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=300, null=True, blank=True, db_index=True)

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'supplier'
    verbose_name = _('supplier')
    verbose_name_plural = _('suppliers')
    ordering = ['name']


class ItemSupplier(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  item = models.ForeignKey(
    Item, verbose_name=_('item'),
    db_index=True, related_name='itemsuppliers',
    null=False, blank=False
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), null=True, blank=True,
    db_index=True, related_name='itemsuppliers'
    )
  supplier = models.ForeignKey(
    Supplier, verbose_name=_('supplier'),
    db_index=True, related_name='suppliers',
    null=False, blank=False
    )
  leadtime = models.DurationField(
    _('lead time'), null=True, blank=True,
    help_text=_('Purchasing lead time')
    )
  sizeminimum = models.DecimalField(
    _('size minimum'), max_digits=15, decimal_places=6,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum purchasing quantity")
    )
  sizemultiple = models.DecimalField(
    _('size multiple'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("A multiple purchasing quantity")
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("Purchasing cost per unit")
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority among all alternates')
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  resource = models.ForeignKey(
    Resource, verbose_name=_('resource'), null=True, blank=True,
    db_index=True, related_name='itemsuppliers',
    help_text=_("Resource to model the supplier capacity")
    )
  resource_qty = models.DecimalField(
    _('resource quantity'), null=True, blank=True,
    max_digits=15, decimal_places=6, default='1.0',
    help_text=_("Resource capacity consumed per purchased unit")
    )
  fence = models.DurationField(
    _('fence'), null=True, blank=True,
    help_text=_('Frozen fence for creating new procurements')
    )

  def __str__(self):
    return '%s - %s - %s' % (
      self.supplier.name if self.supplier else 'No supplier',
      self.item.name if self.item else 'No item',
      self.location.name if self.location else 'Any location'
      )

  class Meta(AuditModel.Meta):
    db_table = 'itemsupplier'
    unique_together = (('item', 'location', 'supplier', 'effective_start'),)
    verbose_name = _('item supplier')
    verbose_name_plural = _('item suppliers')


class ItemDistribution(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  item = models.ForeignKey(
    Item, verbose_name=_('item'),
    db_index=True, related_name='distributions',
    null=False, blank=False
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), null=True, blank=True,
    db_index=True, related_name='itemdistributions_destination'
    )
  origin = models.ForeignKey(
    Location, verbose_name=_('origin'),
    db_index=True, related_name='itemdistributions_origin'
    )
  leadtime = models.DurationField(
    _('lead time'), null=True, blank=True,
    help_text=_('lead time')
    )
  sizeminimum = models.DecimalField(
    _('size minimum'), max_digits=15, decimal_places=6,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum shipping quantity")
    )
  sizemultiple = models.DecimalField(
    _('size multiple'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("A multiple shipping quantity")
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_("Shipping cost per unit")
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority among all alternates')
    )
  effective_start = models.DateTimeField(
    _('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(
    _('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  resource = models.ForeignKey(
    Resource, verbose_name=_('resource'), null=True, blank=True,
    db_index=True, related_name='itemdistributions',
    help_text=_("Resource to model the distribution capacity")
    )
  resource_qty = models.DecimalField(
    _('resource quantity'), null=True, blank=True,
    max_digits=15, decimal_places=6, default='1.0',
    help_text=_("Resource capacity consumed per distributed unit")
    )
  fence = models.DurationField(
    _('fence'), null=True, blank=True,
    help_text=_('Frozen fence for creating new shipments')
    )

  def __str__(self):
    return '%s - %s - %s' % (
      self.location.name if self.location else 'Any destination',
      self.item.name if self.item else 'No item',
      self.origin.name if self.origin else 'No origin'
      )

  class Meta(AuditModel.Meta):
    db_table = 'itemdistribution'
    unique_together = (('item', 'location', 'origin', 'effective_start'),)
    verbose_name = _('item distribution')
    verbose_name_plural = _('item distributions')


class Demand(AuditModel, HierarchyModel):
  # The priorities defined here are for convenience only. FrePPLe accepts any number as priority.
  demandpriorities = (
    (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'),
    (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'), (13, '13'),
    (14, '14'), (15, '15'), (16, '16'), (17, '17'), (18, '18'),
    (19, '19'), (20, '20')
  )

  # Status
  demandstatus = (
    ('inquiry', _('inquiry')),
    ('quote', _('quote')),
    ('open', _('open')),
    ('closed', _('closed')),
    ('canceled', _('canceled')),
    )

  # Database fields
  description = models.CharField(
    _('description'), max_length=500, null=True, blank=True
    )
  category = models.CharField(
    _('category'), max_length=300, null=True, blank=True, db_index=True
    )
  subcategory = models.CharField(
    _('subcategory'), max_length=300, null=True, blank=True, db_index=True
    )
  customer = models.ForeignKey(
    Customer, verbose_name=_('customer'), db_index=True
    )
  item = models.ForeignKey(
    Item, verbose_name=_('item'), db_index=True
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), db_index=True
    )
  due = models.DateTimeField(_('due'), help_text=_('Due date of the demand'))
  status = models.CharField(
    _('status'), max_length=10, null=True, blank=True,
    choices=demandstatus, default='open',
    help_text=_('Status of the demand. Only "open" demands are planned'),
    )
  operation = models.ForeignKey(
    Operation,
    verbose_name=_('delivery operation'), null=True, blank=True,
    related_name='used_demand',
    help_text=_('Operation used to satisfy this demand')
    )
  quantity = models.DecimalField(
    _('quantity'), max_digits=15, decimal_places=6
    )
  priority = models.PositiveIntegerField(
    _('priority'), default=10, choices=demandpriorities,
    help_text=_('Priority of the demand (lower numbers indicate more important demands)')
    )
  minshipment = models.DecimalField(
    _('minimum shipment'), null=True, blank=True,
    max_digits=15, decimal_places=6,
    help_text=_('Minimum shipment quantity when planning this demand')
    )
  maxlateness = models.DurationField(
    _('maximum lateness'), null=True, blank=True,
    help_text=_("Maximum lateness allowed when planning this demand")
    )
  plan = JSONField(default="{}", null=True, blank=True, editable=False)

  # Convenience methods
  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'demand'
    verbose_name = _('sales order')
    verbose_name_plural = _('sales orders')
    ordering = ['name']


class OperationPlan(AuditModel):
  # Possible types
  types = (
    ('STCK', _('inventory')),
    ('MO', _('manufacturing order')),
    ('PO', _('purchase order')),
    ('DO', _('distribution order')),
    ('DLVR', _('customer shipment')),
    )

  # Possible status
  orderstatus = (
    ('proposed', _('proposed')),
    ('approved', _('approved')),
    ('confirmed', _('confirmed')),
    ('closed', _('closed')),
  )

  # Database fields
  # Common fields
  id = models.IntegerField(
    _('identifier'), primary_key=True,
    help_text=_('Unique identifier of an operationplan')
    )
  status = models.CharField(
    _('status'), null=True, blank=True, max_length=20, choices=orderstatus,
    help_text=_('Status of the order')
    )
  type = models.CharField(
    _('type'), max_length=5, choices=types, default='MO',
    help_text=_('Order type'), db_index=True
    )
  reference = models.CharField(
    _('reference'), max_length=300, null=True, blank=True,
    help_text=_('External reference of this order')
    )
  quantity = models.DecimalField(
    _('quantity'), max_digits=15,
    decimal_places=6, default='1.00'
    )
  startdate = models.DateTimeField(_('start date'), help_text=_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), help_text=_('end date'), null=True, blank=True)
  criticality = models.DecimalField(
    _('criticality'), max_digits=15,
    decimal_places=6, null=True, blank=True, editable=False
    )
  delay = models.DurationField(
    _('delay'), null=True, blank=True, editable=False
    )
  plan = JSONField(default="{}", null=True, blank=True, editable=False)
  # Used only for manufacturing orders
  operation = models.ForeignKey(
    Operation, verbose_name=_('operation'),
    db_index=True, null=True, blank=True
    )
  owner = models.ForeignKey(
    'self', verbose_name=_('owner'), null=True, blank=True,
    related_name='xchildren', help_text=_('Hierarchical parent')
    )
  # Used for purchase orders and distribution orders
  item = models.ForeignKey(
    Item, verbose_name=_('item'),
    null=True, blank=True, db_index=True
    )
  # Used only for distribution orders
  origin = models.ForeignKey(
    Location, verbose_name=_('origin'), null=True, blank=True,
    related_name='origins', db_index=True
    )
  destination = models.ForeignKey(
    Location, verbose_name=_('destination'),
    null=True, blank=True, related_name='destinations', db_index=True
    )
  # Used only for purchase orders
  supplier = models.ForeignKey(
    Supplier, verbose_name=_('supplier'),
    null=True, blank=True, db_index=True
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'),
    null=True, blank=True, db_index=True
    )
  # Used for delivery operationplans
  demand = models.ForeignKey(
    Demand, verbose_name=_('demand'),
    null=True, blank=True, db_index=True
    )
  due = models.DateTimeField(
    _('due'), help_text=_('Due date of the demand/forecast'),
    null=True, blank=True
    )
  name = models.CharField(
    _('name'), max_length=1000, null=True, 
    blank=True, db_index=True
    )

  def __str__(self):
    return str(self.id)

  def save(self, *args, **kwargs):
    if not self.id:
      if 'using' in kwargs:
        db = kwargs['using']
      else:
        state = getattr(self, '_state', None)
        db = state.db if state else DEFAULT_DB_ALIAS
      self.id = OperationPlan.objects.all().using(db).aggregate(Max('id'))['id__max']
      if self.id:
        self.id += 1
      else:
        self.id = 1

    # Call the real save() method
    super(OperationPlan, self).save(*args, **kwargs)

  class Meta(AuditModel.Meta):
    db_table = 'operationplan'
    verbose_name = _('operationplan')
    verbose_name_plural = _('operationplans')
    ordering = ['id']


class OperationPlanResource(models.Model):
  # Database fields
  resource = models.CharField(_('resource'), max_length=300, db_index=True)
  operationplan = models.ForeignKey(
    OperationPlan, verbose_name=_('operationplan'), db_index=True
    )
  quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=6)
  startdate = models.DateTimeField(_('startdate'), db_index=True)
  enddate = models.DateTimeField(_('enddate'), db_index=True)
  setup = models.CharField(_('setup'), max_length=300, null=True)

  def __str__(self):
      return "%s %s %s" % (self.resource, self.startdate, self.enddate)

  class Meta:
    db_table = 'operationplanresource'
    ordering = ['resource', 'startdate']
    verbose_name = _('operationplan resource')
    verbose_name_plural = _('operationplan resources')


class OperationPlanMaterial(models.Model):
  # Database fields
  buffer = models.CharField(_('buffer'), max_length=300, db_index=True)
  operationplan = models.ForeignKey(
    OperationPlan, verbose_name=_('operationplan'), db_index=True
    )
  quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=6)
  flowdate = models.DateTimeField(_('date'), db_index=True)
  onhand = models.DecimalField(_('onhand'), max_digits=15, decimal_places=6)

  def __str__(self):
    return "%s %s %s" % (self.buffer, self.flowdate, self.quantity)

  class Meta:
    db_table = 'operationplanmaterial'
    ordering = ['buffer', 'flowdate']
    verbose_name = _('operationplan material')
    verbose_name_plural = _('operationplan materials')


class DistributionOrder(OperationPlan):

  class DistributionOrderManager(models.Manager):

    def get_queryset(self):
      return super(DistributionOrder.DistributionOrderManager, self).get_queryset() \
        .filter(type='DO')
        #.defer("operation", "owner", "supplier", "location")

  objects = DistributionOrderManager()

  def save(self, *args, **kwargs):
    self.type = 'DO'
    self.operation = self.owner = self.location = self.supplier = None
    super(DistributionOrder, self).save(*args, **kwargs)

  class Meta:
    proxy = True
    verbose_name = _('distribution order')
    verbose_name_plural = _('distribution orders')


class PurchaseOrder(OperationPlan):

  class PurchaseOrderManager(models.Manager):

    def get_queryset(self):
      return super(PurchaseOrder.PurchaseOrderManager, self).get_queryset() \
        .filter(type='PO')
        # Note: defer screws up the model name when deleting a PO
        #.defer("operation", "owner", "origin", "destination")

  objects = PurchaseOrderManager()

  def save(self, *args, **kwargs):
    self.type = 'PO'
    self.operation = self.owner = self.origin = self.destination = None
    super(PurchaseOrder, self).save(*args, **kwargs)

  class Meta:
    proxy = True
    verbose_name = _('purchase order')
    verbose_name_plural = _('purchase orders')


class ManufacturingOrder(OperationPlan):

  class ManufacturingOrderManager(models.Manager):

    def get_queryset(self):
      return super(ManufacturingOrder.ManufacturingOrderManager, self).get_queryset() \
        .filter(type='MO')
        # Note: defer screws up the model name when deleting a PO
        # .defer("supplier", "location", "origin", "destination")

  objects = ManufacturingOrderManager()

  def save(self, *args, **kwargs):
    self.type = 'MO'
    self.supplier = self.item = self.location = self.origin = self.destination = None
    super(ManufacturingOrder, self).save(*args, **kwargs)

  class Meta:
    proxy = True
    verbose_name = _('manufacturing order')
    verbose_name_plural = _('manufacturing orders')


class DeliveryOrder(OperationPlan):

  class DeliveryOrderManager(models.Manager):

    def get_queryset(self):
      return super(DeliveryOrder.DeliveryOrderManager, self).get_queryset() \
        .filter(demand__isnull=False, owner__isnull=True)
        # Note: defer screws up the model name when deleting a PO
        # .defer("operation", "owner", "supplier", "location", "origin", "destination")

  objects = DeliveryOrderManager()

  def save(self, *args, **kwargs):
    self.type = 'DLVR'
    self.supplier = self.item = self.location = self.origin = self.destination = self.operation = self.owner = None
    super(DeliveryOrder, self).save(*args, **kwargs)

  class Meta:
    proxy = True
    verbose_name = _('customer shipment')
    verbose_name_plural = _('customer shipments')
