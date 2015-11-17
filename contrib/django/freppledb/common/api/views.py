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
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from rest_framework import generics


@staff_member_required
@csrf_protect
def APIIndexView(request):
  return render_to_response('rest_framework/index.html', {
     'title': _('REST API Help'),
     },
    context_instance=RequestContext(request))


class frePPleListCreateAPIView(generics.ListCreateAPIView):
  '''
  Customized API view for the REST framework.:
     - support for request-specific scenario database
     - add 'title' to the context of the html view
  '''
  def get_queryset(self):
    return super(frePPleListCreateAPIView, self).get_queryset().using(self.request.database)


class frePPleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
  '''
  Customized API view for the REST framework.
     - support for request-specific scenario database
     - add 'title' to the context of the html view
  '''
  def get_queryset(self):
    return super(frePPleRetrieveUpdateDestroyAPIView, self).get_queryset().using(self.request.database)
