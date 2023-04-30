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

from importlib import import_module
import json
import logging
import os
import sys

from django.conf import settings
from django.urls import re_path

from channels.auth import AuthMiddlewareStack
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import WebsocketConsumer
from channels.middleware import BaseMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

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


class HttpService(AsyncHttpConsumer):
    async def handle(self, body):
        print("receiving ", body, self)
        await self.send_response(
            200,
            b"Your response bytes",
            headers=[
                (b"Content-Type", b"text/plain"),
            ],
        )


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
        await self.send_response(
            400, b"Not found", headers=[(b"Content-Type", b"text/plain")]
        )


class AuthenticatedMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if not scope["user"].is_authenticated:
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"Content-Type", b"text/plain")],
                }
            )
            return await send(
                {
                    "type": "http.response.body",
                    "body": b"Unauthenticated",
                    "more_body": False,
                }
            )
        return await super().__call__(scope, receive, send)


application = ProtocolTypeRouter(
    {
        "http": AuthMiddlewareStack(
            AuthenticatedMiddleware(
                URLRouter(svcpatterns + [re_path(r".*", HTTPNotFound.as_asgi())])
            )
        ),
        # "websocket": AllowedHostsOriginValidator(
        #     AuthenticatedMiddleware(AuthMiddlewareStack(
        #         URLRouter([re_path(r"ws/", WebsocketService.as_asgi())])
        #     ))
        # ),
    }
)
