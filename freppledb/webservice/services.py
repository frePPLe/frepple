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

from channels.generic.http import AsyncHttpConsumer
from .commands import WebService


class StopService(AsyncHttpConsumer):
    msgtemplate = """
        <!doctype html>
        <html lang="en">
            <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            </head>
            <body>%s</body>
        </html>
        """

    async def handle(self, body):
        self.scope["response_headers"].append((b"Content-Type", b"text/html"))
        if self.scope["method"] != "POST":
            return await self.send_response(
                401,
                (self.msgtemplate % "Only POST requests allowed").encode("utf-8"),
                headers=self.scope["response_headers"],
            )
        else:
            # TODO wait for lock?
            await self.send_response(
                404,
                (self.msgtemplate % "Shutting down").encode("utf-8"),
                headers=self.scope["response_headers"],
            )
            WebService.stop()


class PingService(AsyncHttpConsumer):
    async def handle(self, body):
        self.scope["response_headers"].append((b"Content-Type", b"text/plain"))
        await self.send_response(
            200,
            b"OK",
            headers=self.scope["response_headers"],
        )
