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

from django.db import models
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.db.models import signals
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.encoding import force_unicode

from freppledb.common.fields import DurationField


CALENDARID = None


class HierarchyModel(models.Model):
  lft = models.PositiveIntegerField(db_index = True, editable=False, null=True, blank=True)
  rght = models.PositiveIntegerField(null=True, editable=False, blank=True)
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True,
    help_text=_('Unique identifier'))
  owner = models.ForeignKey('self', verbose_name=_('owner'), null=True, blank=True, related_name='xchildren',
    help_text=_('Hierarchical parent'))

  def save(self, *args, **kwargs):
    # Trigger recalculation of the hieracrhy
    self.lft = None
    self.rght = None

    # Call the real save() method
    super(HierarchyModel, self).save(*args, **kwargs)

  class Meta:
    abstract = True

  @classmethod
  def rebuildHierarchy(cls, database = DEFAULT_DB_ALIAS):

    # Verify whether we need to rebuild or not.
    # We search for the first record whose lft field is null.
    if len(cls.objects.using(database).filter(lft__isnull=True)[:1]) == 0:
      return

    tmp_debug = settings.DEBUG
    settings.DEBUG = False
    nodes = {}
    transaction.enter_transaction_management(using=database)
    transaction.managed(True, using=database)
    cursor = connections[database].cursor()

    def tagChildren(me, left):
      right = left + 1
      # get all children of this node
      for i, j in nodes.items():
        if j == me:
          # Recursive execution of this function for each child of this node
          right = tagChildren(i, right)

      # After processing the children of this node now know its left and right values
      cursor.execute(
        'update %s set lft=%d, rght=%d where name = %%s' % (cls._meta.db_table, left, right),
        [me]
        )

      # Return the right value of this node + 1
      return right + 1

    # Load all nodes in memory
    for i in cls.objects.using(database).values('name','owner'):
      nodes[i['name']] = i['owner']

    # Loop over nodes without parent
    cnt = 1
    for i, j in sorted(nodes.items()):
      if j == None:
        cnt = tagChildren(i,cnt)
    transaction.commit(using=database)
    settings.DEBUG = tmp_debug
    transaction.leave_transaction_management(using=database)


class AuditModel(models.Model):
  '''
  This is an abstract base model.
  It implements the capability to maintain the date of the last modification of the record.
  '''
  # Database fields
  lastmodified = models.DateTimeField(_('last modified'), editable=False, db_index=True, default=datetime.now())

  def save(self, *args, **kwargs):
    # Update the field with every change
    self.lastmodified = datetime.now()

    # Call the real save() method
    super(AuditModel, self).save(*args, **kwargs)

  class Meta:
    abstract = True


searchmode = (
  ('',_('priority')),
  ('PRIORITY',_('priority')),
  ('MINCOST',_('minimum cost')),
  ('MINPENALTY',_('minimum penalty')),
  ('MINCOSTPENALTY',_('minimum cost plus penalty'))
)


class Parameter(AuditModel):
  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  value = models.CharField(_('value'), max_length=settings.NAMESIZE, null=True, blank=True)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)

  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'parameter'
    verbose_name = _('parameter')
    verbose_name_plural = _('parameters')


