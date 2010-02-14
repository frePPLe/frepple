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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.db.models import Count

from input.models import Plan
from output.models import Problem
from common.report import *


# These definitions are not used in the code, but are required to get the 
# right translations detected.
problem_definitions = {
  _('demand'): (_('overload'), _('underload')), 
  _('material'): (_('material excess'), _('material shortage')),
  _('capacity'): (_('excess'), _('short'), _('early'), _('late'), _('unplanned')),
  _('operation'): (_('precedence'), _('before fence'), _('before current')), 
  }


def getEntities():
  return tuple([ 
    (i['entity'], string_concat(_(i['entity']),":",i['id__count'])) 
    for i in Problem.objects.values('entity').annotate(Count('id')) 
    ])
    

def getNames():
  return tuple([ 
    (i['name'], string_concat(_(i['name']),":",i['id__count']))
    for i in Problem.objects.values('name').annotate(Count('id')) 
    ])
  
  
class Report(ListReport):
  '''
  A list report to show problems.
  '''
  template = 'output/problem.html'
  title = _("Problem Report")
  basequeryset = Problem.objects.all()
  model = Problem
  frozenColumns = 0
  editable = False
  rows = (
    ('entity', {
      'title': _('entity'),
      'filter': FilterChoice(choices=getEntities),
      }),
    ('name', {
      'title': _('name'),
      'filter': FilterChoice(choices=getNames),
      }),
    ('owner', {
      'title': _('owner'),
      'filter': FilterText(size=30),
      }),
    ('description', {
      'title': _('description'),
      'filter': FilterText(size=30),
      }),
    ('startdate', {
      'title': _('startdate'),
      'filter': FilterDate(),
      }),
    ('enddate', {
      'title': _('enddate'),
      'filter': FilterDate(),
      }),
    ('weight', {
      'title': _('weight'),
      'filter': FilterNumber(size=5, operator="lt"),
      }),
    )
