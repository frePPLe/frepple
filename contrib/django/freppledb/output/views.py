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

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from freppledb.output.models import FlowPlan
from freppledb.input.models import Buffer
from django.template import RequestContext, loader

#@login_required
def buffer(request, type='data'):
  response = HttpResponse(mimetype = 'application/xml')
  c = RequestContext(request)
  c.update({ 
    # The select-related gives a 4x speedup, but unfortunately misses some flowplans
    # The inventory operations are not in the input_operation table and the database
    # joins fails for those flowplans.
    # @todo
    'buffers': Buffer.objects.select_related(depth=2).order_by('name'), 
    'flowplans': FlowPlan.objects.select_related(depth=2).order_by('thebuffer','date','-quantity'),
    'type': type,
    })      
  response.write(loader.get_template('buffer.xml').render(c))
  return response
       