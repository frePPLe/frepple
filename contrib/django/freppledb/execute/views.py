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
# email : jdetaeye@users.sourceforge.net


from django import template
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.http import Http404, HttpResponse, HttpResponseRedirect
import os, os.path

from freppledb.execute.create import erase_model, create_model

def execute(request):
    '''
    Main execution window.
    '''
    return render_to_response('execute/execute.html', context_instance=template.RequestContext(request))
execute = staff_member_required(never_cache(execute))

def rundb(request):
    '''
    Database execution button.
    '''
    # Decode form attributes
    try: action = request.POST['action']
    except KeyError: raise Http404

    # Execute appropriate action
    if action == 'erase':
      # Erase the database contents
      try:
        erase_model()
        request.user.message_set.create(message='Erased the database')
      except Exception, e:
        request.user.message_set.create(message='Failure during database erasing:%s' % e)

      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/execute.html')

    elif action == 'create':
      # Erase the database contents
      try:
        clusters = int(request.POST['clusters'])
        demands = int(request.POST['demands'])
        levels = int(request.POST['levels'])
      except KeyError:
        raise Http404
      except ValueError, e:
        request.user.message_set.create(message='Invalid input field' % e)
      else:
        # Execute
        try:
          create_model(clusters,demands,levels)
          request.user.message_set.create(message='Created sample model in the database')
        except Exception, e:
          request.user.message_set.create(message='Failure during sample model creation:%s' % e)

      # Show the main screen again
      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/execute.html')

    else:
      # No valid action found
      raise Http404

rundb = staff_member_required(never_cache(rundb))

def runfrepple(request):
    '''
    Frepple execution button.
    '''
    # Decode form attributes
    try: action = request.POST['action']
    except KeyError: raise Http404

    if action == 'run':
      # Run frepple
      try:
        # @todo running frepple as batch command here is not flexible and robust enough
        frepple = '/home/frepple/workspace/frepple/bin'
        os.environ['PATH'] = frepple + os.pathsep + os.environ['PATH']
        os.environ['FREPPLE_HOME'] = frepple
        os.environ['LD_LIBRARY_PATH'] = frepple
        os.chdir(os.path.normpath(os.path.join(frepple,'..','contrib','django','freppledb','execute')))
        print os.path.normpath(os.path.join(frepple,'..','contrib','django','freppledb','execute'))
        os.system('frepple commands.xml')
        request.user.message_set.create(message='Successfully ran frepple')
      except Exception, e:
        request.user.message_set.create(message='Failure when running frepple:%s' % e)
      # Redirect the page such that reposting the doc is prevented and refreshing the page doesn't give errors
      return HttpResponseRedirect('/execute/execute.html')

    else:
      # No valid action found
      raise Http404

runfrepple = staff_member_required(never_cache(runfrepple))
