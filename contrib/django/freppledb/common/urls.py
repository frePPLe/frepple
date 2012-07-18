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

import freppledb.common.views

urlpatterns = patterns('',

  # User preferences
  (r'^preferences/$', freppledb.common.views.preferences),

  # Model list reports, which override standard admin screens
  (r'^admin/auth/user/$', freppledb.common.views.UserList.as_view()),
  (r'^admin/auth/group/$', freppledb.common.views.GroupList.as_view()),

  (r'^admin/common/bucket/$', freppledb.common.views.BucketList.as_view()),
  (r'^admin/common/bucketdetail/$', freppledb.common.views.BucketDetailList.as_view()),
  (r'^admin/common/parameter/$', freppledb.common.views.ParameterList.as_view()),
  (r'^comments/([^/]+)/([^/]+)/([^/]+)/$', freppledb.common.views.Comments),
  (r'^admin/common/comment/$', freppledb.common.views.CommentList.as_view()),
  
  # RSS feed with recently changed objects
  # IMPORTANT NOTE: 
  # The RSS feed is not authenticated. Everybody can see the change list.
  # For security sensitive environments the RSS feed should be deactivated.
  (r'^rss/$', freppledb.common.views.RSSFeed()),
)
