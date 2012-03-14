#
# Copyright (C) 2010-2012 by Johan De Taeye, frePPLe bvba
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

import re

from django.contrib.auth.models import AnonymousUser
from django.middleware.locale import LocaleMiddleware as DjangoLocaleMiddleware
from django.utils import translation
from django.db import DEFAULT_DB_ALIAS
from django.http import Http404
from django.conf import settings

from freppledb.execute.models import Scenario
from freppledb.common.models import Preferences


class LocaleMiddleware(DjangoLocaleMiddleware):
  """
  This middleware extends the Django default locale middleware with the user
  preferences used in frePPLe:
    - language choice to override the browser default
    - user interface theme to be used
  """
  def process_request(self, request):
    if isinstance(request.user, AnonymousUser):
      # Anonymous users don't have prefences      
      language = 'auto'
      request.theme = settings.DEFAULT_THEME
      request.pagesize = settings.DEFAULT_PAGESIZE
    else:
      prefs = request.user.get_profile()
      language = prefs.language
      request.theme = prefs.theme or settings.DEFAULT_THEME
      request.pagesize = prefs.pagesize or settings.DEFAULT_PAGESIZE
    if language == 'auto':
      language = translation.get_language_from_request(request)
    if translation.get_language() != language:
      translation.activate(language)
    request.LANGUAGE_CODE = translation.get_language()
    request.charset = settings.DEFAULT_CHARSET
 

# Initialize the URL parsing middleware  
for i in settings.DATABASES:
  settings.DATABASES[i]['regexp'] = re.compile("^/%s/" % i)


class DatabaseSelectionMiddleware(object):
  """
  This middleware examines the URL of the incoming request, and determines the
  name of database to use.
  URLs starting with the name of a configured database will be executed on that
  database. Extra fields are set on the request to set the selected database.
  This prefix is then stripped from the path while processing the view.
  """
  def process_request(self, request):
    for i in Scenario.objects.all():
      try:
        if settings.DATABASES[i.name]['regexp'].match(request.path) and i.name != DEFAULT_DB_ALIAS:
          if i.status != u'In use':
            raise Http404('Scenario not in use')
          request.prefix = '/%s' % i.name
          request.path_info = request.path_info[len(request.prefix):]
          request.path = request.path[len(request.prefix):]
          request.database = i.name
          return
      except:
        pass
    request.database = DEFAULT_DB_ALIAS
    request.prefix = ''
