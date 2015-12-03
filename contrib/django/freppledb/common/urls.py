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

from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

import freppledb.common.views
import freppledb.common.serializers
import freppledb.common.dashboard

from freppledb.common.api.views import APIIndexView


# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = patterns(
  # Prefix
  '',

  # User preferences
  url(r'^preferences/$', freppledb.common.views.preferences, name="preferences"),

  # Horizon updates
  url(r'^horizon/$', freppledb.common.views.horizon, name="horizon"),

  # Dashboard widgets
  url(r'^widget/(.+)/', freppledb.common.dashboard.Dashboard.dispatch, name="dashboard"),

  # Model list reports, which override standard admin screens
  url(r'^data/auth/group/$', freppledb.common.views.GroupList.as_view(), name="admin:auth_group_changelist"),
  url(r'^data/common/user/$', freppledb.common.views.UserList.as_view(), name="admin:common_user_changelist"),
  url(r'^data/common/bucket/$', freppledb.common.views.BucketList.as_view(), name="admin:common_bucket_changelist"),
  url(r'^data/common/bucketdetail/$', freppledb.common.views.BucketDetailList.as_view(), name="admin:common_bucketdetail_changelist"),
  url(r'^data/common/parameter/$', freppledb.common.views.ParameterList.as_view(), name="admin:common_parameter_changelist"),
  url(r'^data/common/comment/$', freppledb.common.views.CommentList.as_view(), name="admin:common_comment_changelist"),

  # Special case of the next line for user password changes in the user edit screen
  (r'detail/common/user/(?P<id>.+)/password/$', RedirectView.as_view(url="/data/common/user/%(id)s/password/")),

  # Detail URL for an object, which internally redirects to the view for the last opened tab
  (r'^detail/([^/]+)/([^/]+)/(.+)/$', freppledb.common.views.detail),

  # REST API framework
  (r'^api/common/bucket/$', freppledb.common.serializers.BucketAPI.as_view()),
  (r'^api/common/bucketdetail/$', freppledb.common.serializers.BucketDetailAPI.as_view()),
  (r'^api/common/bucketdetail/$', freppledb.common.serializers.BucketDetailAPI.as_view()),
  (r'^api/common/parameter/$', freppledb.common.serializers.ParameterAPI.as_view()),
  (r'^api/common/comment/$', freppledb.common.serializers.CommentAPI.as_view()),

  (r'^api/common/bucket/(?P<pk>(.+))/$', freppledb.common.serializers.BucketdetailAPI.as_view()),
  (r'^api/common/bucketdetail/(?P<pk>(.+))/$', freppledb.common.serializers.BucketDetaildetailAPI.as_view()),
  (r'^api/common/parameter/(?P<pk>(.+))/$', freppledb.common.serializers.ParameterdetailAPI.as_view()),
  (r'^api/common/comment/(?P<pk>(.+))/$', freppledb.common.serializers.CommentdetailAPI.as_view()),
  (r'^api/$', APIIndexView),
)
