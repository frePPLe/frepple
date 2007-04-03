#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net

from django.conf.urls.defaults import *
import sys
import freppledb.output.views

urlpatterns = patterns('',
    (r'^execute/log', 'django.views.generic.simple.direct_to_template', {'template': 'execute/log.html'} ),
    (r'^execute/runfrepple', 'freppledb.execute.views.runfrepple'),
    (r'^execute/rundb', 'freppledb.execute.views.rundb'),
    (r'^execute/', 'freppledb.execute.views.execute'),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^buffer/$', freppledb.output.views.bufferreport.view),
    (r'^demand/$', freppledb.output.views.demandreport.view),
    (r'^path/$', freppledb.output.views.pathreport.view),
)

# Allows the standalone development server to serve the static pages.
# In a production environment you need to configure your web server to take care of
# these pages.
if 'runserver' in sys.argv:
  urlpatterns += patterns('',(r'static/(?P<path>.*)$', 'django.views.static.serve', 
       {'document_root': 'static', 'show_indexes': False}),
    )
