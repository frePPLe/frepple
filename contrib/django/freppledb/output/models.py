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


class OperationPlan(models.Model):
    # Database fields
    identifier = models.IntegerField(primary_key=True)
    demand = models.CharField(maxlength=60, null=True, db_index=True)
    operation = models.CharField(maxlength=60, db_index=True, null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='1.00')
    startdatetime = models.DateTimeField()
    enddatetime = models.DateTimeField()
    startdate = models.DateField(db_index=True)
    enddate = models.DateField(db_index=True)
    locked = models.BooleanField(default=True, radio_admin=True)
    owner = models.IntegerField(null=True, blank=True, db_index=True)

    def __str__(self): return str(self.identifier)

    class Meta:
        db_table = 'out_operationplan'
        permissions = (("view_operationplan", "Can view operation plans"),)


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

    class Meta:
        db_table = 'out_problem'
        permissions = (("view_problem", "Can view problems"),)
        ordering = ['startdatetime']


class LoadPlan(models.Model):
    # Database fields
    resource = models.CharField(maxlength=60, db_index=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    startdatetime = models.DateTimeField('start')
    startdate = models.DateField('startdate', db_index=True)
    enddatetime = models.DateTimeField('end')
    enddate = models.DateField('enddate', db_index=True)
    operationplan = models.IntegerField(db_index=True)

    def __str__(self):
        return self.resource.name + ' ' + str(self.startdatetime) + ' ' + str(self.enddatetime)

    class Meta:
        db_table = 'out_loadplan'
        permissions = (("view_loadplans", "Can view load plans"),)
        ordering = ['resource','startdatetime']


class FlowPlan(models.Model):
    # Database fields
    thebuffer = models.CharField(maxlength=60, db_index=True)
    operation = models.CharField(maxlength=60, db_index=True)
    operationplan = models.IntegerField(db_index=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    flowdatetime = models.DateTimeField('datetime')
    flowdate = models.DateField('date', db_index=True)
    onhand = models.DecimalField(max_digits=15, decimal_places=4)

    def __str__(self):
        return self.thebuffer.name + str(self.flowdatetime)

    class Meta:
        db_table = 'out_flowplan'
        permissions = (("view_flowplans", "Can view flow plans"),)
        ordering = ['thebuffer','flowdatetime']


class Demand(models.Model):
    # Database fields
    demand = models.CharField(maxlength=60, db_index=True, null=True)
    duedate = models.DateField()
    duedatetime = models.DateTimeField()
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default='0.00')
    planquantity = models.DecimalField(max_digits=15, decimal_places=4, default='0.00', null=True)
    plandate = models.DateField(null=True)
    plandatetime = models.DateTimeField(null=True)
    operationplan = models.IntegerField(null=True, db_index=True)

    def __str__(self):
        return self.demand.name

    class Meta:
        db_table = 'out_demand'
        ordering = ['id']


class DemandPegging(models.Model):
    # Database fields
    demand = models.CharField(maxlength=60, db_index=True)
    depth = models.IntegerField()
    cons_operationplan = models.IntegerField(db_index=True, null=True)
    cons_date = models.DateTimeField()
    prod_operationplan = models.IntegerField(db_index=True, null=True)
    prod_date = models.DateTimeField()
    buffer = models.CharField(maxlength=60, db_index=True, null=True)
    quantity_demand = models.DecimalField(max_digits=15, decimal_places=4, default='0.00')
    quantity_buffer = models.DecimalField(max_digits=15, decimal_places=4, default='0.00')
    pegged = models.BooleanField(default=True, radio_admin=True)

    def __str__(self):
        return self.demand.name \
          + ' - ' + str(self.depth) + ' - ' + str(self.operationplan or 'None') \
          + ' - ' + self.buffer.name

    class Meta:
        db_table = 'out_demandpegging'
        ordering = ['id']