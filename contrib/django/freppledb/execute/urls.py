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

from django.conf.urls import patterns

import freppledb.execute.views

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = patterns(
  '',   # Prefix
  (r'^execute/$', freppledb.execute.views.TaskReport.as_view()),
  (r'^execute/logfrepple/$', freppledb.execute.views.logfile),
  (r'^execute/launch/(.+)/$', freppledb.execute.views.LaunchTask),
  (r'^execute/cancel/(.+)/$', freppledb.execute.views.CancelTask),
)
