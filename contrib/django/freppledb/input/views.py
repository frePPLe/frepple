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


from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden
from django.core import serializers
from django.utils.simplejson.decoder import JSONDecoder

from freppledb.input.models import Buffer, Flow, Operation, Plan, Resource, Item

from datetime import date, datetime


class uploadjson:
  @staticmethod
  @staff_member_required
  def post(request):
    try:
      # Validate the upload form
      if request.method != 'POST':
        raise Exception('Only POST method allowed')

      # Validate uploaded file is present
      if len(request.FILES)!=1 or 'data' not in request.FILES or request.FILES['data']['content-type'] != 'application/json':
        raise Exception('Invalid uploaded data')

      # Parse the uploaded file
      for i in JSONDecoder().decode(request.FILES['data']['content']):
        try:
          entity = i['entity']
          if entity == 'resource.maximum':
            # CASE 1: The maximum calendar of a resource is being edited
            # a) Verify permissions
            if not request.user.has_perm('input.change_resource'):
              raise Exception('No permission to change resources')
            # b) Find the calendar
            res = Resource.objects.get(name = i['name'])
            if not res.maximum:
              raise Exception('Resource "%s" has no max calendar' % res.name)
            # c) Update the calendar
            start = datetime.strptime(i['startdate'],'%Y-%m-%d')
            end = datetime.strptime(i['enddate'],'%Y-%m-%d')
            res.maximum.setvalue(
              start,
              end,
              float(i['value']) / (end - start).days,
              user = request.user)
          else:
            raise Exception('Unknown editing action "%s"' % entity)
        except Exception, e:
          print 'error processing record %s' % e

      # Processing went fine...
      return HttpResponse("OK")

    except Exception, e:
      print 'Error processing uploaded data: %s %s' % (type(e),e)
      return HttpResponseForbidden('Error processing uploaded data: %s' % e)
