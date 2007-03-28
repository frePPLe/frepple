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

class Dates(models.Model):
    date = models.DateField(primary_key=True)
    week = models.CharField(maxlength=10, db_index=True)
    week_start = models.DateField(db_index=True)
    month = models.CharField(maxlength=10, db_index=True)
    month_start = models.DateField(db_index=True)
    quarter = models.CharField(maxlength=10, db_index=True)
    quarter_start = models.DateField(db_index=True)
    year = models.CharField(maxlength=10, db_index=True)
    year_start = models.DateField(db_index=True)
    class Admin:
        pass
        list_display = ('date', 'week', 'month', 'quarter', 'year',
          'week_start', 'month_start', 'quarter_start', 'year_start')
        fields = (
            (None, {'fields': ('date',
                               ('week','week_start'),
                               ('month','month_start'),
                               ('quarter','quarter_start'),
                               ('year','year_start'),
                               )}),
            )
    class Meta:
        verbose_name = 'Dates'  # There will only be multiple dates...
        verbose_name_plural = 'Dates'  # There will only be multiple dates...

class OperationPlan(models.Model):
    identifier = models.IntegerField(primary_key=True)
    demand = models.ForeignKey(Demand, related_name='delivery', null=True, db_index=True, raw_id_admin=True)
    operation = models.ForeignKey(Operation, related_name='instances', null=True, db_index=True, raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2, default='1.00')
    startdatetime = models.DateTimeField()
    enddatetime = models.DateTimeField()
    startdate = models.DateField(db_index=True)
    enddate = models.DateField(db_index=True)
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children', raw_id_admin=True)
    def __str__(self):
        return str(self.identifier)
    class Admin:
        search_fields = ['operation']
        list_display = ('identifier', 'operation', 'startdate', 'enddate', 'quantity', 'owner')
        date_hierarchy = 'startdate'
    class Meta:
        permissions = (("view_operationplan", "Can view operation plans"),)

class Problem(models.Model):
    entity = models.CharField(maxlength=10, db_index=True)
    name = models.CharField(maxlength=20, db_index=True)
    description = models.CharField(maxlength=80)
    startdatetime = models.DateTimeField('start date')
    enddatetime = models.DateTimeField('end date')
    startdate = models.DateField(db_index=True)
    enddate = models.DateField(db_index=True)
    def __str__(self):
        return str(self.name)
    class Admin:
        list_display = ('entity', 'name', 'description', 'startdate', 'enddate')
        search_fields = ['description']
        date_hierarchy = 'startdate'
        list_filter = ['entity','name','startdate']
    class Meta:
        permissions = (("view_problem", "Can view problems"),)

class LoadPlan(models.Model):
    resource = models.ForeignKey(Resource, related_name='loadplans', db_index=True, raw_id_admin=True)
    operation = models.ForeignKey(Operation, related_name='loadplans', db_index=True, raw_id_admin=True)
    operationplan = models.ForeignKey(OperationPlan, related_name='loadplans', raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField()
    date = models.DateField(db_index=True)
    onhand = models.FloatField(max_digits=10, decimal_places=2)
    maximum = models.FloatField(max_digits=10, decimal_places=2)
    def __str__(self):
        return self.resource.name + ' ' + str(self.date)
    class Admin:
        list_display = ('resource', 'operation', 'quantity', 'date', 'onhand', 'maximum', 'operationplan')
    class Meta:
        permissions = (("view_loadplans", "Can view load plans"),)

class FlowPlan(models.Model):
    thebuffer = models.ForeignKey(Buffer, related_name='flowplans', db_index=True, raw_id_admin=True)
    operation = models.ForeignKey(Operation, related_name='flowplans', db_index=True, raw_id_admin=True)
    operationplan = models.ForeignKey(OperationPlan, related_name='flowplans', raw_id_admin=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField()
    date = models.DateField(db_index=True)
    onhand = models.FloatField(max_digits=10, decimal_places=2)
    def __str__(self):
        return self.thebuffer.name + str(self.date) 
    class Admin:
        list_display = ('thebuffer', 'operation', 'quantity', 'date', 'onhand', 'operationplan')
    class Meta:
        permissions = (("view_flowplans", "Can view flow plans"),)
