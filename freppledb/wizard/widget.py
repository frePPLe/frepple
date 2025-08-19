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

from django.middleware.csrf import get_token
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str

from freppledb.common.dashboard import Dashboard, Widget


class WizardWidget(Widget):
    name = "wizard"
    title = _("Loading your first data")
    asynchronous = False
    size = "xl"

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals

        return """
        <div class="row pt-3 pb-3">
            <div class="col-auto mx-auto">
                <h1 class="heading wizard-heading fw-bold">Two ways to get started quickly</h1>
            </div>
        </div>
        <div class="row pb-3 gy-5" id="wizard">

            <div class="col-md-6">
                <div class="text-center">
                    <h2 class="heading wizard-heading">
                        <span class="fa-stack">
                            <i class="fa fa-circle-o fa-stack-2x"></i>
                            <strong class="fa-stack-1x">A</strong>
                        </span>
                    </h2>
                    <h1 class="heading wizard-heading">Start with one item</h1>
                    <div class="dropdown-center">
                        <button class="btn btn-primary btn-lg" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        QUICKSTART
                        </button>
                        <ul class="dropdown-menu bg-primary">
                        <li><a href="%s/wizard/quickstart/forecast/" class="btn btn-primary w-100">FORECAST</a></li>
                        <li><a href="%s/wizard/quickstart/production/" class="btn btn-primary w-100">PRODUCTION</a></li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="text-center">
                <h2 class="heading wizard-heading">
                    <span class="fa-stack">
                        <i class="fa fa-circle-o fa-stack-2x"></i>
                        <strong class="fa-stack-1x">B</strong>
                    </span>
                </h2>
                    <h1 class="heading wizard-heading">Upload more data</h1>
                    <div class="dropdown-center">
                        <button class="btn btn-primary btn-lg" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        UPLOAD
                        </button>
                        <ul class="dropdown-menu bg-primary">
                        <li><a class="btn btn-primary w-100" href="%s/wizard/load/forecast/">FORECAST</a></li>
                        <li><a class="btn btn-primary w-100" href="%s/wizard/load/production/">PRODUCTION</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>""" % (
            _thread_locals.request.prefix,
            _thread_locals.request.prefix,
            _thread_locals.request.prefix,
            _thread_locals.request.prefix,
        )


Dashboard.register(WizardWidget)
