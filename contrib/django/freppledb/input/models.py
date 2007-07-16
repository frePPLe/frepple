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
# email : jdetaeye@users.sourceforge.net

from django.db import models
from django.db.models import signals
from datetime import date, datetime
from django.http import HttpRequest
from datetime import datetime
from django.dispatch import dispatcher
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

import sys


# The date format used by the frepple XML data.
dateformat = '%Y-%m-%dT%H:%M:%S'

# This variable defines the number of records to show in the admin lists.
LIST_PER_PAGE = 100

CALENDARID = None

class Plan(models.Model):
    # Database fields
    name = models.CharField(maxlength=60, null=True, blank=True)
    description = models.CharField(maxlength=60, null=True, blank=True)
    currentdate = models.DateTimeField('current date')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return self.name

    class Admin:
        list_display = ('name', 'description', 'currentdate')
        search_fields = ['name', 'description']
        list_per_page = LIST_PER_PAGE

    class Meta:
        verbose_name_plural = 'Plan'  # There will only be 1 plan...


class Dates(models.Model):
    # Database fields
    day = models.DateField(primary_key=True)
    dayofweek = models.SmallIntegerField('Day of week')
    week = models.CharField(maxlength=10, db_index=True)
    week_start = models.DateField(db_index=True)
    week_end = models.DateField(db_index=True)
    month = models.CharField(maxlength=10, db_index=True)
    month_start = models.DateField(db_index=True)
    month_end = models.DateField(db_index=True)
    quarter = models.CharField(maxlength=10, db_index=True)
    quarter_start = models.DateField(db_index=True)
    quarter_end = models.DateField(db_index=True)
    year = models.CharField(maxlength=10, db_index=True)
    year_start = models.DateField(db_index=True)
    year_end = models.DateField(db_index=True)

    class Admin:
        pass
        list_display = ('day', 'dayofweek', 'week', 'month', 'quarter', 'year',
          'week_start', 'month_start', 'quarter_start', 'year_start')
        fields = (
            (None, {'fields': ('day',
                               'dayofweek',
                               ('week','week_start','week_end'),
                               ('month','month_start','month_end'),
                               ('quarter','quarter_start','quarter_end'),
                               ('year','year_start','year_end'),
                               )}),
            )
        list_per_page = LIST_PER_PAGE

    class Meta:
        verbose_name = 'Dates'  # There will only be multiple dates...
        verbose_name_plural = 'Dates'  # There will only be multiple dates...


class Calendar(models.Model):
    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def currentvalue(self):
        ''' Returns the value of the calendar on the current day.'''
        v = 0.0
        curdate = date.today()
        curdatetime = datetime(curdate.year,curdate.month,curdate.day)
        for b in self.buckets.all():
            if curdatetime < b.startdate: return v
            v = b.value
        return v
    currentvalue.short_description = 'Current value'

    def setvalue(self, start, end, value, user=None):
      '''Update calendar buckets such that the calendar value is changed
      in the specified date range.
      The admin log is updated if a user is passed as argument.
      '''
      # Create a change log entry, if a user is specified
      if user:
        global CALENDARID
        if not CALENDARID:
          CALENDARID = ContentType.objects.get_for_model(models.get_model('input','calendar')).id
        LogEntry.objects.log_action(
          user.id, CALENDARID, self.name, self.name, CHANGE,
          "Updated value to %s for the daterange %s to %s" % (value, start, end)
          )
      for b in self.buckets.all():
        if b.enddate <= start:
          # Earlier bucket
          continue
        elif b.startdate >= end:
          # Later bucket
          return
        elif b.startdate == start and b.enddate <= end:
          # Overwrite entire bucket
          b.value = value
          b.save()
        elif b.startdate >= start and b.enddate <= end:
          # Bucket became redundant
          b.delete()
        elif b.startdate < start and b.enddate > end:
          # New value is completely within this bucket
          Bucket(calendar=self, startdate=start, value=value).save()
          Bucket(calendar=self, startdate=end, value=b.value).save()
        elif b.startdate < start:
          # An existing bucket is partially before the new daterange
          Bucket(calendar=self, startdate=start, value=value).save()
        elif b.enddate > end:
          # An existing bucket is partially after the new daterange
          Bucket(calendar=self, startdate=b.startdate, value=value).save()
          b.startdate = end
          b.save()
      if self.buckets.count() == 0:
        # There wasn't any bucket yet...
        Bucket(calendar=self, startdate=start, value=value).save()
        Bucket(calendar=self, startdate=end, value=0).save()
      return

    def __str__(self): return self.name

    class Admin:
        list_display = ('name', 'description', 'category', 'subcategory', 'currentvalue', 'lastmodified')
        search_fields = ['name','description']
        list_filter = ['category', 'subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True


class Bucket(models.Model):
    # Database fields
    calendar = models.ForeignKey(Calendar, edit_inline=models.TABULAR, min_num_in_admin=5, num_extra_on_change=3, related_name='buckets')
    startdate = models.DateTimeField('start date', core=True)
    enddate = models.DateTimeField('end date', editable=False, null=True)
    value = models.DecimalField(max_digits=15, decimal_places=4, default=0.00)
    name = models.CharField(maxlength=60, null=True, blank=True)
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self):
        if self.name: return self.name
        return str(self.startdate)

    class Meta:
        ordering = ['startdate','name']

    @staticmethod
    def updateEndDate(instance):
        '''
        The user edits the start date of the calendar buckets.
        This method will automatically update the end date of a bucket to be equal to the start date of the next bucket.
        '''
        # Loop through all buckets
        prev = None
        for i in instance.calendar.buckets.all():
          if prev and i.startdate != prev.enddate:
            # Update the end date of the previous bucket to the start date of this one
            prev.enddate = i.startdate
            prev.save()
          prev = i
        if prev and prev.enddate != datetime(2030,12,31):
          # Update the last entry
          prev.enddate = datetime(2030,12,31)
          prev.save()


