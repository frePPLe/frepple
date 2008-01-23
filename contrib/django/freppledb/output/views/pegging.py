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

from input.models import Plan
from output.models import DemandPegging
from utils.report import *


class Report(ListReport):
  '''
  A list report to show peggings.
  '''
  template = 'output/pegging.html'
  title = _("Pegging Report")
  reset_crumbs = False
  basequeryset = DemandPegging.objects.all()
  model = DemandPegging
  rows = (
    ('demand', {
      'filter': FilterText(size=15),
      'title': _('demand'),
      }),
    ('buffer', {
      'filter': FilterText(),
      'title': _('buffer'),
      }),
    ('depth', {
      'filter': FilterText(size=2),
      'title': _('depth'),
      }),
    ('cons_date', {
      'title': _('consuming date'),
      'filter': FilterDate(),
      }),
    ('prod_date', {
      'title': _('producing date'),
      'filter': FilterDate(),
      }),
    ('cons_operationplan', {'title': _('consuming operationplan')}),
    ('prod_operationplan', {'title': _('producing operationplan')}),
    ('quantity_demand', {
      'title': _('quantity demand'),
      'filter': FilterNumber(),
      }),
    ('quantity_buffer', {
      'title': _('quantity buffer'),
      'filter': FilterNumber(),
      }),
    ('pegged', {
      'title': _('pegged'),
      'filter': FilterBool(),
      }),
    )

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified
