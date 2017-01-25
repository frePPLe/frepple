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
from django.utils.translation import string_concat
from django.db.models import Count

from freppledb.output.models import Problem
from freppledb.common.report import GridReport, GridFieldText, GridFieldNumber, GridFieldDateTime, GridFieldInteger


def getEntities(request):
  return tuple([
    (i['entity'], string_concat(_(i['entity']), ":", i['id__count']))
    for i in Problem.objects.using(request.database).values('entity').annotate(Count('id')).order_by('entity')
    ])


def getNames(request):
  return tuple([
    (i['name'], string_concat(_(i['name']), ":", i['id__count']))
    for i in Problem.objects.using(request.database).values('name').annotate(Count('id')).order_by('name')
    ])


class Report(GridReport):
  '''
  A list report to show problems.
  '''
  template = 'output/problem.html'
  title = _("Problem report")
  basequeryset = Problem.objects  # TODO .extra(select={'forecast': "select name from forecast where out_problem.owner like forecast.name || ' - %%'",})
  model = Problem
  permissions = (("view_problem_report", "Can view problem report"),)
  frozenColumns = 0
  editable = False
  multiselect = False
  help_url = 'user-guide/user-interface/plan-analysis/problem-report.html'
  rows = (
    #. Translators: Translation included with Django
    GridFieldInteger('id', title=_('id'), key=True, editable=False, hidden=True),
    GridFieldText('entity', title=_('entity'), editable=False, align='center'),  # TODO choices=getEntities
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), editable=False, align='center'),  # TODO choices=getNames
    GridFieldText('owner', title=_('owner'), editable=False, extra='"formatter":probfmt'),
    GridFieldText('description', title=_('description'), editable=False, width=350),
    GridFieldDateTime('startdate', title=_('start date'), editable=False),
    GridFieldDateTime('enddate', title=_('end date'), editable=False),
    GridFieldNumber('weight', title=_('weight'), editable=False),
    )
