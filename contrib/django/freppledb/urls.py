#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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

r'''
Django URL mapping file.
'''

from django.conf.urls import patterns, include
from django.conf import settings
from django.views.generic.base import RedirectView
from django.utils.importlib import import_module

import freppledb.admin

urlpatterns = patterns(
  # Prefix
  '',

  # Root url redirects to the admin index page
  (r'^$', RedirectView.as_view(url='/admin/')),

  # Handle browser icon and robots.txt
  (r'favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
  (r'robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
)

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
    if not 'urls' in str(e):
      raise e

# Admin pages, and the Javascript i18n library.
# It needs to be added as the last item since the applications can
# hide/override some admin urls.
urlpatterns += patterns(
  '',  # Prefix
  (r'^data/', include(freppledb.admin.data_site.urls)),
  (r'^admin/', include(freppledb.admin.admin_site.urls)),
  (r'^data/jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('django.conf', 'freppledb')}),
  (r'^admin/jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('django.conf', 'freppledb')}),
)