# This dispatcher function is called after a bucket is saved. There seems no cleaner way to do this, since
# the method calendar.buckets.all() is only up to date after the save...
# The method is not very efficient: called for every single bucket, and recursively triggers
# another save and dispatcher event
dispatcher.connect(Bucket.updateEndDate, signal=signals.post_save, sender=Bucket)
dispatcher.connect(Bucket.updateEndDate, signal=signals.post_delete, sender=Bucket)


class Location(models.Model):
    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children',
      raw_id_admin=True, help_text='Hierarchical parent')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return self.name

    class Admin:
        list_display = ('name', 'description', 'category', 'subcategory', 'owner', 'lastmodified')
        search_fields = ['name', 'description']
        list_filter = ['category', 'subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True


class Customer(models.Model):
    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children',
      raw_id_admin=True, help_text='Hierarchical parent')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return self.name

    class Admin:
        list_display = ('name', 'description', 'category', 'subcategory', 'owner', 'lastmodified')
        search_fields = ['name', 'description']
        list_filter = ['category', 'subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True


class Item(models.Model):
    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    operation = models.ForeignKey('Operation', null=True, blank=True, raw_id_admin=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children',
      raw_id_admin=True, help_text='Hierarchical parent')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return self.name

    class Admin:
        list_display = ('name', 'description', 'category', 'subcategory', 'operation', 'owner', 'lastmodified')
        search_fields = ['name', 'description']
        list_filter = ['category', 'subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True


class Operation(models.Model):
    # Types of operations
    operationtypes = (
      ('','FIXED_TIME'),
      ('OPERATION_FIXED_TIME','FIXED_TIME'),
      ('OPERATION_TIME_PER','TIME_PER'),
      ('OPERATION_ROUTING','ROUTING'),
      ('OPERATION_ALTERNATE','ALTERNATE'),
    )

    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    type = models.CharField(maxlength=20, null=True, blank=True, choices=operationtypes)
    fence = models.DecimalField('release fence', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="Operationplans within this time window from the current day are expected to be released to production ERP")
    pretime = models.DecimalField('pre-op time', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="A delay time to be respected as a soft constraint before starting the operation")
    posttime = models.DecimalField('post-op time', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="A delay time to be respected as a soft constraint after ending the operation")
    sizeminimum = models.DecimalField('size minimum', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="A minimum lotsize quantity for operationplans")
    sizemultiple = models.DecimalField('size multiple', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="A multiple quantity for operationplans")
    duration = models.DecimalField('duration', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="A fixed duration for the operation")
    duration_per = models.DecimalField('duration per unit', max_digits=15, decimal_places=4, null=True, blank=True,
      help_text="A variable duration for the operation")
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return self.name

    def save(self):
        if self.type == '' or self.type == 'OPERATION_FIXED_TIME':
          self.duration_per = None
        elif self.type != 'OPERATION_TIME_PER':
          self.duration = None
          self.duration_per = None
        # Call the real save() method
        super(Operation, self).save()

    class Admin:
        list_display = ('name', 'type', 'fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'lastmodified')
        search_fields = ['name',]
        list_per_page = LIST_PER_PAGE
        save_as = True
        fields = (
            (None, {'fields': ('name', 'type')}),
            ('Planning parameters', {
               'fields': ('fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'duration', 'duration_per'),
               'classes': 'collapse'
               }),
        )


class SubOperation(models.Model):
    ## Django bug: @todo
    ## We want to edit the sub-operations inline as part of the operation editor.
    ## But django doesn't like it...
    ## See Django ticket: http://code.djangoproject.com/ticket/1939
    #operation = models.ForeignKey(Operation, edit_inline=models.TABULAR,
    #  min_num_in_admin=3, num_extra_on_change=1, related_name='alfa')
    operation = models.ForeignKey(Operation, raw_id_admin=True, related_name='suboperations')
    priority = models.DecimalField(max_digits=5, decimal_places=4, default=1)
    suboperation = models.ForeignKey(Operation, raw_id_admin=True, related_name='beta', core=True)
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self):
        return self.operation.name \
          + "   " + str(self.priority) \
          + "   " + self.suboperation.name

    class Meta:
        ordering = ['operation','priority','suboperation']

    class Admin:
        list_display = ('operation','priority','suboperation')
        list_per_page = LIST_PER_PAGE


class Buffer(models.Model):
    # Types of buffers
    buffertypes = (
      ('','Default'),
      ('BUFFER_INFINITE','Infinite'),
      ('BUFFER_PROCURE','Procure'),
    )

    # Fields common to all buffer types
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    type = models.CharField(maxlength=20, null=True, blank=True, choices=buffertypes, default='')
    location = models.ForeignKey(Location, null=True, blank=True, db_index=True, raw_id_admin=True)
    item = models.ForeignKey(Item, db_index=True, raw_id_admin=True)
    onhand = models.DecimalField(max_digits=15, decimal_places=4, default=0.00, help_text='current inventory')
    minimum = models.ForeignKey('Calendar', null=True, blank=True, raw_id_admin=True,
      help_text='Calendar storing the safety stock profile')
    producing = models.ForeignKey('Operation', null=True, blank=True,
      related_name='used_producing', raw_id_admin=True,
      help_text='Operation to replenish the buffer')
    # Extra fields for procurement buffers
    leadtime = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, help_text='Leadtime for supplier of a procure buffer')
    min_inventory = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text='Inventory level that triggers replenishment of a procure buffer')
    max_inventory = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text='Inventory level to which a procure buffer is replenished')
    min_interval = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, help_text='Minimum time interval between replenishments of a procure buffer')
    max_interval = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, help_text='Maximum time interval between replenishments of a procure buffer')
    size_minimum = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text='Minimum size of replenishments of a procure buffer')
    size_multiple = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text='Replenishments of a procure buffer are a multiple of this quantity')
    size_maximum =  models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text='Maximum size of replenishments of a procure buffer')
    # Maintenance fields
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return self.name

    def save(self):
        if self.type == 'BUFFER_INFINITE' or self.type == 'BUFFER_PROCURE':
            # Handle irrelevant fields for infinite and procure buffers
            self.producing = None
        if self.type != 'BUFFER_PROCURE':
            # Handle irrelevant fields for non-procure buffers
            self.leadtime = None
            self.min_inventory = None
            self.max_inventory = None
            self.min_interval = None
            self.max_interval = None
            self.size_minimum = None
            self.size_multiple = None
            self.size_maximum = None
        super(Buffer, self).save()

    class Admin:
        fields = (
            (None,{
              'fields': (('name'), ('item', 'location'), 'description', ('category', 'subcategory'))}),
            ('Inventory', {
              'fields': ('onhand',)}),
            ('Planning parameters', {
              'fields': ('type','minimum','producing',)},),
            ('Planning parameters for procurement buffers', {
              'fields': ('leadtime','min_inventory','max_inventory','min_interval','max_interval','size_minimum','size_multiple','size_maximum'),
              'classes': 'collapse'},),
        )
        list_display = ('name', 'description', 'category', 'subcategory', 'location', 'item',
          'onhand', 'type', 'minimum', 'producing', 'lastmodified')
        search_fields = ['name', 'description']
        list_filter = ['category', 'subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True


class Resource(models.Model):
    # Types of resources
    resourcetypes = (
      ('','Default'),
      ('RESOURCE_INFINITE','Infinite'),
    )

    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    type = models.CharField(maxlength=20, null=True, blank=True, choices=resourcetypes, default='')
    maximum = models.ForeignKey('Calendar', null=True, blank=True,
      raw_id_admin=True, help_text='Calendar defining the available capacity')
    location = models.ForeignKey(Location, null=True, blank=True, db_index=True, raw_id_admin=True)
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    # Methods
    def __str__(self): return self.name

    def save(self):
        if self.type == 'RESOURCE_INFINITE':
            # These fields are not relevant for infinite resources
            self.maximum = None
        # Call the real save() method
        super(Resource, self).save()

    class Admin:
        list_display = ('name', 'description', 'category', 'subcategory', 'location',
          'type', 'maximum', 'lastmodified')
        search_fields = ['name', 'description']
        list_filter = ['category', 'subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True


class Flow(models.Model):
    # Types of flow
    flowtypes = (
      ('','Start'),
      ('FLOW_END','End'),
    )

    # Database fields
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True, related_name='flows')
    thebuffer = models.ForeignKey(Buffer, db_index=True, raw_id_admin=True, related_name='flows')
    type = models.CharField(maxlength=20, null=True, blank=True, choices=flowtypes,
      help_text='Consume/produce material at the start or the end of the operationplan',
      )
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='1.00')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self):
        return '%s - %s' % (self.operation.name, self.thebuffer.name)

    class Admin:
        save_as = True
        search_fields = ['operation', 'thebuffer']
        list_display = ('operation', 'thebuffer', 'type', 'quantity', 'lastmodified')
        # @todo we don't have a hyperlink any more to edit a flow...
        list_per_page = LIST_PER_PAGE
        list_display_links = ('operation', 'thebuffer')

    class Meta:
        unique_together = (('operation','thebuffer'),)


