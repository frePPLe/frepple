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

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from utils.report import ListReport

kpilist = []

@staff_member_required
def main(request):
  '''
  This view implements the overview screen with all kpis.
  '''
  return direct_to_template(request,  template='output/kpi.html',
    extra_context={
      'title': _('Key performance indicators'),
      'reset_crumbs': True,
      } )


class KPILateDemand(ListReport):
  '''
  A list report to show the amount of lateness, grouped by demand category.
  '''
  template = 'output/kpilatedemand.html'
  title = _("Late demand by category")
  reset_crumbs = False
  basequeryset = LoadPlan.objects.extra(
    select={'operation':'out_operationplan.operation'},
    where=['out_operationplan.identifier = out_loadplan.operationplan'],
    tables=['out_operationplan'])
  rows = (
    ('resource', {
      'filter': FilterText(),
      'title': _('resource')
      }),
    # @todo Eagerly awaiting the Django queryset refactoring to be able to filter on the operation field.
    #('operation', {'filter': 'operation__icontains', 'title': _('operation')}),
    ('operation', {'sort': False, 'title': _('operation')}),
    ('startdatetime', {
      'title': _('startdate'),
      'filter': FilterDate(field='startdate'),
      }),
    ('enddatetime', {
      'title': _('enddate'),
      'filter': FilterDate(field='enddate'),
      }),
    ('quantity', {
      'title': _('quantity'),
      'filter': FilterNumber(),
      }),
    ('operationplan', {
      'filter': FilterText(),
      'title': _('operationplan')
      }),
    )