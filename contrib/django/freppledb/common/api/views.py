#
# Copyright (C) 2015-2017 by frePPLe bvba
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

from django.contrib.admin.views.decorators import staff_member_required
from django.db import DEFAULT_DB_ALIAS
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from rest_framework import generics
from rest_framework_bulk import ListBulkCreateUpdateDestroyAPIView, ListBulkCreateAPIView
from rest_framework import filters

@staff_member_required
@csrf_protect
def APIIndexView(request):
  return render_to_response('rest_framework/index.html', {
     'title': _('REST API Help'),
     },
    context_instance=RequestContext(request))


class frePPleListCreateAPIView(ListBulkCreateUpdateDestroyAPIView):
  '''
  Customized API view for the REST framework.:
     - support for request-specific scenario database
     - add 'title' to the context of the html view
  '''
  filter_backends = (filters.DjangoFilterBackend,)

  def get_queryset(self):

      return super(frePPleListCreateAPIView, self).get_queryset().using(self.request.database)

  def allow_bulk_destroy(self, qs, filtered):
    # Safety check to prevent deleting all records in the database table
    if qs.count() > filtered.count():
      return True
    # default checks if the qs was filtered
    # qs comes from self.get_queryset()
    # filtered comes from self.filter_queryset(qs)
    return False

class frePPleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
  '''
  Customized API view for the REST framework.
     - support for request-specific scenario database
     - add 'title' to the context of the html view
  '''
  def get_queryset(self):
    if self.request.database == 'default':
      return super(frePPleRetrieveUpdateDestroyAPIView,self).get_queryset()
    else:
      return super(frePPleRetrieveUpdateDestroyAPIView, self).get_queryset().using(self.request.database)
