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


class ExecuteWidget(Widget):
    name = "execute"
    title = _("Execute")
    permissions = (("generate_plan", "Can generate plans"),)
    tooltip = _("Generate a constrained plan")
    asynchronous = False
    url = "/execute/"

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals

        return """<div style="text-align:center">
      <form method="post" action="%s/execute/launch/runplan/">
      <input type="hidden" name="csrfmiddlewaretoken" value="%s">
      <input type="hidden" name="plantype" value="1"/>
      <input type="hidden" name="constraint" value="15"/>
      <input class="btn btn-primary" type="submit" value="%s"/>
      </form></div>
      """ % (
            _thread_locals.request.prefix,
            get_token(_thread_locals.request),
            force_str(_("Create a plan")),
        )


Dashboard.register(ExecuteWidget)
