#
# Copyright (C) 2014 by frePPLe bv
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

from django.middleware.csrf import get_token
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str

from freppledb.common.dashboard import Dashboard, Widget


@Dashboard.register
class ExecuteWidget(Widget):
    name = "execute"
    title = _("Create a plan")
    permissions = (("auth.generate_plan", "Can generate plans"),)
    tooltip = _("Generate a constrained plan")
    asynchronous = False
    url = "/execute/#runplan"

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals
        from freppledb.execute.management.commands.runplan import Command

        return Command.getHTML(request or _thread_locals.request, widget=True)


@Dashboard.register
class ExecuteTaskGroupWidget(Widget):
    name = "executegroup"
    title = _("Group tasks")
    permissions = (("auth.generate_plan", "Can generate plans"),)
    tooltip = _("Run a sequence of tasks.")
    asynchronous = False
    url = "/execute/#scheduletasks"

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals
        from freppledb.execute.management.commands.scheduletasks import Command

        return Command.getHTML(request or _thread_locals.request, widget=True)
