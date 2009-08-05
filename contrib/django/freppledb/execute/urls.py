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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.conf.urls.defaults import patterns

import execute.views

urlpatterns = patterns('',
    (r'^logfrepple/$', 'django.views.generic.simple.direct_to_template',
       {'template': 'execute/logfrepple.html',
        'extra_context': {'title': 'frePPLe log file'},
       }),
    (r'^log/$', 'common.report.view_report', {'report': execute.views.LogReport,}),
    (r'^runfrepple/$', 'execute.views.runfrepple'),
    (r'^erase/$', 'execute.views.erase'),
    (r'^create/$', 'execute.views.create'),
    (r'^fixture/$', 'execute.views.fixture'),
    (r'^', 'execute.views.main'),
)