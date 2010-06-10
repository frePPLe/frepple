#
# Copyright (C) 2010 by Johan De Taeye
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


class LocaleMiddleware(DjangoLocaleMiddleware):
  """
  This middleware extends the Django default locale middleware:
    - Support for a user preference that overrides the browser default.
  """
  def process_request(self, request):
    if isinstance(request.user,AnonymousUser):
      language = 'auto'
    else:
      language = request.user.get_profile().language
    if language == 'auto':
      language = translation.get_language_from_request(request)
    translation.activate(language)
    request.LANGUAGE_CODE = translation.get_language()


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
    for i in settings.DATABASES:
      if settings.DATABASES[i]['regexp'].match(request.path) and i != DEFAULT_DB_ALIAS:
        request.prefix = '/%s' % i
        request.path_info = request.path_info[len(request.prefix):]
        request.path = request.path[len(request.prefix):]
        request.database = i
        return
    request.database = DEFAULT_DB_ALIAS
    request.prefix = ''
      