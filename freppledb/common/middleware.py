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

import jwt
import re
import threading

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser
from django.middleware.locale import LocaleMiddleware as DjangoLocaleMiddleware
from django.utils import translation
from django.db import DEFAULT_DB_ALIAS
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.http.response import HttpResponseForbidden

from freppledb.common.models import Scenario, User

import logging
logger = logging.getLogger(__name__)


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
    # Make request information available throughout the application
    setattr(_thread_locals, 'request', request)

    # Authentication through a web token.specified as an URL parameter
    # The token can be specified as a a URL argument or as a HTTP header
    # with this structure:
    #    Authorization: Bearer <token>  (see https://jwt.io/introduction/
    # The token must have a "user" and "exp" field in the payload.
    webtoken = request.GET.get('webtoken', None)
    if not webtoken:
      auth_header = request.META.get('HTTP_AUTHORIZATION', None)
      if auth_header:
        try:
          auth = auth_header.split()
          if auth[0].lower() == 'bearer':
            webtoken = auth[1]
        except:
          pass
    if webtoken:
      # Decode the web token
      try:
        decoded = jwt.decode(
          webtoken,
          settings.DATABASES[request.database].get('SECRET_WEBTOKEN_KEY', settings.SECRET_KEY),
          algorithms=['HS256']
          )
        user = User.objects.get(username=decoded['user'])
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, user)
        request.session['navbar'] = decoded.get('navbar', True)
        request.session['xframe_options_exempt'] = True
      except jwt.exceptions.InvalidTokenError as e:
        logger.error('Missing or incorrect webtoken: %s' % e)
        return HttpResponseForbidden("Missing or incorrect webtoken")

      language = request.user.language
      request.theme = request.user.theme or settings.DEFAULT_THEME
      request.pagesize = request.user.pagesize or settings.DEFAULT_PAGESIZE
    elif isinstance(request.user, AnonymousUser):
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
    # Set a clickjacking protection x-frame-option header in the
    # response UNLESS one the following conditions applies:
    #  - a x-trame-options header is already populated
    #  - the view was marked xframe_options_exempt
    #  - a web token was used to authenticate the request
    # See https://docs.djangoproject.com/en/1.10/ref/clickjacking/#module-django.middleware.clickjacking
    # See https://en.wikipedia.org/wiki/Clickjacking
    if not response.get('X-Frame-Options', None) \
      and not getattr(response, 'xframe_options_exempt', False) \
      and not request.session.get('xframe_options_exempt', False):
        response['X-Frame-Options'] = getattr(settings, 'X_FRAME_OPTIONS', 'SAMEORIGIN').upper()

    if not response.streaming:
      setattr(_thread_locals, 'request', None)
    # Note: Streaming response get the request field cleared in the
    # request_finished signal handler
    return response


def resetRequest(**kwargs):
  """
  Used as a request_finished signal handler.
  """
  setattr(_thread_locals, 'request', None)


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
    if not hasattr(request, 'user'):
      request.user = auth.get_user(request)
    if not hasattr(request.user, 'scenarios'):
      # A scenario list is not available on the request
      for i in settings.DATABASES:
        try:
          if settings.DATABASES[i]['regexp'].match(request.path):
            scenario = Scenario.objects.get(name=i)
            if scenario.status != 'In use':
              return HttpResponseNotFound('Scenario not in use')
            request.prefix = '/%s' % i
            request.path_info = request.path_info[len(request.prefix):]
            request.path = request.path[len(request.prefix):]
            request.database = i
            return
        except Exception:
          pass
      request.prefix = ''
      request.database = DEFAULT_DB_ALIAS
    else:
      # A list of scenarios is already available
      if request.user.is_anonymous():
        return
      default_scenario = None
      for i in request.user.scenarios:
        if i.name == DEFAULT_DB_ALIAS:
          default_scenario = i
        try:
          if settings.DATABASES[i.name]['regexp'].match(request.path):
            request.prefix = '/%s' % i.name
            request.path_info = request.path_info[len(request.prefix):]
            request.path = request.path[len(request.prefix):]
            request.database = i.name
            request.scenario = i
            request.user._state.db = i.name
            request.user.is_superuser = i.is_superuser
            return
        except:
          pass
      request.prefix = ''
      request.database = DEFAULT_DB_ALIAS
      if default_scenario:
        request.scenario = default_scenario
      else:
        request.scenario = Scenario(name=DEFAULT_DB_ALIAS)


class AutoLoginAsAdminUser(object):
  """
  Automatically log on a user as admin user.
  This can be handy during development or for demo models.
  """
  def process_request(self, request):
    if not hasattr(request, 'user'):
      request.user = auth.get_user(request)
    if not request.user.is_authenticated():
      try:
        user = User.objects.get(username="admin")
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, user)
        request.user.scenarios = []
        for db in Scenario.objects.filter(Q(status='In use') | Q(name=DEFAULT_DB_ALIAS)):
          if not db.description:
            db.description = db.name
          if db.name == DEFAULT_DB_ALIAS:
            if request.user.is_active:
              db.is_superuser = request.user.is_superuser
              request.user.scenarios.append(db)
          else:
            try:
              user2 = User.objects.using(db.name).get(username=request.user.username)
              if user2.is_active:
                db.is_superuser = user2.is_superuser
                request.user.scenarios.append(db)
            except:
              # Silently ignore errors. Eg user doesn't exist in scenario
              pass
      except User.DoesNotExist:
        pass
