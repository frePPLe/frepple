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
from freppledb.input.models import Operation, Demand

class OperationPlan(models.Model):
    identifier = models.IntegerField(primary_key=True)
    operation = models.ForeignKey(Operation, related_name='instances', db_index=True)
    quantity = models.FloatField(max_digits=10, decimal_places=2, default='1.00')
    start = models.DateTimeField()
    end = models.DateTimeField()
    owner = models.ForeignKey('self', null=True, blank=True, related_name='children')
    def __str__(self):
        return str(self.identifier) 
    class Admin:
        pass
    class Meta:
        permissions = (("view_operationplan", "Can view operation plans"),)

class Problem(models.Model):
    name = models.CharField(maxlength=20, db_index=True)
    description = models.CharField(maxlength=80)
    start = models.DateTimeField('start date', db_index=True)
    end = models.DateTimeField('end date', db_index=True)
    def __str__(self):
        return str(self.name) 
    class Admin:
        list_display = ('name', 'description', 'start', 'end')
        search_fields = ['description']
        date_hierarchy = 'start'
        list_filter = ['name','start']
    class Meta:
        permissions = (("view_problem", "Can view problems"),)

class ResourcePlan(models.Model):
    name = models.CharField(maxlength=20, db_index=True)
    def __str__(self):
        return str(self.name) 
    class Admin:
        pass
    class Meta:
        permissions = (("view_resourceplans", "Can view resource plans"),)

class BufferPlan(models.Model):
    name = models.CharField(maxlength=20, db_index=True)
    def __str__(self):
        return str(self.name) 
    class Admin:
        pass
    class Meta:
        permissions = (("view_bufferplan", "Can view buffer plans"),)

class DemandPlan(models.Model):
    name = models.CharField(maxlength=20, db_index=True)
    def __str__(self):
        return str(self.name) 
    class Admin:
        pass
    class Meta:
        permissions = (("view_demandplan", "Can view demand plans"),)
