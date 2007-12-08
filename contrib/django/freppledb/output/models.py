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

from django.utils.translation import ugettext_lazy as _
from django.db import models


class OperationPlan(models.Model):
    # Database fields
    identifier = models.IntegerField(_('identifier'), primary_key=True)
    demand = models.CharField(_('demand'), max_length=60, null=True, db_index=True)
    operation = models.CharField(_('operation'), max_length=60, db_index=True, null=True)
    quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4, default='1.00')
    startdatetime = models.DateTimeField(_('start datetime'), )
    enddatetime = models.DateTimeField(_('end datetime'), )
    startdate = models.DateField(_('start date'), db_index=True)
    enddate = models.DateField(_('end date'), db_index=True)
    locked = models.BooleanField(_('locked'), default=True, radio_admin=True)
    owner = models.IntegerField(_('owner'), null=True, blank=True, db_index=True)

    def __unicode__(self): return str(self.identifier)

    class Meta:
        db_table = 'out_operationplan'
        permissions = (("view_operationplan", "Can view operation plans"),)
        verbose_name = _('operationplan')
        verbose_name_plural = _('operationplans')


class Problem(models.Model):
    # Database fields
    entity = models.CharField(_('entity'), max_length=10, db_index=True)
    name = models.CharField(_('name'), max_length=20, db_index=True)
    description = models.CharField(_('description'), max_length=80)
    startdatetime = models.DateTimeField(_('start datetime'))
    enddatetime = models.DateTimeField(_('end datetime'))
    startdate = models.DateField(_('start date'), db_index=True)
    enddate = models.DateField(_('end date'), db_index=True)
    weight = models.DecimalField(_('weight'), max_digits=15, decimal_places=4)

    def __unicode__(self): return str(self.name)

    class Meta:
        db_table = 'out_problem'
        permissions = (("view_problem", "Can view problems"),)
        ordering = ['startdatetime']
        verbose_name = _('problem')
        verbose_name_plural = _('problems')


class LoadPlan(models.Model):
    # Database fields
    resource = models.CharField(_('resource'), max_length=60, db_index=True)
    quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4)
    startdatetime = models.DateTimeField(_('start datetime'))
    startdate = models.DateField(_('start date'), db_index=True)
    enddatetime = models.DateTimeField(_('end datetime'))
    enddate = models.DateField(_('end date'), db_index=True)
    operationplan = models.IntegerField(_('operationplan'), db_index=True)

    def __unicode__(self):
        return self.resource.name + ' ' + str(self.startdatetime) + ' ' + str(self.enddatetime)

    class Meta:
        db_table = 'out_loadplan'
        permissions = (("view_loadplans", "Can view load plans"),)
        ordering = ['resource','startdatetime']
        verbose_name = _('loadplan')
        verbose_name_plural = _('loadplans')


class FlowPlan(models.Model):
    # Database fields
    thebuffer = models.CharField(_('buffer'), max_length=60, db_index=True)
    operationplan = models.IntegerField(_('operationplan'), db_index=True)
    quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4)
    flowdatetime = models.DateTimeField(_('datetime'))
    flowdate = models.DateField(_('date'), db_index=True)
    onhand = models.DecimalField(_('onhand'), max_digits=15, decimal_places=4)

    def __unicode__(self):
        return self.thebuffer.name + str(self.flowdatetime)

    class Meta:
        db_table = 'out_flowplan'
        permissions = (("view_flowplans", "Can view flow plans"),)
        ordering = ['thebuffer','flowdatetime']
        verbose_name = _('flowplan')
        verbose_name_plural = _('flowplans')


class Demand(models.Model):
    # Database fields
    demand = models.CharField(_('demand'), max_length=60, db_index=True, null=True)
    item = models.CharField(_('item'), max_length=60, db_index=True, null=True)
    duedate = models.DateField(_('due date'))
    duedatetime = models.DateTimeField(_('due datetime'))
    quantity = models.DecimalField(_('demand quantity'), max_digits=15, decimal_places=4, default='0.00')
    planquantity = models.DecimalField(_('planned quantity'), max_digits=15, decimal_places=4, default='0.00', null=True)
    plandate = models.DateField(_('planned date'), null=True)
    plandatetime = models.DateTimeField(_('planned datetime'), null=True)
    operationplan = models.IntegerField(_('operationplan'), null=True, db_index=True)

    def __unicode__(self):
        return self.demand.name

    class Meta:
        db_table = 'out_demand'
        ordering = ['id']
        verbose_name = _('demand')
        verbose_name_plural = _('demands')


class DemandPegging(models.Model):
    # Database fields
    demand = models.CharField(_('demand'), max_length=60, db_index=True)
    depth = models.IntegerField(_('depth'))
    cons_operationplan = models.IntegerField(_('consuming operationplan'), db_index=True, null=True)
    cons_date = models.DateTimeField(_('consuming datetime'))
    prod_operationplan = models.IntegerField(_('producing operationplan'), db_index=True, null=True)
    prod_date = models.DateTimeField(_('producing datetime'))
    buffer = models.CharField(_('buffer'), max_length=60, db_index=True, null=True)
    quantity_demand = models.DecimalField(_('quantity demand'), max_digits=15, decimal_places=4, default='0.00')
    quantity_buffer = models.DecimalField(_('quantity buffer'), max_digits=15, decimal_places=4, default='0.00')
    pegged = models.BooleanField(_('pegged'), default=True, radio_admin=True)

    def __unicode__(self):
        return self.demand.name \
          + ' - ' + str(self.depth) + ' - ' + str(self.operationplan or 'None') \
          + ' - ' + self.buffer.name

    class Meta:
        db_table = 'out_demandpegging'
        ordering = ['id']
        verbose_name = _('demand pegging')
        verbose_name_plural = _('demand peggings')


class Forecast(models.Model):
    # Database fields
    forecast = models.CharField(_('forecast'), max_length=60, db_index=True)
    startdate = models.DateField(_('start date'), null=False)
    enddate = models.DateField(_('end date'), null=False)
    total = models.DecimalField(_('total quantity'), max_digits=15, decimal_places=4, default='0.00')
    net = models.DecimalField(_('net quantity'), max_digits=15, decimal_places=4, default='0.00')
    consumed = models.DecimalField(_('consumed quantity'), max_digits=15, decimal_places=4, default='0.00')

    def __unicode__(self):
        return self.forecast.name \
          + ' - ' + str(self.startdate) + ' - ' + str(self.enddate)

    class Meta:
        db_table = 'out_forecast'
        ordering = ['id']
        verbose_name = _('forecast plan')
        verbose_name_plural = _('forecast plans')
