from django.db import models
from datetime import date
import sys
from django.http import HttpRequest

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
    class Admin:
        list_display = ('name', 'description', 'currentvalue', 'lastmodified', 'modifiedby')
        search_fields = ['name','description']
        save_as = True

class Bucket(models.Model):
    calendar = models.ForeignKey(Calendar, edit_inline=models.TABULAR, num_in_admin=3, related_name='buckets')
    start = models.DateField('start date', core=True)
    name = models.CharField(maxlength=60, blank=True)
    value = models.FloatField(max_digits=10, decimal_places=2, default='0.00')
    def __str__(self):
        if self.name: return self.name
        return str(self.start)
    class Meta:
        ordering = ('start','name')

class Location(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children', raw_id_admin=True)
    def __str__(self):
        return self.name
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
    class Admin:
        list_display = ('name', 'fence', 'pretime', 'posttime', 'sizeminimum', 'sizemultiple', 'owner')
        save_as = True

class Buffer(models.Model):
    name = models.CharField(maxlength=60, primary_key=True)
    description = models.CharField(maxlength=200, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, db_index=True, raw_id_admin=True)
    item = models.ForeignKey(Item, db_index=True, raw_id_admin=True)
    onhand = models.FloatField(max_digits=10, decimal_places=2, default='0.00')
    minimum = models.ForeignKey('Calendar', null=True, blank=True, raw_id_admin=True)
    producing = models.ForeignKey('Operation', null=True, blank=True, related_name='used_producing', raw_id_admin=True)
    consuming = models.ForeignKey('Operation', null=True, blank=True, related_name='used_consuming', raw_id_admin=True)
    def __str__(self):
        return self.name
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
    class Admin:
        list_display = ('name', 'description', 'maximum', 'location')
        save_as = True

class Flow(models.Model):
    operation = models.ForeignKey(Operation, db_index=True, raw_id_admin=True)
    thebuffer = models.ForeignKey(Buffer, db_index=True, raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2, default='1.00')
    def __str__(self):
        return '%s - %s' % (self.operation.name, self.thebuffer.name) 
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
