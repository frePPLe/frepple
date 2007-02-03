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
from datetime import date
import sys
from django.http import HttpRequest
from datetime import datetime 

dateformat = '%Y-%m-%dT%H:%M:%S'

# @todo testing code: a simple logging decorator
def logger(f, name=None):
    # Closure to remember our name and function objects
    if name is None:
        name = f.func_name
    def wrapped(*args, **kwargs):
        print "Calling", name, args, kwargs
        result = f(*args, **kwargs)
        print "Called", name, args, kwargs, "returned", repr(result)
        return result
    wrapped.__doc__ = f.__doc__
    return wrapped

class Plan(models.Model):
    name = models.CharField(maxlength=60)
    description = models.CharField(maxlength=60, blank=True)
    current = models.DateTimeField('current date')
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<CURRENT>%s</CURRENT>' %self.current.strftime(dateformat) ]
        if self.name: x.append('<NAME>%s</NAME>' % self.name)
        if self.description: x.append('<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        return '\n'.join(x)        
    class Admin:
        list_display = ('name', 'description', 'current')
        search_fields = ['name', 'description']
    class Meta:
        verbose_name_plural = 'Plan'  # There will only be 1 plan...

def get_user():
    '''
    User information is not always readily available.
    Here we are looking into the interpreter stack to find the current request
    (if there is one) and pick up the user from there.
    '''
    i=1
    user = None
    while True:
        try:
            frame = sys._getframe(i)
        except ValueError: # Stack isn't this deep
            break
        if 'request' in frame.f_locals and issubclass(type(frame.f_locals['request']) , HttpRequest):
            user = frame.f_locals['request'].user
            del(frame)
            break
        del(frame)
        i += 1
    return user

class Calendar(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    lastmodified = models.DateTimeField('last modified', auto_now=True, editable=False)
    modifiedby = models.CharField('modified by', maxlength=30, blank=True, editable=False)
    def currentvalue(self):
        ''' Returns the value of the calendar on the current day '''
        v = 0.0
        cur = date.today()
        for b in self.buckets.all():
            if cur < b.start: return v
            v = b.value
        return v
    currentvalue.short_description = 'Current value'
    def save(self):
        self.modifiedby = get_user()
        super(Calendar, self).save() # Call the "real" save() method
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<CALENDAR NAME="%s">' % self.name ]
        if self.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        for b in self.buckets.all(): b.xml()
        x.append('</CALENDAR>')
        return '\n'.join(x)
    class Admin:
        list_display = ('name', 'description', 'currentvalue', 'lastmodified', 'modifiedby')
        search_fields = ['name','description']
        save_as = True

class Bucket(models.Model):
    calendar = models.ForeignKey(Calendar, edit_inline=models.TABULAR, num_in_admin=3, related_name='buckets')
    start = models.DateField('start date', core=True)
    name = models.CharField(maxlength=60, blank=True)
    value = models.FloatField(max_digits=10, decimal_places=2, default=0.00)
    def __str__(self):
        if self.name: return self.name
        return str(self.start)
    def xml(self):
        x = [ '<BUCKET START="%s" VALUE="%f">' % (self.start.strftime(dateformat), self.value) ]
        if self.name: x.append( '<NAME>%s</NAME>' % self.name)
        x.append('</BUCKET>')
        return '\n'.join(x)
    class Meta:
        ordering = ('start','name')

class Location(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children', raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<LOCATION NAME="%s">' % self.name ]
        if self.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        if self.owner: x.append( '<OWNER NAME="%s"/>' % self.owner)
        x.append('</LOCATION>')
        return '\n'.join(x)
    class Admin:
        list_display = ('name', 'description', 'owner')
        search_fields = ['name', 'description']
        save_as = True

class Customer(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children', raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<CUSTOMER NAME="%s">' % self.name ]
        if self.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        if self.owner: x.append( '<OWNER NAME="%s"/>' % self.owner)
        x.append('</CUSTOMER>')
        return '\n'.join(x)
    class Admin:
        list_display = ('name', 'description', 'owner')
        search_fields = ['name', 'description']
        save_as = True

class Item(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    operation = models.ForeignKey('Operation', null=True, blank=True, raw_id_admin=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children', raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<ITEM NAME="%s">' % self.name ]
        if self.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        if self.operation: x.append( '<OPERATION NAME="%s"/>' % self.operation)
        if self.owner: x.append( '<OWNER NAME="%s"/>' % self.owner)
        x.append('</ITEM>')
        return '\n'.join(x)
    class Admin:
        list_display = ('name', 'description', 'operation', 'owner')
        search_fields = ['name', 'description']
        save_as = True

class Operation(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    fence = models.FloatField('release fence', max_digits=10, decimal_places=2, null=True, blank=True)
    pretime = models.FloatField('pre-op time', max_digits=10, decimal_places=2, null=True, blank=True)
    posttime = models.FloatField('post-op time', max_digits=10, decimal_places=2, null=True, blank=True)
    sizeminimum = models.FloatField('size minimum', max_digits=10, decimal_places=2, null=True, blank=True)
    sizemultiple = models.FloatField('size multiple', max_digits=10, decimal_places=2, null=True, blank=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='suboperations', raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<OPERATION NAME="%s">' % self.name ]
        if self.fence: x.append( '<FENCE>%f</FENCE>' % self.fence)
        if self.pretime: x.append( '<PRETIME>%f</PRETIME>' % self.pretime)
        if self.posttime: x.append( '<POSTTIME>%f</POSTTIME>' % self.posttime)
        if self.pretime: x.append( '<PRETIME>%d</PRETIME>' % self.pretime)
        if self.sizeminimum: x.append( '<SIZE_MINIMUM>%d</SIZE_MINIMUM>' % self.sizeminimum)
        if self.sizemultiple: x.append( '<SIZE_MULTIPLE>%d</SIZE_MULTIPLE>' % self.sizemultiple)
        if self.owner: x.append( '<OWNER NAME="%s"/>' % self.owner)
        x.append('</OPERATION>')
        return '\n'.join(x)
    class Admin:
        list_display = ('name', 'fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'owner')
        save_as = True

class Buffer(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, db_index=True, raw_id_admin=True)
    item = models.ForeignKey(Item, db_index=True, raw_id_admin=True)
    onhand = models.FloatField(max_digits=10, decimal_places=2, default=0.00)
    minimum = models.ForeignKey('Calendar', null=True, blank=True, raw_id_admin=True)
    producing = models.ForeignKey('Operation', null=True, blank=True, related_name='used_producing', raw_id_admin=True)
    consuming = models.ForeignKey('Operation', null=True, blank=True, related_name='used_consuming', raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<BUFFER NAME="%s">' % self.name ]
        if self.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        if self.location: x.append( '<LOCATION NAME="%s" />' % self.location.name)
        if self.item: x.append( '<ITEM NAME="%s" />' % self.item.name)
        if self.onhand: x.append( '<ONHAND>%s</ONHAND>' % self.onhand)
        if self.minimum: x.append( '<MINIMUM NAME="%s" />' % self.minimum.name)
        if self.producing: x.append( '<PRODUCING NAME="%s" />' % self.producing.name)
        if self.consuming: x.append( '<CONSUMING NAME="%s" />' % self.consuming.name)
        x.append('</BUFFER>')
        return '\n'.join(x)
    class Admin:
        fields = (
            (None, {'fields': ('name', 'description', 'location', 'item')}),
            ('Inventory', {'fields': ('onhand',)}),
            ('Planning parameters', {'fields': ('minimum','producing','consuming',), 'classes': 'collapse'}),
        )
        #list_display = ('name', 'description', 'location', 'item', 'onhand', 'minimum', 'producing', 'consuming')
        list_display = ('name', 'description', 'location', 'item', 'minimum', 'producing', 'consuming')
        save_as = True

class Resource(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    maximum = models.ForeignKey('Calendar', null=True, blank=True, raw_id_admin=True)
    location = models.ForeignKey(Location, null=True, blank=True, db_index=True, raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<RESOURCE NAME="%s">' % self.name ]
        if self.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % self.description)
        if self.maximum: x.append( '<MAXIMUM NAME="%s" />' % self.maximum.name)
        if self.location: x.append( '<LOCATION NAME="%s" />' % self.location.name)
        x.append('</RESOURCE>')
        return '\n'.join(x)
    class Admin:
        list_display = ('name', 'description', 'maximum', 'location')
        save_as = True

class Flow(models.Model):
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True)
    thebuffer = models.ForeignKey(Buffer, db_index=True, raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2, default='1.00')
    def __str__(self):
        return '%s - %s' % (self.operation.name, self.thebuffer.name) 
    def xml(self):
        x = [ '<FLOW>', '<OPERATION NAME="%s"/>' % self.operation.name , '<BUFFER NAME="%s"/>' % self.thebuffer.name, '<QUANTITY>%s</QUANTITY>' % self.quantity, '</FLOW>']
        return '\n'.join(x)
    class Admin:
        save_as = True
        #list_display = ('operation', 'thebuffer', 'quantity')
        list_display = ('operation', 'thebuffer')
    class Meta:
        unique_together = (('operation','thebuffer'),)

class Load(models.Model):
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True)
    resource = models.ForeignKey(Resource, db_index=True, raw_id_admin=True)
    usagefactor = models.FloatField(max_digits=10, decimal_places=2, default='1.00')
    def __str__(self):
        return '%s - %s' % (self.operation.name, self.resource.name) 
    def xml(self):
        x = [ '<LOAD>', '<OPERATION NAME="%s" />' % self.operation.name , '<RESOURCE NAME="%s"/>' % self.resource.name, '<USAGE>%f<USAGE>' % self.usagefactor, '</LOAD>']
        return '\n'.join(x)
    class Admin:
        #list_display = ('operation', 'resource', 'usagefactor')
        list_display = ('operation', 'resource')
        save_as = True
    class Meta:
        unique_together = (('operation','resource'),)

class OperationPlan(models.Model):
    identifier = models.IntegerField(primary_key=True)
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2, default='1.00')
    start = models.DateTimeField()
    end = models.DateTimeField()
    locked = models.BooleanField(default=True, radio_admin=True)
    def __str__(self):
        return str(self.identifier) 
    def xml(self):
        x = [ '<OPERATION_PLAN ID="%d" OPERATION="%s" QUANTITY="%s">' % (self.identifier, self.operation.name, self.quantity) ]
        if self.start: x.append( '<START>%s</START>' % self.start.strftime(dateformat))
        if self.end: x.append( '<START>%s</START>' % self.end.strftime(dateformat))
        if self.locked: x.append( '<LOCKED>true</LOCKED>')
        x.append('</OPERATION_PLAN>')
        return '\n'.join(x)
    class Admin:
        save_as = True
        list_display = ('identifier', 'operation', 'start', 'end', 'quantity', 'locked')
        date_hierarchy = 'start'

class Demand(models.Model):
    demandpriorities = (
      (1,'1 - high'),
      (2,'2 - normal'),
      (3,'3 - low')
    )
    name = models.CharField(maxlength=60, primary_key=True)
    customer = models.ForeignKey(Customer, null=True, blank=True, db_index=True, raw_id_admin=True)
    item = models.ForeignKey(Item, db_index=True, raw_id_admin=True)
    due = models.DateField('due')
    operation = models.ForeignKey('Operation', null=True, blank=True, related_name='used_demand', raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2)
    priority = models.PositiveIntegerField(default=2, choices=demandpriorities, radio_admin=True)
    owner = models.ForeignKey('self', null=True, blank=True, raw_id_admin=True)
    def __str__(self):
        return self.name
    def xml(self):
        x = [ '<DEMAND NAME="%s" DUE="%s" QUANTITY="%s" PRIORITY="%d">' % (self.name, self.due.strftime(dateformat), self.quantity, self.priority) ]
        if self.item: x.append( '<ITEM NAME="%s" />' % self.item.name)
        if self.operation: x.append( '<OPERATION NAME="%s" />' % self.operation.name)
        if self.customer: x.append( '<CUSTOMER NAME="%s" />' % self.customer.name)
        if self.owner: x.append( '<OWNER NAME="%s" />' % self.owner.name)
        x.append('</DEMAND>')
        return '\n'.join(x)
    class Admin:
        fields = (
            (None, {'fields': ('name', 'item', 'customer', 'due', 'quantity', 'priority','owner')}),
            ('Planning parameters', {'fields': ('operation',), 'classes': 'collapse'}),
        )
        #list_display = ('name', 'item', 'customer', 'due', 'operation', 'quantity', 'priority','owner')
        list_display = ('name', 'item', 'customer', 'due', 'operation','priority','owner')
        search_fields = ['name','customer','item','operation']
        date_hierarchy = 'due'
        list_filter = ['due','priority']
        save_as = True
