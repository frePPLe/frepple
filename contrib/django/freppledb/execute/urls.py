#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

from django.conf.urls import patterns

import freppledb.execute.views

urlpatterns = patterns('',
    (r'^scenarios/$', 'freppledb.execute.views.scenarios'),
    (r'^logfrepple/$', 'freppledb.execute.views.logfile'),
    (r'^log/$', freppledb.execute.views.LogReport.as_view()),
    (r'^runfrepple/$', 'freppledb.execute.views.runfrepple'),
    (r'^erase/$', 'freppledb.execute.views.erase'),
    (r'^create/$', 'freppledb.execute.views.create'),
    (r'^fixture/$', 'freppledb.execute.views.fixture'),
    (r'^', 'freppledb.execute.views.main'),
)