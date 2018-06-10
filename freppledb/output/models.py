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


class Problem(models.Model):
  # Database fields
  entity = models.CharField(_('entity'), max_length=15, db_index=True)
  owner = models.CharField(_('owner'), max_length=300, db_index=True)
  #. Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=20, db_index=True)
  description = models.CharField(_('description'), max_length=1000)
  startdate = models.DateTimeField(_('start date'), db_index=True)
  enddate = models.DateTimeField(_('end date'), db_index=True)
  weight = models.DecimalField(_('weight'), max_digits=20, decimal_places=8)

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
  weight = models.DecimalField(_('weight'), max_digits=20, decimal_places=8)

  def __str__(self):
    return str(self.demand) + ' ' + str(self.description)

  class Meta:
    db_table = 'out_constraint'
    ordering = ['demand', 'startdate']
    verbose_name = _('constraint')
    verbose_name_plural = _('constraints')


class ResourceSummary(models.Model):
  resource = models.CharField(_('resource'), max_length=300)
  startdate = models.DateTimeField(_('startdate'))
  available = models.DecimalField(_('available'), max_digits=20, decimal_places=8, null=True)
  unavailable = models.DecimalField(_('unavailable'), max_digits=20, decimal_places=8, null=True)
  setup = models.DecimalField(_('setup'), max_digits=20, decimal_places=8, null=True)
  load = models.DecimalField(_('load'), max_digits=20, decimal_places=8, null=True)
  free = models.DecimalField(_('free'), max_digits=20, decimal_places=8, null=True)

  class Meta:
    db_table = 'out_resourceplan'
    ordering = ['resource', 'startdate']
    unique_together = (('resource', 'startdate'),)
    verbose_name = 'resource summary'  # No need to translate these since only used internally
    verbose_name_plural = 'resource summaries'