class Calendar(AuditModel):
  # Types of calendars
  calendartypes = (
    ('',_('double')),
    ('calendar_double',_('double')),
    ('calendar_boolean',_('boolean')),
  )

  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  type = models.CharField(_('type'), _('type'), max_length=20,
    null=True, blank=True, choices=calendartypes,
    help_text= _('Type of data values stored in the calendar')
    )
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True,
    blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True,
    blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE,
    null=True, blank=True, db_index=True)
  defaultvalue = models.DecimalField(_('default value'), max_digits=settings.MAX_DIGITS,
    decimal_places=settings.DECIMAL_PLACES, default='0.00',
    help_text= _('Value to be used when no entry is effective')
    )

  def currentvalue(self):
    ''' Returns the value of the calendar on this moment.'''
    return self.getvalue(datetime.now())
  currentvalue.short_description = 'current value'

  def getvalue(self, when):
    '''Return the value of the calendar on a certain day.'''
    curValue = self.defaultvalue
    curPriority = None
    # Loop through the entries to find the effective one
    for b in self.buckets.all():
      if not curPriority or curPriority > b.priority:
        thisValue = b.getvalue(when)
        if thisValue:
          # The entry is valid value on this day, and has
          # a higher priority than other entries.
          curValue = thisValue
          curPriority = b.priority
    return curValue

  def setvalue(self, start, end, value, user=None):
    '''Update calendar buckets such that the calendar value is changed
    in the specified date range.
    The admin log is updated if a user is passed as argument.

    @todo The calendar editing isnt as flexible as the frePPLe core: the
    user interface only support non-overlapping calendar entries to keep SQL
    statements easy.
    '''
    db = self._state.db
    for b in self.buckets.filter(enddate__gt=start,startdate__lt=end).order_by('startdate'):
      if b.enddate <= start:
        # Earlier bucket
        continue
      elif b.startdate >= end:
        # Later bucket
        return
      elif b.startdate == start and b.enddate <= end:
        # Overwrite entire bucket
        b.value = str(value)
        b.save(using=db)
      elif b.startdate >= start and b.enddate <= end:
        # Bucket became redundant
        b.delete(using=db)
      elif b.startdate < start and b.enddate > end:
        # New value is completely within this bucket
        CalendarBucket(calendar=self, startdate=start, value=str(value)).save(using=db)
        CalendarBucket(calendar=self, startdate=end, value=str(b.value)).save(using=db)
      elif b.startdate < start:
        # An existing bucket is partially before the new daterange
        CalendarBucket(calendar=self, startdate=start, enddate=end, value=str(value)).save(using=db)
        b.enddate = start
        b.save(using=db)
      elif b.enddate > end:
        # An existing bucket is partially after the new daterange
        CalendarBucket(calendar=self, startdate=b.startdate, enddate=end, value=str(value)).save(using=db)
        b.startdate = end
        b.save(using=db)
    if self.buckets.count() == 0:
      # There wasn't any bucket yet...
      CalendarBucket(calendar=self, startdate=start, value=str(value)).save(using=db)
      CalendarBucket(calendar=self, startdate=end, value="0").save(using=db)
    # Create a change log entry, if a user is specified
    if user:
      global CALENDARID
      if not CALENDARID:
        CALENDARID = ContentType.objects.get_for_model(models.get_model('input','calendar')).id
      LogEntry(
        user_id = user.id, content_type_id = CALENDARID,
        object_id = self.name, object_repr = force_unicode(self)[:200],
        action_flag = CHANGE,
        change_message = "Updated value to %s for the daterange %s to %s" % (value, start, end)
        ).save(using=db)

  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'calendar'
    verbose_name = _('calendar')
    verbose_name_plural = _('calendars')
    ordering = ['name']


class CalendarBucket(AuditModel):
  '''
  @todo The calendar editing isnt as flexible as the frePPLe core: the
  user interface only support non-overlapping calendar entries to keep SQL
  statements easy.
  The core engine allows the end date to be edited independently.
  '''
  # Database fields
  calendar = models.ForeignKey(Calendar, verbose_name=_('calendar'), related_name='buckets')
  startdate = models.DateTimeField(_('start date'), null=True, blank=True)
  enddate = models.DateTimeField(_('end date'), editable=False, null=True, blank=True, default=datetime(2030,12,31))
  value = models.DecimalField(_('value'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='0.00', blank=True)
  priority = models.IntegerField(_('priority'), default=0, blank=True)
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, null=True, blank=True)

  def getvalue(self, when):
    if (self.startdate and when < self.startdate) or (self.enddate and when >= self.enddate):
      # Outside of validity range
      return None
    return self.value

  def __unicode__(self):
    if self.name: return self.name
    return u"%s - %s" % (self.startdate, self.enddate)

  class Meta(AuditModel.Meta):
    ordering = ['startdate','name']
    db_table = 'calendarbucket'
    verbose_name = _('calendar bucket')
    verbose_name_plural = _('calendar buckets')

  @staticmethod
  def updateEndDate(instance, **kwargs):
    '''
    The user edits the start date of the calendar buckets.
    This method will automatically update the end date of a bucket to be
    equal to the start date of the next bucket.

    @todo The calendar editing isnt as flexible as the frePPLe core: the
    user interface only support non-overlapping calendar entries to keep SQL
    statements easy.
    '''
    # Loop through all buckets
    prev = None
    for i in instance.calendar.buckets.all():
      if prev and i.startdate != prev.enddate:
        # Update the end date of the previous bucket to the start date of this one
        prev.enddate = i.startdate
        if prev.enddate == prev.startdate:
          prev.delete()
        else:
          prev.save()
      prev = i
    if prev and prev.enddate != datetime(2030,12,31):
      # Update the last entry
      prev.enddate = datetime(2030,12,31)
      prev.save()

  @staticmethod
  def insertBucket(instance, **kwargs):
    # If the end date is specified, we take it for granted.
    # Ideally we would check all inserts, but that is very time consuming
    # when creating or restoring big datasets.
    if instance.enddate == datetime(2030,12,31) or not kwargs['created']:
      CalendarBucket.updateEndDate(instance)

