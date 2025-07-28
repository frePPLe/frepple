#
# Copyright (C) 2023 by frePPLe bv
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
from importlib import import_module
import json
import jwt
import logging
import os
import sys

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import DEFAULT_DB_ALIAS
from django.urls import re_path

from django.contrib.auth.models import AnonymousUser
from freppledb.common.models import User
from freppledb.common.utils import get_databases

from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import WebsocketConsumer
from channels.middleware import BaseMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware

from .urls import svcpatterns

# Assure frePPLe is found in the Python path.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")

logger = logging.getLogger(__name__)

serviceRegistry = {}

connected = set()


def registerService(key):
    def inner(func):
        if callable(func):
            serviceRegistry[key] = func
        else:
            logger.warning("Warning: Only functions can be registered as a service")
        return func

    return inner


# Adding urls for each installed application.
for app in settings.INSTALLED_APPS:
    try:
        mod = import_module("%s.services" % app)
    except ModuleNotFoundError as e:
        # Silently ignore if the missing module is called urls
        if "services" not in str(e):
            raise e


# class WebsocketService(WebsocketConsumer):
#     def connect(self):
#         self.user = self.scope["user"]
#         print("connecting", self.user)
#         connected.add(self)
#         self.accept()

#     def disconnect(self, close_code):
#         print("disconnecting")
#         connected.remove(self)
#         pass

#     def receive(self, text_data):
#         print("receive", text_data, self.scope)
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]

#         self.send(text_data=json.dumps({"message": message}))


class HTTPNotFound(AsyncHttpConsumer):
    async def handle(self, body):
        self.scope["response_headers"].append((b"Content-Type", b"text/plain"))
        await self.send_response(
            400, b"Not found", headers=self.scope["response_headers"]
        )


@database_sync_to_async
def get_user(username=None, email=None, password=None, database=DEFAULT_DB_ALIAS):
    try:
        if username:
            if password:
                return authenticate(username=username, password=password)
            else:
                return User.objects.using(database).get(username=username)
        elif email:
            return User.objects.using(database).get(email=email)
        else:
            return AnonymousUser()
    except Exception:
        return AnonymousUser()


class TokenMiddleware(BaseMiddleware):
    """
    - adds scenario database to the scope
    - add user to the scope if a JWT token is present
    """

    def __init__(self, app):
        self.database = os.environ.get("FREPPLE_DATABASE", DEFAULT_DB_ALIAS)
        super().__init__(app)

    async def __call__(self, scope, receive, send):
        scope["database"] = self.database
        try:
            if "headers" in scope:
                for h in scope["headers"]:
                    if h[0] == b"authorization":
                        auth = h[1].decode("ascii").split()
                        if auth[0].lower() == "bearer":
                            # JWT webtoken authentication
                            for secret in (
                                getattr(settings, "AUTH_SECRET_KEY", None),
                                get_databases()[self.database].get(
                                    "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
                                ),
                            ):
                                if secret:
                                    try:
                                        decoded = jwt.decode(
                                            auth[1],
                                            secret,
                                            algorithms=["HS256"],
                                        )
                                        if "user" in decoded:
                                            scope["user"] = await get_user(
                                                username=decoded["user"],
                                                database=scope["database"],
                                            )
                                        elif "email" in decoded:
                                            scope["user"] = await get_user(
                                                email=decoded["email"],
                                                database=scope["database"],
                                            )
                                    except jwt.exceptions.InvalidSignatureError:
                                        continue
                        elif auth[0].lower() == "basic":
                            # Basic authentication
                            args = (
                                base64.b64decode(auth[1])
                                .decode("iso-8859-1")
                                .split(":", 1)
                            )
                            scope["user"] = await get_user(
                                username=args[0],
                                password=args[1],
                                database=scope["database"],
                            )
        except Exception:
            pass
        return await super().__call__(scope, receive, send)


class AuthAndPermissionMiddleware(AuthMiddleware):
    """
    Populates user permissions.
    """

    async def __call__(self, scope, receive, send):
        usr = scope.get("user", None)
        if not usr:
            scope["user"] = AnonymousUser
        elif usr.is_authenticated and not usr.is_superuser:
            await database_sync_to_async(usr.get_all_permissions)()
        return await super().__call__(scope, receive, send)


class AuthenticatedMiddleware(BaseMiddleware):
    """
    Disallows any unauthenticated connection with the service.
    A django session or a JWT token are required.
    """

    async def __call__(self, scope, receive, send):
        scope["response_headers"] = [
            (b"Access-Control-Allow-Methods", b"GET, POST, OPTIONS"),
            (b"Server", b"frepple"),
            (b"Access-Control-Allow-Credentials", b"true"),
            (
                b"Access-Control-Allow-Headers",
                b"authorization, content-type, x-requested-with",
            ),
        ]
        for hdr in scope["headers"]:
            if hdr[0] == b"origin":
                scope["response_headers"].append(
                    (b"Access-Control-Allow-Origin", hdr[1])
                )
                break
        if scope["method"] == "OPTIONS":
            await send(
                {
                    "type": "http.response.start",
                    "status": 204,
                    "headers": scope["response_headers"],
                }
            )
            return await send(
                {
                    "type": "http.response.body",
                    "body": b"OK",
                    "more_body": False,
                }
            )
        if (
            "user" not in scope
            or not scope["user"].is_authenticated
            or not scope["user"].is_active
        ):
            scope["response_headers"].append((b"Content-Type", b"text/plain"))
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": scope["response_headers"],
                }
            )
            return await send(
                {
                    "type": "http.response.body",
                    "body": b"Unauthenticated",
                    "more_body": False,
                }
            )
        try:
            return await super().__call__(scope, receive, send)
        except Exception as e:
            print("Error:", e)
            scope["response_headers"].append((b"Content-Type", b"text/plain"))
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": scope["response_headers"],
                }
            )
            return await send(
                {
                    "type": "http.response.body",
                    "body": b"Server error",
                    "more_body": False,
                }
            )


application = ProtocolTypeRouter(
    {
        "http": CookieMiddleware(
            SessionMiddleware(
                TokenMiddleware(
                    AuthAndPermissionMiddleware(
                        AuthenticatedMiddleware(
                            URLRouter(
                                svcpatterns + [re_path(r".*", HTTPNotFound.as_asgi())]
                            )
                        )
                    )
                )
            )
        ),
        # "websocket": AllowedHostsOriginValidator(
        #     AuthenticatedMiddleware(AuthMiddlewareStack(
        #         URLRouter([re_path(r"ws/", WebsocketService.as_asgi())])
        #     ))
        # ),
    }
)
