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

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings


class OperationPlan(models.Model):
  # Database fields
  id = models.IntegerField(_('identifier'), primary_key=True)
  operation = models.CharField(_('operation'), max_length=300, db_index=True, null=True)
  quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4, default='1.00')
  unavailable = models.DecimalField(_('unavailable'), max_digits=15, decimal_places=4, default='0.00')
  startdate = models.DateTimeField(_('startdate'), db_index=True)
  enddate = models.DateTimeField(_('enddate'), db_index=True)
  criticality = models.DecimalField(_('criticality'), max_digits=15, decimal_places=4, null=True)
  locked = models.BooleanField(_('locked'), default=True)
  owner = models.IntegerField(_('owner'), null=True, blank=True, db_index=True)

  def __str__(self):
    return "Operationplan %s" % self.id

  class Meta:
    db_table = 'out_operationplan'
    verbose_name = _('operationplan')
    verbose_name_plural = _('operationplans')


class Problem(models.Model):
  # Database fields
  entity = models.CharField(_('entity'), max_length=15, db_index=True)
  owner = models.CharField(_('owner'), max_length=300, db_index=True)
  #. Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=20, db_index=True)
  description = models.CharField(_('description'), max_length=1000)
  startdate = models.DateTimeField(_('start date'), db_index=True)
  enddate = models.DateTimeField(_('end date'), db_index=True)
  weight = models.DecimalField(_('weight'), max_digits=15, decimal_places=4)

  def __str__(self):
    return str(self.description)

  class Meta:
    db_table = 'out_problem'
    ordering = ['startdate']
    verbose_name = _('problem')
    verbose_name_plural = _('problems')


class Constraint(models.Model):
  # Database fields
  demand = models.CharField(_('demand'), max_length=300, db_index=True)
  entity = models.CharField(_('entity'), max_length=15, db_index=True)
  owner = models.CharField(_('owner'), max_length=300, db_index=True)
  #. Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=20, db_index=True)
  description = models.CharField(_('description'), max_length=1000)
  startdate = models.DateTimeField(_('start date'), db_index=True)
  enddate = models.DateTimeField(_('end date'), db_index=True)
  weight = models.DecimalField(_('weight'), max_digits=15, decimal_places=4)

  def __str__(self):
    return str(self.demand) + ' ' + str(self.description)

  class Meta:
    db_table = 'out_constraint'
    ordering = ['demand', 'startdate']
    verbose_name = _('constraint')
    verbose_name_plural = _('constraints')


class ResourceSummary(models.Model):
  theresource = models.CharField(_('resource'), max_length=300)
  startdate = models.DateTimeField(_('startdate'))
  available = models.DecimalField(_('available'), max_digits=15, decimal_places=4, null=True)
  unavailable = models.DecimalField(_('unavailable'), max_digits=15, decimal_places=4, null=True)
  setup = models.DecimalField(_('setup'), max_digits=15, decimal_places=4, null=True)
  load = models.DecimalField(_('load'), max_digits=15, decimal_places=4, null=True)
  free = models.DecimalField(_('free'), max_digits=15, decimal_places=4, null=True)

  class Meta:
    db_table = 'out_resourceplan'
    ordering = ['theresource', 'startdate']
    unique_together = (('theresource', 'startdate'),)
    verbose_name = 'resource summary'  # No need to translate these since only used internally
    verbose_name_plural = 'resource summaries'


class LoadPlan(models.Model):
  # Database fields
  theresource = models.CharField(_('resource'), max_length=300, db_index=True)
  quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4)
  startdate = models.DateTimeField(_('startdate'), db_index=True)
  enddate = models.DateTimeField(_('enddate'), db_index=True)
  operationplan = models.ForeignKey(OperationPlan, verbose_name=_('operationplan'), db_index=True, related_name='loadplans')
  setup = models.CharField(_('setup'), max_length=300, null=True)

  def __str__(self):
      return self.theresource + ' ' + str(self.startdate) + ' ' + str(self.enddate)

  class Meta:
    db_table = 'out_loadplan'
    ordering = ['theresource', 'startdate']
    verbose_name = _('loadplan')
    verbose_name_plural = _('loadplans')


class FlowPlan(models.Model):
  # Database fields
  thebuffer = models.CharField(_('buffer'), max_length=300, db_index=True)
  operationplan = models.ForeignKey(OperationPlan, verbose_name=_('operationplan'), db_index=True, related_name='flowplans')
  quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4)
  flowdate = models.DateTimeField(_('date'), db_index=True)
  onhand = models.DecimalField(_('onhand'), max_digits=15, decimal_places=4)

  def __str__(self):
    return self.thebuffer.name + str(self.flowdate)

  class Meta:
    db_table = 'out_flowplan'
    ordering = ['thebuffer', 'flowdate']
    verbose_name = _('flowplan')
    verbose_name_plural = _('flowplans')


class Demand(models.Model):
  # Database fields
  demand = models.CharField(_('demand'), max_length=300, db_index=True, null=True)
  item = models.CharField(_('item'), max_length=300, db_index=True, null=True)
  customer = models.CharField(_('customer'), max_length=300, db_index=True, null=True)
  due = models.DateTimeField(_('due'), db_index=True)
  quantity = models.DecimalField(_('demand quantity'), max_digits=15, decimal_places=4, default='0.00')
  planquantity = models.DecimalField(_('planned quantity'), max_digits=15, decimal_places=4, default='0.00', null=True)
  plandate = models.DateTimeField(_('planned date'), null=True, db_index=True)
  operationplan = models.IntegerField(_('operationplan'), null=True, db_index=True)

  def __str__(self):
    return self.demand.name

  class Meta:
    db_table = 'out_demand'
    ordering = ['id']
    verbose_name = _('demand')
    verbose_name_plural = _('demands')


class DemandPegging(models.Model):
  # Database fields
  demand = models.CharField(_('demand'), max_length=300, db_index=True)
  level = models.IntegerField(_('level'))
  operationplan = models.IntegerField(_('operationplan'), db_index=True)
  quantity = models.DecimalField(_('quantity'), max_digits=15, decimal_places=4, default='0.00')

  def __str__(self):
    return self.demand \
      + ' - ' + str(self.depth) + ' - ' + str(self.operationplan) \
      + ' - ' + self.quantity

  class Meta:
    db_table = 'out_demandpegging'
    ordering = ['id']
    verbose_name = _('demand pegging')
    verbose_name_plural = _('demand peggings')
