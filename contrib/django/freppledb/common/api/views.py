#
# Copyright (C) 2015 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
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
