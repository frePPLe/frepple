#
# Copyright (C) 2007-2013 by frePPLe bv
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

import base64
import jwt
import time

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import DEFAULT_DB_ALIAS
from django.db.models import Q
from django.http import HttpResponse

from freppledb.common.models import User, Scenario

import logging

logger = logging.getLogger(__name__)


class MultiDBBackend(ModelBackend):
    """
    This customized authentication is based on the Django ModelBackend
    with the following extensions:
      - We allow a user to log in using either their user name or
        their email address.
      - Permissions are scenario-specific.

    This authentication backend relies on the MultiDBMiddleware class
    to assure that the user object refers to the correct database.
    """

    def authenticate(self, request, username=None, password=None):
        try:
            validate_email(username)
            # The user name looks like an email address
            user = User.objects.get(email__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user.
            # See django ticket #20760
            User().set_password(password)
        except (ValidationError, User.MultipleObjectsReturned):
            # The user name isn't an email address
            try:
                user = User.objects.get(username__iexact=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                User().set_password(password)
            except User.MultipleObjectsReturned:
                try:
                    user = User.objects.get(username__exact=username)
                    if user.check_password(password):
                        return user
                except User.DoesNotExist:
                    User().set_password(password)

    def _get_user_permissions(self, user_obj):
        return user_obj.user_permissions.all()

    def _get_group_permissions(self, user_obj):
        user_groups_field = User._meta.get_field("groups")
        user_groups_query = "group__%s" % user_groups_field.related_query_name()
        return Permission.objects.using(user_obj._state.db).filter(
            **{user_groups_query: user_obj}
        )

    def _get_permissions(self, user_obj, obj, from_name):
        """
        Returns the permissions of `user_obj` from `from_name`. `from_name` can
        be either "group" or "user" to return permissions from
        `_get_group_permissions` or `_get_user_permissions` respectively.
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        perm_cache_name = "_%s_perm_cache_%s" % (from_name, user_obj._state.db)
        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.using(user_obj._state.db).all()
            else:
                perms = getattr(self, "_get_%s_permissions" % from_name)(user_obj)
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(
                user_obj,
                perm_cache_name,
                set("%s.%s" % (ct, name) for ct, name in perms),
            )
        return getattr(user_obj, perm_cache_name)

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        if not hasattr(user_obj, "_perm_cache_%s" % user_obj._state.db):
            user_obj._perm_cache = self.get_user_permissions(user_obj)
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
        return user_obj._perm_cache

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None


def basicauthentication(allow_logged_in=True, realm="frepple"):
    """
    A decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    This code is inspired on and copied from this snippet:
      https://djangosnippets.org/snippets/243/
    """

    def view_decorator(view):
        def wrapper(request, *args, **kwargs):
            ok = False
            try:
                if allow_logged_in:
                    u = getattr(request, "user", None)
                    if u and u.is_authenticated:
                        ok = True
                if not ok:
                    auth_header = request.META.get("HTTP_AUTHORIZATION", None)
                    if auth_header:
                        # Missing the header
                        auth = auth_header.split()
                        if auth[0].lower() == "basic":
                            # Only basic authentication
                            auth = (
                                base64.b64decode(auth[1])
                                .decode("iso-8859-1")
                                .split(":", 1)
                            )
                            user = authenticate(username=auth[0], password=auth[1])
                            if user and user.is_active:
                                # Active user
                                request.api = (
                                    True  # TODO I think this is no longer used
                                )
                                login(request, user)
                                request.user = user
                                ok = True
            except Exception:
                # Everything going wrong in the above will get the 401-unauthorized
                # reply. Any exception is silently ignored.
                pass
            if ok:
                # All clear
                return view(request, *args, **kwargs)
            else:
                # Send a 401-unauthorized response with a header prompting for a
                # username and password.
                logger.error("Failed basic authentication on %s" % request.path)
                resp = HttpResponse(
                    "Missing or incorrect authorization header", status=401
                )
                resp["WWW-Authenticate"] = 'Basic realm="%s"' % realm
                return resp

        return wrapper

    return view_decorator


def getWebserviceAuthorization(database=DEFAULT_DB_ALIAS, secret=None, **kwargs):
    # Create authorization header for the web service
    payload = {}
    if not secret:
        secret = settings.DATABASES[database].get(
            "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
        )
    for key, value in kwargs.items():
        if key == "exp":
            payload["exp"] = round(time.time()) + value
        else:
            payload[key] = value
    token = jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )
    return token.decode("ascii") if not isinstance(token, str) else token
