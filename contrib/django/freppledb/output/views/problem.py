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
from output.models import Problem
from utils.report import *


class Report(ListReport):
  '''
  A list report to show problems.
  '''
  template = 'output/problem.html'
  title = _("Problem Report")
  basequeryset = Problem.objects.all()
  rows = (
    ('entity', {
      'title': _('entity'),
      'filter': FilterText(),
      }),
    ('name', {
      'title': _('name'),
      'filter': FilterText(operator='exact', ),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(size=30),
      }),
    ('startdatetime', {
      'title': _('startdate'),
      'filter': FilterDate(),
      }),
    ('enddatetime', {
      'title': _('enddate'),
      'filter': FilterDate(),
      }),
    ('weight', {
      'title': _('weight'),
      'filter': FilterNumber(size=5, operator="lt"),
      }),
    )

  @staticmethod
  def lastmodified():
    return Plan.objects.all()[0].lastmodified