class Load(models.Model):
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True, related_name='loads')
    resource = models.ForeignKey(Resource, db_index=True, raw_id_admin=True, related_name='loads')
    usagefactor = models.DecimalField(max_digits=15, decimal_places=4, default='1.00')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self):
        return '%s - %s' % (self.operation.name, self.resource.name)

    class Admin:
        search_fields = ['operation', 'resource']
        list_display = ('operation', 'resource', 'usagefactor', 'lastmodified')
        list_per_page = LIST_PER_PAGE
        save_as = True

    class Meta:
        unique_together = (('operation','resource'),)


class OperationPlan(models.Model):
    identifier = models.IntegerField(primary_key=True,
      help_text='Unique identifier of an operationplan')
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='1.00')
    startdate = models.DateTimeField(help_text='Start date')
    enddate = models.DateTimeField(help_text='End date')
    locked = models.BooleanField(default=True, radio_admin=True, help_text='Prevent or allow changes')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    def __str__(self): return str(self.identifier)

    class Admin:
        save_as = True
        search_fields = ['operation']
        list_display = ('identifier', 'operation', 'startdate', 'enddate', 'quantity', 'locked', 'lastmodified')
        list_per_page = LIST_PER_PAGE
        date_hierarchy = 'startdate'


class Demand(models.Model):
    # The priorities defined here are for convenience only. Frepple accepts any number as priority.
    demandpriorities = (
      (1,'1 - high'),
      (2,'2 - normal'),
      (3,'3 - low')
    )

    # Delivery policies to plan the demand
    demandpolicies = (
      ('','late with multiple deliveries'),
      ('SINGLEDELIVERY','late with single delivery'),
      ('PLANSHORT', 'short with multiple deliveries'),
      ('PLANSHORT SINGLEDELIVERY', 'short with single delivery')
    )

    # Database fields
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, null=True, blank=True)
    category = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    subcategory = models.CharField(maxlength=20, null=True, blank=True, db_index=True)
    customer = models.ForeignKey(Customer, null=True, db_index=True, raw_id_admin=True)
    item = models.ForeignKey(Item, db_index=True, raw_id_admin=True)
    due = models.DateTimeField('due')
    operation = models.ForeignKey(Operation, null=True, blank=True,
      related_name='used_demand', raw_id_admin=True, help_text='Operation used to satisfy this demand')
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    priority = models.PositiveIntegerField(default=2, choices=demandpriorities, radio_admin=True)
    policy = models.CharField(maxlength=25, null=True, blank=True, choices=demandpolicies,
      help_text='Choose whether to plan the demand short or late, and with single or multiple deliveries allowed')
    owner = models.ForeignKey('self', null=True, blank=True, raw_id_admin=True,
      help_text='Hierarchical parent')
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False, db_index=True)

    # Convenience methods
    def __str__(self): return self.name

    class Admin:
        fields = (
            (None, {'fields': ('name', 'item', 'customer', 'description', 'category','subcategory', 'due', 'quantity', 'priority','owner')}),
            ('Planning parameters', {'fields': ('operation', 'policy', ), 'classes': 'collapse'}),
        )
        list_display = ('name', 'item', 'customer', 'description', 'category',
          'subcategory', 'due', 'operation', 'quantity', 'priority','owner', 'lastmodified')
        search_fields = ['name','customer','item','operation']
        date_hierarchy = 'due'
        list_filter = ['due','priority','category','subcategory']
        list_per_page = LIST_PER_PAGE
        save_as = True
