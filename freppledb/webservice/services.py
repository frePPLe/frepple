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

import os
import signal

from channels.generic.http import AsyncHttpConsumer


class StopService(AsyncHttpConsumer):
    async def handle(self, body):
        if self.scope["method"] != "POST":
            await self.send_response(
                401,
                "Only POST requests allowed",
                headers=[
                    (b"Content-Type", b"text/html"),
                ],
            )
        else:
            # TODO wait for lock
            await self.send_response(
                404,
                "Shutting down",
                headers=[
                    (b"Content-Type", b"text/html"),
                ],
            )
            os.kill(os.getpid(), signal.CTRL_C_EVENT)


class ForcedStopService(AsyncHttpConsumer):
    async def handle(self, body):
        if self.scope["method"] != "POST":
            await self.send_response(
                401,
                "Only POST requests allowed",
                headers=[(b"Content-Type", b"text/html")],
            )
        else:
            await self.send_response(
                404,
                "Forced shutdown",
                headers=[
                    (b"Content-Type", b"text/html"),
                ],
            )
            os.kill(os.getpid(), signal.CTRL_C_EVENT)


from channels.exceptions import StopConsumer


class PingService(AsyncHttpConsumer):
    async def handle(self, body):
        await self.send_response(
            200,
            b"OK",
            headers=[
                (b"Content-Type", b"text/html"),
            ],
        )
