#
# Copyright (C) 2010-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from datetime import timedelta, datetime
import base64
import ipaddress
import jwt
import re
import threading
from warnings import warn

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import info
from django.middleware.locale import LocaleMiddleware as DjangoLocaleMiddleware
from django.db import connection, connections, DEFAULT_DB_ALIAS, close_old_connections
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.http.response import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.utils import translation, timezone
from django.utils.translation import get_supported_language_variant
from django.utils.translation import gettext_lazy as _

from freppledb.common.auth import MultiDBBackend
from freppledb.common.models import Scenario, User

import logging

logger = logging.getLogger(__name__)


# A local thread variable to make the current request visible everywhere
_thread_locals = threading.local()


class HTTPAuthenticationMiddleware:
    def __init__(self, get_response):
        warn(
            "The HTTPAuthenticationMiddleware class is deprecated. You can safely remove it from your djangosettings.py file without loss of functionality",
            DeprecationWarning,
        )
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


class LocaleMiddleware(DjangoLocaleMiddleware):
    """
    This middleware extends the Django default locale middleware with the user
    preferences used in frePPLe:
    - language choice to override the browser default
    - user interface theme to be used
    """

    def process_request(self, request):
        if isinstance(request.user, AnonymousUser):
            # Anonymous users don't have preferences
            language = "auto"
            request.theme = settings.DEFAULT_THEME
            request.pagesize = settings.DEFAULT_PAGESIZE
        else:
            if "language" in request.GET:
                try:
                    language = get_supported_language_variant(request.GET["language"])
                except Exception:
                    language = request.user.language
            else:
                language = request.user.language
            if request.user.scenario_themes:
                request.theme = request.user.scenario_themes.get(
                    request.database, request.user.theme
                )
            else:
                request.theme = request.user.theme
            if not request.theme or request.theme not in settings.THEMES:
                request.theme = settings.DEFAULT_THEME
            request.pagesize = request.user.pagesize or settings.DEFAULT_PAGESIZE
        if language == "auto":
            language = translation.get_language_from_request(request)
        if translation.get_language() != language:
            translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        request.charset = settings.DEFAULT_CHARSET
        if request.GET.get("navbar", None):
            request.session["navbar"] = True

    def process_response(self, request, response):
        # Set a clickjacking protection x-frame-option header in the
        # response UNLESS one the following conditions applies:
        #  - a X-Frame-Options or Content-Security-Policy header is already populated
        #  - the view was marked xframe_options_exempt
        #  - a web token was used to authenticate the request
        # See https://docs.djangoproject.com/en/1.10/ref/clickjacking/#module-django.middleware.clickjacking
        # See https://en.wikipedia.org/wiki/Clickjacking
        if (
            not response.get("X-Frame-Options", None)
            and not response.get("Content-Security-Policy", None)
            and not getattr(response, "xframe_options_exempt", False)
            and not request.session.get("xframe_options_exempt", False)
        ):
            val = getattr(settings, "X_FRAME_OPTIONS", None)
            if val:
                response["X-Frame-Options"] = val
            val = getattr(settings, "CONTENT_SECURITY_POLICY", None)
            if val:
                response["Content-Security-Policy"] = val
        if request.is_secure:
            response["strict-transport-security"] = "max-age=864000"
        return response


def resetRequest(**kwargs):
    """
    Used as a request_finished signal handler.
    """
    setattr(_thread_locals, "request", None)


# Initialize the URL parsing middleware
for i in settings.DATABASES:
    settings.DATABASES[i]["regexp"] = re.compile("^/%s/" % i)


