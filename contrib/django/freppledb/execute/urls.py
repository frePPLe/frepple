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

from django.conf.urls import patterns

import freppledb.execute.views

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = patterns('',
    (r'^execute/scenarios/$', 'freppledb.execute.views.scenarios'),
    (r'^execute/logfrepple/$', 'freppledb.execute.views.logfile'),
    (r'^execute/log/$', freppledb.execute.views.LogReport.as_view()),
    (r'^execute/runfrepple/$', 'freppledb.execute.views.runfrepple'),
    (r'^execute/cancelfrepple/$', 'freppledb.execute.views.cancelfrepple'),
    (r'^execute/progressfrepple/$', 'freppledb.execute.views.progressfrepple'),
    (r'^execute/erase/$', 'freppledb.execute.views.erase'),
    (r'^execute/create/$', 'freppledb.execute.views.create'),
    (r'^execute/fixture/$', 'freppledb.execute.views.fixture'),
    (r'^execute/', 'freppledb.execute.views.main'),
)
