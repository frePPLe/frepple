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

import os, os.path

from django.conf import settings
from django.core import management, serializers
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext_lazy as _

from execute.models import log
from utils.report import *


@staff_member_required
def main(request):
  '''
  This view implements the overview screen with all execution
  actions.
  '''
  return direct_to_template(request,  template='execute/execute.html',
        extra_context={'title': _('Execute'), 'reset_crumbs': True} )


@staff_member_required
@never_cache
def erase(request):
    '''
    Erase the contents of the database.
    '''
    # Allow only post
    if request.method != 'POST':
      request.user.message_set.create(message='Only POST method allowed')
      return HttpResponseRedirect('/execute/execute.html')

    # Erase the database contents
    try:
      management.call_command('frepple_flush', user=request.user.username)
      request.user.message_set.create(message='Erased the database')
    except Exception, e:
      request.user.message_set.create(message='Failure during database erasing:%s' % e)

    # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
    return HttpResponseRedirect('/execute/execute.html')


@staff_member_required
@never_cache
def create(request):
    '''
    Create a sample model in the database.
    '''
    # Allow only post
    if request.method != 'POST':
      request.user.message_set.create(message='Only POST method allowed')
      return HttpResponseRedirect('/execute/execute.html')

    # Validate the input form data
    try:
      clusters = int(request.POST['clusters'])
      demands = int(request.POST['demands'])
      fcstqty = int(request.POST['fcst'])
      levels = int(request.POST['levels'])
      resources = int(request.POST['rsrc_number'])
      resource_size = int(request.POST['rsrc_size'])
      procure_lt = int(request.POST['procure_lt'])
      components_per = int(request.POST['components_per'])
      components = int(request.POST['components'])
      deliver_lt = int(request.POST['deliver_lt'])
      if clusters>100000 or clusters<=0 \
        or fcstqty<0 or demands>=10000 or demands<0 \
        or levels<0 or levels>=50 \
        or resources>=1000 or resources<0 \
        or resource_size>100 or resource_size<0 \
        or deliver_lt<=0 or procure_lt<=0 \
        or components<0 or components>=100000 \
        or components_per<0:
          raise ValueError("Invalid parameters")
    except KeyError:
      raise Http404
    except ValueError, e:
      request.user.message_set.create(message='Invalid input field')
    else:
      # Execute
      try:
        management.call_command('frepple_flush', user=request.user.username)
        management.call_command('frepple_createmodel',
          verbosity=0, cluster=clusters, demand=demands,
          forecast_per_item=fcstqty, level=levels, resource=resources,
          resource_size=resource_size, components=components,
          components_per=components_per, deliver_lt=deliver_lt,
          procure_lt=procure_lt, user=request.user.username
          )
        request.user.message_set.create(message='Created sample model in the database')
      except Exception, e:
        request.user.message_set.create(message='Failure during sample model creation: %s' % e)

    # Show the main screen again
    # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
    return HttpResponseRedirect('/execute/')


@staff_member_required
@never_cache
def runfrepple(request):
    '''
    FrePPLe execution button.
    '''
    # Decode form input
    try: type = int(request.POST['type'])
    except: type = 7   # Default plan is fully constrained

    # Run frepple
    try:
      management.call_command('frepple_run', user=request.user.username, type=type)
      request.user.message_set.create(message='Successfully ran frepple')
    except Exception, e:
      request.user.message_set.create(message='Failure when running frepple: %s' % e)
    # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
    return HttpResponseRedirect('/execute/execute.html')


@staff_member_required
def fixture(request):
  """
  Load a dataset stored in a django fixture file.
  """

  # Validate the request
  if request.method != 'POST':
    request.user.message_set.create(message='Only POST method allowed')
    # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
    return HttpResponseRedirect('/execute/execute.html')

  # Decode the input data from the form
  try:
    fixture = request.POST['datafile']
    if fixture == '-': raise
  except:
    request.user.message_set.create(message='Missing dataset name')
    return HttpResponseRedirect('/execute/execute.html')

  # Load the fixture
  # The fixture loading code is unfornately such that no exceptions are
  # or any error status returned when it fails...
  try:
    log(category='LOAD', user=request.user.username,
      message='Start loading dataset "%s"' % fixture).save()
    management.call_command('loaddata', fixture, verbosity=0)
    request.user.message_set.create(message='Loaded dataset')
    log(category='LOAD', user=request.user.username,
      message='Finished loading dataset "%s"' % fixture).save()
  except Exception, e:
    request.user.message_set.create(message='Error while loading dataset: %s' % e)
    log(category='LOAD', user=request.user.username,
      message='Failed loading dataset "%s": %s' % (fixture,e)).save()
  return HttpResponseRedirect('/execute/execute.html')


class LogReport(ListReport):
  '''
  A list report to review the history of actions.
  '''
  template = 'execute/log.html'
  title = _('Command log')
  reset_crumbs = True
  basequeryset = log.objects.all()
  default_sort = '1d'
  rows = (
    ('lastmodified', {
      'title':_('last modified'),
      'filter': FilterDate(),
      }),
    ('category', {
      'filter': FilterText(),
      'title': _('category'),
      }),
    ('user', {
      'filter': FilterText(),
      'title': _('user'),
      }),
    ('message', {
      'filter': FilterText(size=30),
      'title':_('message'),
      }),
    )