class MultiDBMiddleware:
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

    def __init__(self, get_response):
        # One-time initialisation
        self.get_response = get_response

    def __call__(self, request):
        # Make request information available throughout the application
        setattr(_thread_locals, "request", request)

        # Select scenario database
        request.prefix = ""
        db = DEFAULT_DB_ALIAS
        for i in settings.DATABASES:
            try:
                if settings.DATABASES[i]["regexp"].match(request.path):
                    request.prefix = "/%s" % i
                    request.path_info = request.path_info[len(request.prefix) :]
                    request.path = request.path[len(request.prefix) :]
                    db = i
            except Exception:
                pass

        # Authentication through the header
        auth_header = request.META.get("HTTP_AUTHORIZATION", None)
        webtoken = request.GET.get("webtoken", None)
        if auth_header or webtoken:
            try:
                if auth_header:
                    auth_header_split = auth_header.split()
                    authmethod = auth_header_split[0].lower()
                else:
                    authmethod = None
                if authmethod == "basic":
                    # Basic authentication
                    auth_header_split = (
                        base64.b64decode(auth_header_split[1])
                        .decode("iso-8859-1")
                        .split(":", 1)
                    )
                    user = authenticate(
                        username=auth_header_split[0], password=auth_header_split[1]
                    )
                    if user and user.is_active:
                        # Active user
                        login(request, user)
                        request.user = user
                elif authmethod == "bearer" or webtoken:
                    # JWT webtoken authentication
                    decoded = None
                    for secret in (
                        getattr(settings, "AUTH_SECRET_KEY", None),
                        settings.DATABASES[db].get(
                            "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
                        ),
                    ):
                        if secret:
                            try:
                                decoded = jwt.decode(
                                    webtoken or auth_header_split[1],
                                    secret,
                                    algorithms=["HS256"],
                                )
                            except jwt.exceptions.InvalidTokenError:
                                pass
                    if not decoded:
                        logger.error("Missing or invalid webtoken")
                        return HttpResponseForbidden("Missing or invalid webtoken")
                    try:
                        if "user" in decoded:
                            user = User.objects.get(username=decoded["user"])
                        elif "email" in decoded:
                            user = User.objects.get(email=decoded["email"])
                        else:
                            logger.error("No user or email in webtoken")
                            return HttpResponseForbidden("No user or email in webtoken")
                    except User.DoesNotExist:
                        if getattr(settings, "SOCIALACCOUNT_AUTO_SIGNUP", True):
                            # Autocreate new user
                            user_args = {}
                            if "user" in decoded:
                                user_args["username"] = decoded["user"]
                                user_args["email"] = decoded["user"]
                            if "email" in decoded:
                                user_args["email"] = decoded["email"]
                            user = User.objects.create_user(**user_args)
                            user.save(using=DEFAULT_DB_ALIAS)
                        else:
                            logger.error("Invalid user in webtoken")
                            messages.add_message(
                                request, messages.ERROR, "Unknown user"
                            )
                            return HttpResponseRedirect("/data/login/")
                    user.backend = settings.AUTHENTICATION_BACKENDS[0]
                    login(request, user)
                    request.user = user
                    if "navbar" in decoded:
                        request.session["navbar"] = decoded["navbar"] == True
                    if "branding" in decoded:
                        request.session["branding"] = decoded["branding"] == True
                    if decoded.get("xframe_options_exempt", True):
                        request.session["xframe_options_exempt"] = True
            except Exception as e:
                logger.warning(
                    "silently ignoring exception in http authentication: %s" % e
                )

        if not hasattr(request, "user"):
            if not connection.in_atomic_block:
                close_old_connections()
            request.user = auth.get_user(request)

        # Log out automatically after inactivity
        if (
            not request.user.is_anonymous
            and settings.SESSION_LOGOUT_IDLE_TIME
            and "freppledb.common.middleware.AutoLoginAsAdminUser"
            not in settings.MIDDLEWARE
        ):
            now = datetime.now()
            if "last_request" in request.session:
                idle_time = now - datetime.strptime(
                    request.session["last_request"], "%y-%m-%d %H:%M:%S"
                )
                if idle_time > timedelta(minutes=settings.SESSION_LOGOUT_IDLE_TIME):
                    logout(request)
                    info(
                        request,
                        _("Your session has expired. Please login again to continue."),
                    )
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return HttpResponse(
                            status=401,
                            content=_(
                                "Your session has expired. Please login again to continue."
                            ),
                        )
                    else:
                        return HttpResponseRedirect(request.path_info)
                else:
                    request.session["last_request"] = now.strftime("%y-%m-%d %H:%M:%S")
            else:
                request.session["last_request"] = now.strftime("%y-%m-%d %H:%M:%S")

        # Set the database for queries only here.
        # All statements before this MUST be executed on the default database.
        request.database = db

        # Keep last_login date up to date and start web service if needed.
        # The user object is ALWAYS on default database at this stage, and we save the last login
        # only in that database. It's lazily replicated to other databases when needed.
        if request.user.is_anonymous:
            allowed_scenarios = {DEFAULT_DB_ALIAS: None}
        else:
            state = getattr(request.user, "_state", None)
            if state.db == DEFAULT_DB_ALIAS:
                user_dflt = request.user
                if not user_dflt.databases and user_dflt.is_active:
                    user_dflt.databases = [DEFAULT_DB_ALIAS]
                    user_dflt.save(update_fields=["databases"])
            else:
                print("warning: ", request.user, state.db)
                user_dflt = User.objects.using(DEFAULT_DB_ALIAS).get(pk=request.user.pk)
            last_login = getattr(user_dflt, "last_login", None)
            now = timezone.now()
            if not last_login or now - last_login > timedelta(hours=1):
                user_dflt.last_login = now
                user_dflt.save(update_fields=["last_login"])
            allowed_scenarios = {i.name: i for i in user_dflt.scenarios}

            # Check scenario access
            request.scenario = allowed_scenarios.get(request.database, None)
            if not request.scenario and not request.user.is_anonymous:
                return HttpResponseNotFound("Scenario not in use, or access is denied")

            # Update user
            request.user.switchDatabase(request.database)

        # Request processing
        response = self.get_response(request)
        if not response.streaming:
            # Note: Streaming response get the request field cleared in the
            # request_finished signal handler
            setattr(_thread_locals, "request", None)
        return response


class AutoLoginAsAdminUser:
    """
    Automatically log on a user as admin user.
    This can be handy during development or for demo models.
    """

    def __init__(self, get_response):
        # One-time initialisation
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, "user"):
            request.user = auth.get_user(request)
        if not request.user.is_authenticated:
            try:
                user = User.objects.get(username="admin")
                user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, user)
            except User.DoesNotExist:
                pass
        return self.get_response(request)


class AllowedIpMiddleware:
    """
    Checks that the IP address of the request is allowed in the
    settings.ALLOWED_IPS variable.
    """

    def __init__(self, get_response):
        # One-time initialisation
        self.get_response = get_response
        self.allowed_ips = [
            ipaddress.ip_network(ip) for ip in getattr(settings, "ALLOWED_IPS", [])
        ]

    def __call__(self, request):
        if self.allowed_ips:
            address = ipaddress.ip_address(request.META["REMOTE_ADDR"])
            for ip in self.allowed_ips:
                if address in ip:
                    return self.get_response(request)
            return HttpResponseForbidden("<h1>Unauthorized access</h1>")
        return self.get_response(request)
