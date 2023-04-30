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

from importlib import import_module

from django.urls import include, re_path
from django.conf import settings
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog

from freppledb.admin import data_site

urlpatterns = [
    # Redirect admin index page /data/ to /
    re_path(r"^data/$", RedirectView.as_view(url="/")),
    # Handle browser icon and robots.txt
    re_path(r"favicon\.ico$", RedirectView.as_view(url="/static/favicon.ico")),
    re_path(r"robots\.txt$", RedirectView.as_view(url="/static/robots.txt")),
]
svcpatterns = []

# Custom handlers for error pages.
handler404 = "freppledb.common.views.handler404"
handler500 = "freppledb.common.views.handler500"

# Adding urls for each installed application.
for app in settings.INSTALLED_APPS:
    try:
        mod = import_module("%s.urls" % app)
        if getattr(mod, "autodiscover", False):
            if hasattr(mod, "urlpatterns"):
                urlpatterns += mod.urlpatterns
            if hasattr(mod, "svcpatterns"):
                svcpatterns += mod.svcpatterns
    except ImportError as e:
        # Silently ignore if the missing module is called urls
        if "urls" not in str(e):
            raise e

# Admin pages, and the Javascript i18n library.
# It needs to be added as the last item since the applications can
# hide/override some admin urls.
urlpatterns += [
    re_path(
        r"^data/jsi18n/$",
        JavaScriptCatalog.as_view(),
    ),
    re_path(
        r"^admin/jsi18n/$",
        JavaScriptCatalog.as_view(),
    ),
    re_path(r"^data/", data_site.urls),
    re_path(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