# This dispatcher function is called after a bucket is saved. There seems no cleaner way to do this, since
# the method calendar.buckets.all() is only up to date after the save...
# The method is not very efficient: called for every single bucket, and recursively triggers
# another save and dispatcher event
signals.post_save.connect(CalendarBucket.insertBucket, sender=CalendarBucket)
signals.post_delete.connect(CalendarBucket.updateEndDate, sender=CalendarBucket)


class Location(AuditModel, HierarchyModel):
  # Database fields
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  available = models.ForeignKey(Calendar, verbose_name=_('available'),
    null=True, blank=True,
    help_text=_('Calendar defining the working hours and holidays of this location'))

  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'location'
    verbose_name = _('location')
    verbose_name_plural = _('locations')
    ordering = ['name']


class Customer(AuditModel,HierarchyModel):
  # Database fields
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)

  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'customer'
    verbose_name = _('customer')
    verbose_name_plural = _('customers')
    ordering = ['name']


class Item(AuditModel,HierarchyModel):
  # Database fields
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  operation = models.ForeignKey('Operation', verbose_name=_('delivery operation'), null=True, blank=True,
    help_text=_("Default operation used to ship a demand for this item"))
  price = models.DecimalField(_('price'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Selling price of the item"))

  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'item'
    verbose_name = _('item')
    verbose_name_plural = _('items')
    ordering = ['name']


class Operation(AuditModel):
  # Types of operations
  operationtypes = (
    ('',_('fixed_time')),
    ('operation_fixed_time',_('fixed_time')),
    ('operation_time_per',_('time_per')),
    ('operation_routing',_('routing')),
    ('operation_alternate',_('alternate')),
  )

  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  type = models.CharField(_('type'), _('type'), max_length=20, null=True, blank=True, choices=operationtypes)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  location = models.ForeignKey(Location, verbose_name=_('location'), null=True,
    blank=True, db_index=True)
  fence = DurationField(_('release fence'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Operationplans within this time window from the current day are expected to be released to production ERP"))
  pretime = DurationField(_('pre-op time'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("A delay time to be respected as a soft constraint before starting the operation"))
  posttime = DurationField(_('post-op time'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("A delay time to be respected as a soft constraint after ending the operation"))
  sizeminimum = models.DecimalField(_('size minimum'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES,
    null=True, blank=True, default='1.0',
    help_text=_("A minimum quantity for operationplans"))
  sizemultiple = models.DecimalField(_('size multiple'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("A multiple quantity for operationplans"))
  sizemaximum = models.DecimalField(_('size maximum'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("A maximum quantity for operationplans"))
  cost = models.DecimalField(_('cost'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Cost per operationplan unit"))
  duration = DurationField(_('duration'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("A fixed duration for the operation"))
  duration_per = DurationField(_('duration per unit'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("A variable duration for the operation"))
  search = models.CharField(_('search mode'), _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select prefered alternate')
    )

  def __unicode__(self): return self.name

  def save(self, *args, **kwargs):
    if self.type is None or self.type == '' or self.type == 'operation_fixed_time':
      self.duration_per = None
      self.search = None
    elif self.type == 'operation_alternate':
      self.duration = None
      self.duration_per = None
    elif self.type != 'operation_time_per':
      self.duration = None
      self.duration_per = None
      self.search = None

    # Call the real save() method
    super(Operation, self).save(*args, **kwargs)

  class Meta(AuditModel.Meta):
    db_table = 'operation'
    verbose_name = _('operation')
    verbose_name_plural = _('operations')
    ordering = ['name']


class SubOperation(AuditModel):
  # Database fields
  operation = models.ForeignKey(Operation, verbose_name=_('operation'),
    related_name='suboperations')
  priority = models.IntegerField(_('priority'), default=1)
  suboperation = models.ForeignKey(Operation, verbose_name=_('suboperation'),
    related_name='superoperations')
  effective_start = models.DateTimeField(_('effective start'), null=True, blank=True)
  effective_end = models.DateTimeField(_('effective end'), null=True, blank=True)

  def __unicode__(self):
    return self.operation.name \
      + "   " + str(self.priority) \
      + "   " + self.suboperation.name

  class Meta(AuditModel.Meta):
    db_table = 'suboperation'
    ordering = ['operation','priority','suboperation']
    verbose_name = _('suboperation')
    verbose_name_plural = _('suboperations')


class Buffer(AuditModel,HierarchyModel):
  # Types of buffers
  buffertypes = (
    ('',_('Default')),
    ('buffer_infinite',_('Infinite')),
    ('buffer_procure',_('Procure')),
  )

  # Fields common to all buffer types
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  type = models.CharField(_('type'), max_length=20, null=True, blank=True, choices=buffertypes, default='')
  location = models.ForeignKey(Location, verbose_name=_('location'), null=True,
    blank=True, db_index=True)
  item = models.ForeignKey(Item, verbose_name=_('item'), db_index=True, null=True)
  onhand = models.DecimalField(_('onhand'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES,
    default="0.00", null=True, blank=True, help_text=_('current inventory'))
  minimum = models.DecimalField(_('minimum'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES,
    default="0.00", null=True, blank=True, help_text=_('Safety stock'))
  minimum_calendar = models.ForeignKey(Calendar, verbose_name=_('minimum calendar'),
    null=True, blank=True,
    help_text=_('Calendar storing a time-dependent safety stock profile'))
  producing = models.ForeignKey(Operation, verbose_name=_('producing'),
    null=True, blank=True, related_name='used_producing',
    help_text=_('Operation to replenish the buffer'))
  carrying_cost = models.DecimalField(_('carrying cost'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Cost of holding inventory in this buffer, expressed as an annual percentage of the item price."))
  # Extra fields for procurement buffers
  leadtime = DurationField(_('leadtime'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Leadtime for supplier of a procure buffer'))
  fence = DurationField(_('fence'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Frozen fence for creating new procurements'))
  min_inventory = models.DecimalField(_('min_inventory'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Inventory level that triggers replenishment of a procure buffer'))
  max_inventory = models.DecimalField(_('max_inventory'),max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Inventory level to which a procure buffer is replenished'))
  min_interval = DurationField(_('min_interval'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Minimum time interval between replenishments of a procure buffer'))
  max_interval = DurationField(_('max_interval'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Maximum time interval between replenishments of a procure buffer'))
  size_minimum = models.DecimalField(_('size_minimum'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Minimum size of replenishments of a procure buffer'))
  size_multiple = models.DecimalField(_('size_multiple'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Replenishments of a procure buffer are a multiple of this quantity'))
  size_maximum =  models.DecimalField(_('size_maximum'),max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Maximum size of replenishments of a procure buffer'))

  def __unicode__(self): return self.name

  def save(self, *args, **kwargs):
    if self.type == 'buffer_infinite' or self.type == 'buffer_procure':
      # Handle irrelevant fields for infinite and procure buffers
      self.producing = None
    if self.type != 'buffer_procure':
      # Handle irrelevant fields for non-procure buffers
      self.leadtime = None
      self.fence = None
      self.min_inventory = None
      self.max_inventory = None
      self.min_interval = None
      self.max_interval = None
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
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)

  # Methods
  def __unicode__(self): return self.name

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
  setupmatrix = models.ForeignKey(SetupMatrix, verbose_name=_('setup matrix'), related_name='rules')
  priority = models.IntegerField(_('priority'))
  fromsetup = models.CharField(_('from setup'), max_length=settings.NAMESIZE, blank=True, null=True,
    help_text=_("Name of the old setup (wildcard characters are supported)"))
  tosetup = models.CharField(_('to setup'), max_length=settings.NAMESIZE, blank=True, null=True,
    help_text=_("Name of the new setup (wildcard characters are supported)"))
  duration = DurationField(_('duration'), max_digits=settings.MAX_DIGITS, decimal_places=0, null=True, blank=True,
    help_text=_("Duration of the changeover"))
  cost = models.DecimalField(_('cost'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Cost of the conversion"))

  def __unicode__(self):
    return u"%s - %s" % (self.setupmatrix.name, self.priority)

  class Meta(AuditModel.Meta):
    ordering = ['priority',]
    db_table = 'setuprule'
    unique_together = (('setupmatrix', 'priority'),)
    verbose_name = _('setup matrix rule')
    verbose_name_plural = _('setup matrix rules')


class Resource(AuditModel,HierarchyModel):
  # Types of resources
  resourcetypes = (
    ('',_('Default')),
    ('resource_infinite',_('Infinite')),
  )

  # Database fields
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  type = models.CharField(_('type'), max_length=20, null=True, blank=True, choices=resourcetypes, default='')
  maximum = models.DecimalField(_('maximum'),
    max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES,
    default="1.00", null=True, blank=True, help_text=_('Size of the resource'))
  maximum_calendar = models.ForeignKey(Calendar, verbose_name=_('maximum calendar'),
    null=True, blank=True,
    help_text=_('Calendar defining the resource size varying over time'))
  location = models.ForeignKey(Location, verbose_name=_('location'),
    null=True, blank=True, db_index=True)
  cost = models.DecimalField(_('cost'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Cost for using 1 unit of the resource for 1 hour"))
  maxearly = DurationField(_('max early'),max_digits=settings.MAX_DIGITS, decimal_places=0, null=True, blank=True,
    help_text=_('Time window before the ask date where we look for available capacity'))
  setupmatrix = models.ForeignKey(SetupMatrix, verbose_name=_('setup matrix'),
    null=True, blank=True, db_index=True,
    help_text=_('Setup matrix defining the conversion time and cost'))
  setup = models.CharField(_('setup'), max_length=settings.NAMESIZE, null=True, blank=True,
    help_text=_('Setup of the resource at the start of the plan'))

  # Methods
  def __unicode__(self): return self.name

  def save(self, *args, **kwargs):
    if self.type == 'resource_infinite':
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


class Flow(AuditModel):
  # Types of flow
  flowtypes = (
    ('',_('Start')),
    ('flow_start',_('Start')),
    ('flow_end',_('End')),
  )

  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  operation = models.ForeignKey(Operation, verbose_name=_('operation'),
    db_index=True, related_name='flows')
  thebuffer = models.ForeignKey(Buffer, verbose_name=_('buffer'),
    db_index=True, related_name='flows')
  quantity = models.DecimalField(_('quantity'),max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES,
    default='1.00',
    help_text=_('Quantity to consume or produce per operationplan unit')
    )
  type = models.CharField(_('type'), max_length=20, null=True, blank=True,
    choices=flowtypes,
    help_text=_('Consume/produce material at the start or the end of the operationplan'),
    )
  effective_start = models.DateTimeField(_('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(_('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, null=True, blank=True,
    help_text=_('Optional name of this flow'))
  alternate = models.CharField(_('alternate'), max_length=settings.NAMESIZE, null=True, blank=True,
    help_text=_('Puts the flow in a group of alternate flows'))
  priority = models.IntegerField(_('priority'), default=1, null=True, blank=True,
    help_text=_('Priority of this flow in a group of alternates'))
  search = models.CharField(_('search mode'), _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select prefered alternate')
    )

  def __unicode__(self):
    return '%s - %s' % (self.operation.name, self.thebuffer.name)

  class Meta(AuditModel.Meta):
    db_table = 'flow'
    unique_together = (('operation','thebuffer'),) # TODO also include effectivity in this
    verbose_name = _('flow')
    verbose_name_plural = _('flows')


class Load(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  operation = models.ForeignKey(Operation, verbose_name=_('operation'), db_index=True, related_name='loads')
  resource = models.ForeignKey(Resource, verbose_name=_('resource'), db_index=True, related_name='loads')
  quantity = models.DecimalField(_('quantity'),max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='1.00')
  effective_start = models.DateTimeField(_('effective start'), null=True, blank=True,
    help_text=_('Validity start date')
    )
  effective_end = models.DateTimeField(_('effective end'), null=True, blank=True,
    help_text=_('Validity end date')
    )
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, null=True, blank=True,
    help_text=_('Optional name of this load')
    )
  alternate = models.CharField(_('alternate'), max_length=settings.NAMESIZE, null=True, blank=True,
    help_text=_('Puts the load in a group of alternate loads')
    )
  priority = models.IntegerField(_('priority'), default=1, null=True, blank=True,
    help_text=_('Priority of this load in a group of alternates')
    )
  setup = models.CharField(_('setup'), max_length=settings.NAMESIZE, null=True, blank=True,
    help_text=_('Setup required on the resource for this operation')
    )
  search = models.CharField(_('search mode'), _('search mode'), max_length=20,
    null=True, blank=True, choices=searchmode,
    help_text=_('Method to select prefered alternate')
    )

  def __unicode__(self):
    return '%s - %s' % (self.operation.name, self.resource.name)

  class Meta(AuditModel.Meta):
    db_table = 'resourceload'
    unique_together = (('operation','resource'),)
    verbose_name = _('load')
    verbose_name_plural = _('loads')


class OperationPlan(AuditModel):
  # Database fields
  id = models.IntegerField(_('identifier'),primary_key=True,
    help_text=_('Unique identifier of an operationplan'))
  operation = models.ForeignKey(Operation, verbose_name=_('operation'),
    db_index=True)
  quantity = models.DecimalField(_('quantity'),max_digits=settings.MAX_DIGITS,
    decimal_places=settings.DECIMAL_PLACES, default='1.00')
  startdate = models.DateTimeField(_('start date'),help_text=_('start date'))
  enddate = models.DateTimeField(_('end date'),help_text=_('end date'))
  locked = models.BooleanField(_('locked'),default=True,
    help_text=_('Prevent or allow changes'))

  def __unicode__(self): return str(self.id)

  class Meta(AuditModel.Meta):
    db_table = 'operationplan'
    verbose_name = _('operationplan')
    verbose_name_plural = _('operationplans')
    ordering = ['id']


class Demand(AuditModel,HierarchyModel):
  # The priorities defined here are for convenience only. FrePPLe accepts any number as priority.
  demandpriorities = (
    (1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10'),
    (11,'11'),(12,'12'),(13,'13'),(14,'14'),(15,'15'),(16,'16'),(17,'17'),(18,'18'),(19,'19'),(20,'20')
  )

  # Database fields
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  customer = models.ForeignKey(Customer, verbose_name=_('customer'), null=True, blank=True, db_index=True)
  item = models.ForeignKey(Item, verbose_name=_('item'), db_index=True)
  due = models.DateTimeField(_('due'),help_text=_('Due date of the demand'))
  operation = models.ForeignKey(Operation,
    verbose_name=_('delivery operation'), null=True, blank=True,
    related_name='used_demand',
    help_text=_('Operation used to satisfy this demand'))
  quantity = models.DecimalField(_('quantity'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES)
  priority = models.PositiveIntegerField(_('priority'), default=10, choices=demandpriorities,
    help_text=_('Priority of the demand (lower numbers indicate more important demands)'))
  minshipment = models.DecimalField(_('minimum shipment'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Minimum shipment quantity when planning this demand'))
  maxlateness = models.DecimalField(_('maximum lateness'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Maximum lateness allowed when planning this demand"))

  # Convenience methods
  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'demand'
    verbose_name = _('demand')
    verbose_name_plural = _('demands')
    ordering = ['name']


class Forecast(AuditModel):
  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  category = models.CharField(_('category'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  subcategory = models.CharField(_('subcategory'), max_length=settings.CATEGORYSIZE, null=True, blank=True, db_index=True)
  customer = models.ForeignKey(Customer, verbose_name=_('customer'), null=True, blank=True, db_index=True)
  item = models.ForeignKey(Item, verbose_name=_('item'), db_index=True)
  calendar = models.ForeignKey(Calendar, verbose_name=_('calendar'), null=False)
  operation = models.ForeignKey(Operation, verbose_name=_('delivery operation'), null=True, blank=True,
    related_name='used_forecast', help_text=_('Operation used to satisfy this demand'))
  priority = models.PositiveIntegerField(_('priority'),default=2, choices=Demand.demandpriorities)
  minshipment = models.DecimalField(_('minimum shipment'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_('Minimum shipment quantity when planning this demand'))
  maxlateness = models.DecimalField(_('maximum lateness'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True,
    help_text=_("Maximum lateness allowed when planning this demand"))
  discrete = models.BooleanField(_('discrete'),default=True, help_text=_('Round forecast numbers to integers'))

  # Convenience methods
  def __unicode__(self): return self.name

  def setTotal(self, startdate, enddate, quantity):
    '''
    Update the forecast quantity.
    The logic followed is three-fold:
      - If one or more forecast entries already exist in the daterange, the
        quantities of those entries are proportionally rescaled to fit the
        new quantity.
      - If no forecast entries exist yet, we create a new set of entries
        based on the bucket definition of the forecast calendar. This respects
        the weight ratios as defined in the calendar buckets.
      - In case no calendar or no calendar buckets can be identified, we simply
        create a single forecast entry for the specified daterange.
    '''
    # Assure the end date is later than the start date.
    if startdate > enddate:
      tmp = startdate
      startdate = enddate
      enddate = tmp
    # Assure the type of the quantity
    if not isinstance(quantity,Decimal): quantity = Decimal(str(quantity))
    # Round the quantity, if discrete flag is on
    if self.discrete: quantity = quantity.to_integral()
    # Step 0: Check for forecast entries intersecting with the current daterange
    startdate = startdate.date()
    enddate = enddate.date()
    entries = self.entries.filter(enddate__gt=startdate).filter(startdate__lt=enddate)
    if entries:
      # Case 1: Entries already exist in this daterange, which will be rescaled
      # Case 1, step 1: calculate current quantity and "clip" the existing entries
      # if required.
      current = 0
      for i in entries:
        # Calculate the length of this bucket in seconds
        duration = i.enddate - i.startdate
        duration = duration.days+86400*duration.seconds
        if i.startdate == startdate and i.enddate == enddate:
          # This entry has exactly the same daterange: update the quantity and exit
          i.quantity = str(quantity)
          i.save()
          return
        elif i.startdate < startdate and i.enddate > enddate:
          # This bucket starts before the daterange and also ends later.
          # We need to split the entry in three.
          # Part one: after our daterange, create a new entry
          p = i.enddate - enddate
          q = i.quantity * (p.days+86400*p.seconds) / duration
          if self.discrete: q = round(q)
          self.entries.create( \
             startdate = enddate,
             enddate = i.enddate,
             quantity = str(q),
             ).save()
          # Part two: our date range, create a new entry
          self.entries.create( \
             startdate = startdate,
             enddate = enddate,
             quantity = str(quantity),
             ).save()
          # Part three: before our daterange, update the existing entry
          p = startdate - i.startdate
          i.enddate = startdate
          i.quantity = i.quantity * (p.days+86400*p.seconds) / duration
          if self.discrete: i.quantity = round(i.quantity)
          i.quantity = str(i.quantity)
          i.save()
          # Done with this case...
          return
        elif i.startdate >= startdate and i.enddate <= enddate:
          # Entry falls completely in the range
          # TODO Incomplete???
          current += i.quantity
        elif i.startdate < enddate and i.enddate >= enddate:
          # This entry starts in the range and ends later.
          # Split the entry in two.
          p = i.enddate - enddate
          fraction = Decimal(i.quantity * (p.days+86400*p.seconds) / duration)
          current += i.quantity - fraction
          self.entries.create( \
             startdate = i.startdate,
             enddate = enddate,
             quantity = str(i.quantity - fraction),
             ).save()
          i.startdate = enddate
          if self.discrete: i.quantity = str(round(fraction))
          else: i.quantity = str(fraction)
          i.save()
        elif i.enddate > startdate and i.startdate <= startdate:
          # This entry ends in the range and starts earlier.
          # Split the entry in two.
          p = startdate - i.startdate
          fraction = Decimal(i.quantity * (p.days+86400*p.seconds) / duration)
          current += i.quantity - fraction
          self.entries.create( \
             startdate = startdate,
             enddate = i.enddate,
             quantity = str(i.quantity - fraction),
             ).save()
          i.enddate = startdate
          if self.discrete: i.quantity = str(round(fraction))
          else: i.quantity = str(fraction)
          i.save()
      # Case 1, step 2: Rescale the existing entries
      # Note that we retrieve an updated set of buckets from the database here...
      entries = self.entries.filter(enddate__gt=startdate).filter(startdate__lt=enddate)
      factor = quantity / current
      if factor == 0:
        for i in entries: i.delete()
      elif self.discrete:
        # Only put integers
        remainder = 0
        for i in entries:
          q = Decimal(i.quantity * factor + remainder)
          i.quantity = q.to_integral()
          remainder = q - i.quantity
          i.quantity = str(i.quantity)
          i.save()
      else:
        # No rounding required
        for i in entries:
          i.quantity *= factor
          i.quantity = str(i.quantity)
          i.save()
    else:
      # Case 2: No intersecting forecast entries exist yet. We use the
      # calendar buckets to create a new set of forecast entries, respecting
      # the weight of each bucket.
      # Note: if the calendar values are updated later on, such changes are
      # obviously not reflected any more in the forecast entries.
      cal = self.calendar
      if cal:
        entries = cal.buckets.filter(enddate__gt=startdate).filter(startdate__lte=enddate)
      if entries:
        # Case 2a: We found calendar buckets
        # Case 2a, step 1: compute total sum of weight values
        weights = 0
        for i in entries:
          p = min(i.enddate.date(),enddate) - max(i.startdate.date(),startdate)
          q = i.enddate.date() - i.startdate.date()
          weights +=  i.value * (p.days+86400*p.seconds) / (q.days+86400*q.seconds)
        # Case 2a, step 2: create a forecast entry for each calendar bucket
        remainder = Decimal(0)
        if weights == 0:
          # No non-zero weight buckets found: the update is infeasible
          return
        for i in entries:
          p = min(i.enddate.date(),enddate) - max(i.startdate.date(),startdate)
          q = i.enddate.date() - i.startdate.date()
          q = Decimal(quantity * i.value * (p.days+86400*p.seconds) / (q.days+86400*q.seconds) / weights)
          if self.discrete:
            q += remainder
            k = q.to_integral()
            remainder = q - k
            q = k
          if q > 0:
            self.entries.create( \
              startdate=max(i.startdate.date(),startdate),
              enddate=min(i.enddate.date(),enddate),
              quantity=str(q),
              ).save()
      else:
        # Case 2b: No calendar buckets found at all
        # Create a new entry for the daterange
        self.entries.create(startdate=startdate,enddate=enddate,quantity=str(quantity)).save()

  class Meta(AuditModel.Meta):
    db_table = 'forecast'
    verbose_name = _('forecast')
    verbose_name_plural = _('forecasts')
    ordering = ['name']


# @todo add logic to allow direct import and edit of the forecast demands. Similar to calendar buckets
class ForecastDemand(AuditModel):
  # Database fields
  forecast = models.ForeignKey(Forecast, verbose_name=_('forecast'), null=False, db_index=True, related_name='entries')
  startdate = models.DateField(_('start date'), null=False)
  enddate = models.DateField(_('end date'), null=False)
  quantity = models.DecimalField(_('quantity'), max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default=0)

  # Convenience methods
  def __unicode__(self): return self.forecast.name + " " + str(self.startdate) + " - " + str(self.enddate)

  class Meta(AuditModel.Meta):
    db_table = 'forecastdemand'
    verbose_name = _('forecast demand')
    verbose_name_plural = _('forecast demands')


class Bucket(AuditModel):
  # Create some dummy string for common bucket names to force them to be translated.
  extra_strings = ( _('day'), _('week'), _('month'), _('quarter'), _('year'), _('telescope') )

  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)

  def __unicode__(self): return str(self.name)

  class Meta:
    verbose_name = _('bucket')
    verbose_name_plural = _('buckets')
    db_table = 'bucket'


class BucketDetail(AuditModel):
  # Database fields
  # The primary key is generated automatically
  bucket = models.ForeignKey(Bucket, verbose_name=_('bucket'), db_index=True)
  name = models.CharField(_('name'), max_length=settings.NAMESIZE)
  startdate = models.DateTimeField(_('bucket start'))
  enddate = models.DateTimeField(_('bucket end'))

  class Meta:
    verbose_name = _('bucket date')
    verbose_name_plural = _('bucket dates')
    db_table = 'bucketdetail'
    unique_together = (('bucket', 'startdate'),)
    ordering = ['bucket','startdate']

