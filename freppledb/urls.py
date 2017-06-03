#
# Copyright (C) 2007-2013 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from importlib import import_module

from django.conf.urls import include, url
from django.conf import settings
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog

from freppledb.admin import data_site

urlpatterns = [

  # Redirect admin index page /data/ to /
  url(r'^data/$', RedirectView.as_view(url='/')),

  # Handle browser icon and robots.txt
  url(r'favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
  url(r'robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),

  ]

# Custom handlers for error pages.
handler404 = 'freppledb.common.views.handler404'
handler500 = 'freppledb.common.views.handler500'

# Adding urls for each installed application.
for app in settings.INSTALLED_APPS:
  try:
    mod = import_module('%s.urls' % app)
    if hasattr(mod, 'urlpatterns'):
      if getattr(mod, 'autodiscover', False):
        urlpatterns += mod.urlpatterns
  except ImportError as e:
    # Silently ignore if the missing module is called urls
    if 'urls' not in str(e):
      raise e

# Admin pages, and the Javascript i18n library.
# It needs to be added as the last item since the applications can
# hide/override some admin urls.
urlpatterns += [
  url(r'^data/', data_site.urls),
  url(r'^data/jsi18n/$', JavaScriptCatalog.as_view(packages=['django.conf', 'freppledb'])),
  url(r'^admin/jsi18n/$', JavaScriptCatalog.as_view(packages=['django.conf', 'freppledb'])),
  url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
  ]
