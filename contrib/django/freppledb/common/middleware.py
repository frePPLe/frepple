#
# Copyright (C) 2010-2013 by frePPLe bvba
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

import re
import threading

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.middleware.locale import LocaleMiddleware as DjangoLocaleMiddleware
from django.utils import translation
from django.db import DEFAULT_DB_ALIAS
from django.http import Http404
from django.conf import settings

from freppledb.common.models import Scenario


# A local thread variable to make the current request visible everywhere
_thread_locals = threading.local()


class LocaleMiddleware(DjangoLocaleMiddleware):
  """
  This middleware extends the Django default locale middleware with the user
  preferences used in frePPLe:
    - language choice to override the browser default
    - user interface theme to be used
  """
  def process_request(self, request):
    setattr(_thread_locals, 'request', request)
    if isinstance(request.user, AnonymousUser):
      # Anonymous users don't have preferences
      language = 'auto'
      request.theme = settings.DEFAULT_THEME
      request.pagesize = settings.DEFAULT_PAGESIZE
    else:
      language = request.user.language
      request.theme = request.user.theme or settings.DEFAULT_THEME
      request.pagesize = request.user.pagesize or settings.DEFAULT_PAGESIZE
    if language == 'auto':
      language = translation.get_language_from_request(request)
    if translation.get_language() != language:
      translation.activate(language)
    request.LANGUAGE_CODE = translation.get_language()
    request.charset = settings.DEFAULT_CHARSET

  def process_exception(self, request, exception):
    setattr(_thread_locals, 'request', None)
    return None

  def process_response(self, request, response):
    setattr(_thread_locals, 'request', None)
    return response


# Initialize the URL parsing middleware
for i in settings.DATABASES:
  settings.DATABASES[i]['regexp'] = re.compile("^/%s/" % i)


class MultiDBMiddleware(object):
  """
  This middleware examines the URL of the incoming request, and determines the
  name of database to use.
  URLs starting with the name of a configured database will be executed on that
  database. Extra fields are set on the request to set the selected database.
  This prefix is then stripped from the path while processing the view.

  If the request has a user, the database of that user is also updated to
  point to the selected database.
  We update the fields:
    - _state.db: a bit of a hack for the django internal stuff
    - is_active
    - is_superuser
  """
  def process_request(self, request):
    request.user = auth.get_user(request)
    for i in Scenario.objects.all().only('name', 'status'):
      try:
        if settings.DATABASES[i.name]['regexp'].match(request.path) and i.name != DEFAULT_DB_ALIAS:
          if i.status != 'In use':
            raise Http404('Scenario not in use')
          request.prefix = '/%s' % i.name
          request.path_info = request.path_info[len(request.prefix):]
          request.path = request.path[len(request.prefix):]
          request.database = i.name
          if request.user and not request.user.is_anonymous():
            superuser = request.user.scenarios.get(i.name)
            if superuser != None:
              request.user._state.db = i.name
              request.user.is_superuser = superuser
            else:
              raise Http404('Access to this scenario is not allowed')
          return
      except Http404:
        raise
      except:
        pass
    request.prefix = ''
    request.database = DEFAULT_DB_ALIAS
    if request.user and not request.user.is_anonymous():
      superuser = request.user.scenarios.get(DEFAULT_DB_ALIAS)
      if superuser != None:
        request.user._state.db = DEFAULT_DB_ALIAS
        request.user.is_superuser = superuser
      else:
        raise Http404('Access to this scenario is not allowed')
