#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$


r'''
Django URL mapping file.
'''

import os.path

from django.conf.urls import patterns, include
from django.conf import settings
from django.views.generic.base import RedirectView
from django.utils.importlib import import_module

import freppledb.admin

urlpatterns = patterns('',
    # Root url redirects to the admin index page
    (r'^$', RedirectView.as_view(url='/admin/')),
    
    # Handle browser icon and robots.txt
    (r'favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),    
    (r'robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),    
)

# Adding urls for each installed application.
for app in settings.INSTALLED_APPS:
  try:
    mod = import_module('%s.urls' % app)
    if hasattr(mod, 'urlpatterns'):
      if getattr(mod, 'autodiscover', False):
        urlpatterns += mod.urlpatterns
  except ImportError:
    # Silently ignore 
    pass
    
# Admin pages, and the Javascript i18n library.
# It needs to be added as the last item since the applications can
# hide/override some admin urls.
urlpatterns += patterns('',
    (r'^admin/jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('django.conf','freppledb'),}),
    (r'^admin/', include(freppledb.admin.site.urls)),
)
