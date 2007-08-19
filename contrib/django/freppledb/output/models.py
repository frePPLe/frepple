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
from freppledb.input.models import Operation, Demand, Buffer, Resource

# This variable defines the number of records to show in the admin lists.
LIST_PER_PAGE = 100


class OperationPlan(models.Model):
    # Database fields
    identifier = models.IntegerField(primary_key=True)
    demand = models.ForeignKey(Demand, related_name='delivery', null=True, db_index=True, raw_id_admin=True)
    operation = models.ForeignKey(Operation, related_name='instances', null=True, db_index=True, raw_id_admin=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='1.00')
    startdatetime = models.DateTimeField()
    enddatetime = models.DateTimeField()
    startdate = models.DateField(db_index=True)
    enddate = models.DateField(db_index=True)
    locked = models.BooleanField(default=True, radio_admin=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children', raw_id_admin=True)

    def __str__(self): return str(self.identifier)

    class Admin:
        search_fields = ['operation']
        list_display = ('identifier', 'operation', 'startdatetime', 'enddatetime', 'quantity', 'locked', 'owner')
        list_per_page = LIST_PER_PAGE
        date_hierarchy = 'startdate'

    class Meta:
        db_table = 'out_operationplan'
        permissions = (("view_operationplan", "Can view operation plans"),)
        # Ordering is buggy :-(
        # Database sync expectes 'operation' and fails when it is set to 'operation_id'
        # Ordering requires 'operation_id' and fails when it is set to 'operation'
        #ordering = ['operation_id','startdatetime']


class Problem(models.Model):
    # Database fields
    entity = models.CharField(maxlength=10, db_index=True)
    name = models.CharField(maxlength=20, db_index=True)
    description = models.CharField(maxlength=80)
    startdatetime = models.DateTimeField('start date')
    enddatetime = models.DateTimeField('end date')
    startdate = models.DateField(db_index=True)
    enddate = models.DateField(db_index=True)
    weight = models.DecimalField(max_digits=15, decimal_places=4)

    def __str__(self): return str(self.name)

    class Admin:
        list_display = ('entity', 'name', 'description', 'startdate', 'enddate', 'weight')
        list_display_links = ('description',)
        search_fields = ['description']
        date_hierarchy = 'startdate'
        list_filter = ['entity','name','startdate']
        list_per_page = LIST_PER_PAGE

    class Meta:
        db_table = 'out_problem'
        permissions = (("view_problem", "Can view problems"),)
        ordering = ['startdatetime']


class LoadPlan(models.Model):
    # Database fields
    resource = models.ForeignKey(Resource, related_name='loadplans', db_index=True, raw_id_admin=True)
    operation = models.ForeignKey(Operation, related_name='loadplans', db_index=True, raw_id_admin=True)
    operationplan = models.ForeignKey(OperationPlan, related_name='loadplans', raw_id_admin=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    loaddatetime = models.DateTimeField('datetime')
    loaddate = models.DateField('date', db_index=True)
    onhand = models.DecimalField(max_digits=15, decimal_places=4)
    maximum = models.DecimalField(max_digits=15, decimal_places=4)

    def __str__(self):
        return self.resource.name + ' ' + str(self.loaddatetime)

    class Admin:
        list_display = ('resource', 'operation', 'quantity', 'loaddatetime', 'onhand', 'maximum', 'operationplan')
        list_per_page = LIST_PER_PAGE

    class Meta:
        db_table = 'out_loadplan'
        permissions = (("view_loadplans", "Can view load plans"),)
        # Ordering is buggy :-(
        # Database sync expectes 'resource' and fails when it is set to 'resource_id'
        # Ordering requires 'resource_id' and fails when it is set to 'resource'
        #ordering = ['resource_id','datetime']


class FlowPlan(models.Model):
    # Database fields
    thebuffer = models.ForeignKey(Buffer, related_name='flowplans', db_index=True, raw_id_admin=True)
    operation = models.ForeignKey(Operation, related_name='flowplans', db_index=True, raw_id_admin=True)
    operationplan = models.ForeignKey(OperationPlan, related_name='flowplans', raw_id_admin=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    flowdatetime = models.DateTimeField('datetime')
    flowdate = models.DateField('date', db_index=True)
    onhand = models.DecimalField(max_digits=15, decimal_places=4)

    def __str__(self):
        return self.thebuffer.name + str(self.flowdatetime)

    class Admin:
        list_display = ('thebuffer', 'operation', 'quantity', 'flowdatetime', 'onhand', 'operationplan')
        list_per_page = LIST_PER_PAGE

    class Meta:
        db_table = 'out_flowplan'
        permissions = (("view_flowplans", "Can view flow plans"),)
        # Ordering is buggy :-(
        # Database sync expectes 'thebuffer' and fails when it is set to 'thebuffer_id'
        # Ordering requires 'thebuffer_id' and fails when it is set to 'thebuffer'
        #ordering = ['thebuffer_id','datetime']


class DemandPegging(models.Model):
    # Database fields
    demand = models.ForeignKey(Demand, related_name='pegging', db_index=True, raw_id_admin=True)
    depth = models.IntegerField()
    operationplan = models.ForeignKey(OperationPlan, related_name='pegging', db_index=True, raw_id_admin=True, null=True)
    buffer = models.ForeignKey(Buffer, related_name='pegging', db_index=True, raw_id_admin=True, null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='0.00')
    factor = models.DecimalField(max_digits=15, decimal_places=4, default='1.00')
    pegged = models.BooleanField(default=True, radio_admin=True)
    pegdate = models.DateTimeField()

    def __str__(self):
        return self.demand.name \
          + ' - ' + str(self.depth) + ' - ' + str(self.operationplan or 'None') \
          + ' - ' + self.buffer.name

    class Admin:
        list_display = ('demand', 'depth', 'operationplan', 'buffer',
          'quantity', 'factor', 'pegdate', 'pegged')
        list_per_page = LIST_PER_PAGE

    class Meta:
        db_table = 'out_demandpegging'
        ordering = ['id']