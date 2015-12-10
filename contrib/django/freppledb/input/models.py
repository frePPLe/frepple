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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from freppledb.common.fields import DurationField
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
    decimal_places=4, default='0.00', null=True, blank=True,
    help_text=_('Value to be used when no entry is effective')
    )

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'calendar'
    #. Translators: Translation included with Django
    verbose_name = _('Calendar')
    #. Translators: Translation included with Django
    verbose_name_plural = _('Calendars')
    ordering = ['name']


class CalendarBucket(AuditModel):

  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  #. Translators: Translation included with Django
  calendar = models.ForeignKey(Calendar, verbose_name=_('Calendar'), related_name='buckets')
  startdate = models.DateTimeField(_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), null=True, blank=True, default=datetime(2030, 12, 31))
  value = models.DecimalField(
    _('value'), default='0.00', blank=True,
    max_digits=15, decimal_places=4
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
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  category = models.CharField(_('category'), max_length=300, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=300, null=True, blank=True, db_index=True)
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
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  category = models.CharField(_('category'), max_length=300, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=300, null=True, blank=True, db_index=True)

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
  operation = models.ForeignKey(
    'Operation', verbose_name=_('delivery operation'), null=True, blank=True,
    help_text=_("Default operation used to ship a demand for this item")
    )
  price = models.DecimalField(
    _('price'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("Selling price of the item")
    )

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'item'
    verbose_name = _('item')
    verbose_name_plural = _('items')
    ordering = ['name']


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
    db_index=True, related_name='itemsuppliers'
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), null=True, blank=True,
    db_index=True, related_name='itemsuppliers'
    )
  supplier = models.ForeignKey(
    Supplier, verbose_name=_('supplier'),
    db_index=True, related_name='suppliers'
    )
  leadtime = DurationField(
    _('lead time'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Purchasing lead time')
    )
  sizeminimum = models.DecimalField(
    _('size minimum'), max_digits=15, decimal_places=4,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum purchasing quantity")
    )
  sizemultiple = models.DecimalField(
    _('size multiple'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("A multiple purchasing quantity")
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=4,
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
    db_index=True, related_name='distributions'
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), null=True, blank=True,
    db_index=True, related_name='itemdistributions_destination'
    )
  origin = models.ForeignKey(
    Location, verbose_name=_('origin'),
    db_index=True, related_name='itemdistributions_origin'
    )
  leadtime = DurationField(
    _('lead time'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('lead time')
    )
  sizeminimum = models.DecimalField(
    _('size minimum'), max_digits=15, decimal_places=4,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum shipping quantity")
    )
  sizemultiple = models.DecimalField(
    _('size multiple'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("A multiple shipping quantity")
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=4,
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
  location = models.ForeignKey(
    Location, verbose_name=_('location'),
    null=True, blank=True, db_index=True
    )
  fence = DurationField(
    _('release fence'), max_digits=15, decimal_places=4, null=True, blank=True,
    help_text=_("Operationplans within this time window from the current day are expected to be released to production ERP")
    )
  posttime = DurationField(
    _('post-op time'), max_digits=15, decimal_places=4, null=True, blank=True,
    help_text=_("A delay time to be respected as a soft constraint after ending the operation")
    )
  sizeminimum = models.DecimalField(
    _('size minimum'), max_digits=15, decimal_places=4,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum quantity for operationplans")
    )
  sizemultiple = models.DecimalField(
    _('size multiple'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("A multiple quantity for operationplans")
    )
  sizemaximum = models.DecimalField(
    _('size maximum'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("A maximum quantity for operationplans")
    )
  cost = models.DecimalField(
    _('cost'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("Cost per operationplan unit")
    )
  duration = DurationField(
    _('duration'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("A fixed duration for the operation")
    )
  duration_per = DurationField(
    _('duration per unit'), null=True, blank=True,
    max_digits=15, decimal_places=4,
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
    ('procure', _('Procure')),
  )

  # Fields common to all buffer types
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  category = models.CharField(_('category'), max_length=300, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=300, null=True, blank=True, db_index=True)
  type = models.CharField(_('type'), max_length=20, null=True, blank=True, choices=types, default='default')
  location = models.ForeignKey(
    Location, verbose_name=_('location'), null=True,
    blank=True, db_index=True
    )
  item = models.ForeignKey(Item, verbose_name=_('item'), db_index=True, null=True)
  onhand = models.DecimalField(
    _('onhand'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    default="0.00", help_text=_('current inventory')
    )
  minimum = models.DecimalField(
    _('minimum'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    default="0.00", help_text=_('Safety stock')
    )
  minimum_calendar = models.ForeignKey(
    Calendar, verbose_name=_('minimum calendar'),
    null=True, blank=True,
    help_text=_('Calendar storing a time-dependent safety stock profile')
    )
  producing = models.ForeignKey(
    Operation, verbose_name=_('producing'),
    null=True, blank=True, related_name='used_producing',
    help_text=_('Operation to replenish the buffer')
    )
  # Extra fields for procurement buffers
  leadtime = DurationField(
    _('leadtime'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Leadtime for supplier of a procure buffer')
    )
  fence = DurationField(
    _('fence'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Frozen fence for creating new procurements')
    )
  min_inventory = models.DecimalField(
    _('min_inventory'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Inventory level that triggers replenishment of a procure buffer')
    )
  max_inventory = models.DecimalField(
    _('max_inventory'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Inventory level to which a procure buffer is replenished')
    )
  min_interval = DurationField(
    _('min_interval'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Minimum time interval between replenishments of a procure buffer')
    )
  max_interval = DurationField(
    _('max_interval'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Maximum time interval between replenishments of a procure buffer')
    )
  size_minimum = models.DecimalField(
    _('size_minimum'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Minimum size of replenishments of a procure buffer')
    )
  size_multiple = models.DecimalField(
    _('size_multiple'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Replenishments of a procure buffer are a multiple of this quantity')
    )
  size_maximum = models.DecimalField(
    _('size_maximum'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Maximum size of replenishments of a procure buffer')
    )

  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    if self.type == 'infinite' or self.type == 'procure':
      # Handle irrelevant fields for infinite and procure buffers
      self.producing = None
    if self.type != 'procure':
      # Handle irrelevant fields for non-procure buffers
      self.leadtime = None
      self.fence = None
      self.min_inventory = None
      self.max_inventory = None
      self.size_minimum = None
      self.size_multiple = None
      self.size_maximum = None
    super(Buffer, self).save(*args, **kwargs)

  class Meta(AuditModel.Meta):
    db_table = 'buffer'
    verbose_name = _('buffer')
    verbose_name_plural = _('buffers')
    ordering = ['name']


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
  duration = DurationField(
    _('duration'), max_digits=15, decimal_places=0, null=True, blank=True,
    help_text=_("Duration of the changeover")
    )
  cost = models.DecimalField(
    _('cost'), max_digits=15, decimal_places=4, null=True, blank=True,
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
    ('default', _('Default')),
    ('buckets', _('Buckets')),
    ('infinite', _('Infinite')),
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
    max_digits=15, decimal_places=4,
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
    max_digits=15, decimal_places=4,
    help_text=_("Cost for using 1 unit of the resource for 1 hour"))
  maxearly = DurationField(
    _('max early'), max_digits=15, decimal_places=0,
    null=True, blank=True,
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
    Resource, verbose_name=_('resource'), db_index=True, related_name='skills'
    )
  skill = models.ForeignKey(
    Skill, verbose_name=_('skill'), db_index=True, related_name='resources'
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


class Flow(AuditModel):
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
    db_index=True, related_name='flows'
    )
  thebuffer = models.ForeignKey(
    Buffer, verbose_name=_('buffer'),
    db_index=True, related_name='flows'
    )
  quantity = models.DecimalField(
    _('quantity'), default='1.00',
    max_digits=15, decimal_places=4,
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
    help_text=_('Optional name of this flow')
    )
  alternate = models.CharField(
    _('alternate'), max_length=300, null=True, blank=True,
    help_text=_('Puts the flow in a group of alternate flows')
    )
  priority = models.IntegerField(
    _('priority'), default=1, null=True, blank=True,
    help_text=_('Priority of this flow in a group of alternates')
    )
  search = models.CharField(
    _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select preferred alternate')
    )

  def __str__(self):
    return '%s - %s' % (self.operation.name, self.thebuffer.name)

  class Meta(AuditModel.Meta):
    db_table = 'flow'
    unique_together = (('operation', 'thebuffer'),)  # TODO also include effectivity in this
    verbose_name = _('flow')
    verbose_name_plural = _('flows')


class Load(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  operation = models.ForeignKey(Operation, verbose_name=_('operation'), db_index=True, related_name='loads')
  resource = models.ForeignKey(Resource, verbose_name=_('resource'), db_index=True, related_name='loads')
  skill = models.ForeignKey(Skill, verbose_name=_('skill'), null=True, blank=True, db_index=True, related_name='loads')
  quantity = models.DecimalField(
    _('quantity'), default='1.00',
    max_digits=15, decimal_places=4
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
  alternate = models.CharField(
    _('alternate'), max_length=300, null=True, blank=True,
    help_text=_('Puts the load in a group of alternate loads')
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
    db_table = 'resourceload'
    unique_together = (('operation', 'resource'),)  # TODO also include effectivity in this
    verbose_name = _('load')
    verbose_name_plural = _('loads')


class OperationPlan(AuditModel):
  # Possible status
  orderstatus = (
    ('proposed', _('proposed')),
    ('confirmed', _('confirmed')),
    ('closed', _('closed')),
  )

  # Database fields
  id = models.IntegerField(
    _('identifier'), primary_key=True,
    help_text=_('Unique identifier of an operationplan')
    )
  status = models.CharField(
    _('status'), null=True, blank=True, max_length=20, choices=orderstatus,
    help_text=_('Status of the order')
    )
  reference = models.CharField(
    _('reference'), max_length=300, null=True, blank=True,
    help_text=_('External reference of this order')
    )
  operation = models.ForeignKey(
    Operation, verbose_name=_('operation'),
    db_index=True
    )
  quantity = models.DecimalField(
    _('quantity'), max_digits=15,
    decimal_places=4, default='1.00'
    )
  startdate = models.DateTimeField(_('start date'), help_text=_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), help_text=_('end date'), null=True, blank=True)
  criticality = models.DecimalField(
    _('criticality'), max_digits=15,
    decimal_places=4, null=True, blank=True,
    )
  owner = models.ForeignKey(
    'self', verbose_name=_('owner'), null=True, blank=True,
    related_name='xchildren', help_text=_('Hierarchical parent')
    )

  def __str__(self):
    return str(self.id)

  class Meta(AuditModel.Meta):
    db_table = 'operationplan'
    verbose_name = _('operationplan')
    verbose_name_plural = _('operationplans')
    ordering = ['id']


class DistributionOrder(AuditModel):
  # Possible status
  orderstatus = (
    ('proposed', _('proposed')),
    ('confirmed', _('confirmed')),
    ('closed', _('closed')),
  )

  # Database fields
  id = models.IntegerField(
    _('identifier'), primary_key=True,
    help_text=_('Unique identifier')
    )
  reference = models.CharField(
    _('reference'), max_length=300, null=True, blank=True,
    help_text=_('External reference of this order')
    )
  status = models.CharField(
    _('status'), null=True, blank=True, max_length=20, choices=orderstatus,
    help_text=_('Status of the order')
    )
  item = models.ForeignKey(
    Item, verbose_name=_('item'),
    db_index=True
    )
  origin = models.ForeignKey(
    Location, verbose_name=_('origin'), null=True, blank=True,
    related_name='origins', db_index=True
    )
  destination = models.ForeignKey(
    Location, verbose_name=_('destination'),
    related_name='destinations', db_index=True
    )
  quantity = models.DecimalField(
    _('quantity'), max_digits=15,
    decimal_places=4, default='1.00'
    )
  startdate = models.DateTimeField(_('start date'), help_text=_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), help_text=_('end date'), null=True, blank=True)
  consume_material = models.BooleanField(_('consume material'), blank=True, default=True,
    help_text=_('Consume material at origin location')
    )
  criticality = models.DecimalField(
    _('criticality'), max_digits=15,
    decimal_places=4, null=True, blank=True,
    )

  def __str__(self):
    return str(self.id)

  class Meta(AuditModel.Meta):
    db_table = 'distribution_order'
    verbose_name = _('distribution order')
    verbose_name_plural = _('distribution orders')
    ordering = ['id']


class PurchaseOrder(AuditModel):
  # Possible status
  orderstatus = (
    ('proposed', _('proposed')),
    ('confirmed', _('confirmed')),
    ('closed', _('closed')),
  )

  # Database fields
  id = models.IntegerField(
    _('identifier'), primary_key=True,
    help_text=_('Unique identifier')
    )
  reference = models.CharField(
    _('reference'), max_length=300, null=True, blank=True,
    help_text=_('External reference of this order')
    )
  status = models.CharField(
    _('status'), null=True, blank=True, max_length=20, choices=orderstatus,
    help_text=_('Status of the order')
    )
  item = models.ForeignKey(
    Item, verbose_name=_('item'),
    db_index=True
    )
  supplier = models.ForeignKey(
    Supplier, verbose_name=_('supplier'),
    db_index=True
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'),
    db_index=True
    )
  quantity = models.DecimalField(
    _('quantity'), max_digits=15,
    decimal_places=4, default='1.00'
    )
  startdate = models.DateTimeField(_('start date'), help_text=_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), help_text=_('end date'), null=True, blank=True)
  criticality = models.DecimalField(
    _('criticality'), max_digits=15,
    decimal_places=4, null=True, blank=True,
    )

  def __str__(self):
    return str(self.id)

  class Meta(AuditModel.Meta):
    db_table = 'purchase_order'
    verbose_name = _('purchase order')
    verbose_name_plural = _('purchase orders')
    ordering = ['id']


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
    Customer, verbose_name=_('customer'), null=True, blank=True, db_index=True
    )
  item = models.ForeignKey(
    Item, verbose_name=_('item'), null=True, blank=True, db_index=True
    )
  location = models.ForeignKey(
    Location, verbose_name=_('location'), null=True, blank=True, db_index=True
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
    _('quantity'), max_digits=15, decimal_places=4
    )
  priority = models.PositiveIntegerField(
    _('priority'), default=10, choices=demandpriorities,
    help_text=_('Priority of the demand (lower numbers indicate more important demands)')
    )
  minshipment = models.DecimalField(
    _('minimum shipment'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_('Minimum shipment quantity when planning this demand')
    )
  maxlateness = DurationField(
    _('maximum lateness'), null=True, blank=True,
    max_digits=15, decimal_places=4,
    help_text=_("Maximum lateness allowed when planning this demand")
    )

  # Convenience methods
  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'demand'
    verbose_name = _('sales order')
    verbose_name_plural = _('sales orders')
    ordering = ['name']
