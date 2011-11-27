#
# Copyright (C) 2010-2011 by Johan De Taeye, frePPLe bvba
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

from freppledb.output.models import Constraint
from freppledb.common.report import GridReport, TextGridField, NumberGridField, DateTimeGridField


entities = (
 ('demand',_('demand')),
 ('material',_('material')),
 ('capacity',_('capacity')),
 ('operation',_('operation'))
 )

names = (
  ('overload',_('overload')),
  ('underload',_('underload')),
  ('material excess',_('material excess')),
  ('material shortage',_('material shortage')),
  ('excess',_('excess')),
  ('short',_('short')),
  ('early',_('early')),
  ('late',_('late')),
  ('unplanned',_('unplanned')),
  ('precedence',_('precedence')),
  ('before fence',_('before fence')),
  ('before current',_('before current'))
  )


def getEntities(request):
  return tuple([
    (i['entity'], string_concat(_(i['entity']),":",i['id__count']))
    for i in Constraint.objects.using(request.database).values('entity').annotate(Count('id')).order_by('entity')
    ])


def getNames(request):
  return tuple([
    (i['name'], string_concat(_(i['name']),":",i['id__count']))
    for i in Constraint.objects.using(request.database).values('name').annotate(Count('id')).order_by('name')
    ])


class Report(GridReport):
  '''
  A list report to show constraints.
  '''
  template = 'output/constraint.html'
  title = _("Constraint Report")
  basequeryset = Constraint.objects.extra(select={'forecast': "select name from forecast where out_constraint.demand like forecast.name || ' - %%'",})
  model = Constraint
  frozenColumns = 0
  editable = False
  rows = (
    TextGridField('demand', title=_('demand'), editable=False, formatter='demand'),
    TextGridField('entity', title=_('entity'), editable=False, width=80, align='center'), # choices=getEntities),  TODO
    TextGridField('name', title=_('name'), editable=False, width=100, align='center'),
    TextGridField('owner', title=_('owner'), editable=False, align='center'),
    TextGridField('description', title=_('description'), editable=False, width=250),
    DateTimeGridField('startdate', title=_('start date'), editable=False),
    DateTimeGridField('enddate', title=_('end date'), editable=False),
    NumberGridField('weight', title=_('weight'), editable=False),
    )
