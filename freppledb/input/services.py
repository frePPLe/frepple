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

from datetime import date, datetime
from dateutil.parser import parse
import json

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer

from freppledb.webservice.utils import lock


class OperationplanService(AsyncHttpConsumer):
    """
    Processes forecast update messages in these formats:

    """

    async def handle(self, body):
        errors = []
        try:
            import frepple

            if self.scope["method"] != "POST":
                self.scope["response_headers"].append((b"Content-Type", b"text/html"))
                await self.send_response(
                    401,
                    (self.msgtemplate % "Only POST requests allowed").encode(),
                    headers=self.scope["response_headers"],
                )
                return

            data = json.loads(body.decode("utf-8"))

            # Check permissions
            if not self.scope["user"].has_perm("input.change_operationplan"):
                self.scope["response_headers"].append((b"Content-Type", b"text/html"))
                await self.send_response(
                    403,
                    (self.msgtemplate % "Permission denied").encode(),
                    headers=self.scope["response_headers"],
                )
                return

            async with lock:
                print("receiving data ", data)

            self.scope["response_headers"].append((b"Content-Type", b"text/html"))
            await self.send_response(
                200,
                b"echo",
                headers=self.scope["response_headers"],
            )
        except Exception as e:
            print("exception " % e)
            await self.send_response(
                500,
                b"Error updating operationplans",
                headers=self.scope["response_headers"],
            )
