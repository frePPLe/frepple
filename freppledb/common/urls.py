#
# Copyright (C) 2007-2017 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.urls import path, re_path
from django.views.generic.base import RedirectView

from freppledb import mode

# Automatically add these URLs when the application is installed
autodiscover = True

if mode == "WSGI":
    from . import views, serializers, dashboard
    from freppledb.common.api.router import rest_api_router

    from freppledb.common.api.views import APIIndexView
    from freppledb.common.registration.views import (
        ResetPasswordRequestView,
        PasswordResetConfirmView,
    )

    urlpatterns = [
        re_path(r"^uploads/(.+)$", views.uploads, name="uploads"),
        path("inbox/", views.inbox, name="inbox"),
        path("follow/", views.follow, name="follow"),
        path("", views.cockpit, name="cockpit"),
        path("preferences/", views.preferences, name="preferences"),
        path("horizon/", views.horizon, name="horizon"),
        path("settings/", views.saveSettings),
        re_path(
            r"^widget/(.+)/",
            dashboard.Dashboard.dispatch,
            name="dashboard",
        ),
        # Model list reports, which override standard admin screens
        path("data/login/", views.login),
        path(
            "data/auth/group/",
            views.GroupList.as_view(),
            name="auth_group_changelist",
        ),
        path(
            "data/common/user/",
            views.UserList.as_view(),
            name="common_user_changelist",
        ),
        path(
            "data/common/follower/",
            views.FollowerList.as_view(),
            name="common_follower_changelist",
        ),
        path(
            "data/common/bucket/",
            views.BucketList.as_view(),
            name="common_bucket_changelist",
        ),
        path(
            "data/common/bucketdetail/",
            views.BucketDetailList.as_view(),
            name="common_bucketdetail_changelist",
        ),
        path(
            "data/common/parameter/",
            views.ParameterList.as_view(),
            name="common_parameter_changelist",
        ),
        path(
            "data/common/attribute/",
            views.AttributeList.as_view(),
            name="common_attribute_changelist",
        ),
        path(
            "data/common/apikey/",
            views.APIKeyList.as_view(),
            name="common_apikey_changelist",
        ),
        path(
            "data/common/comment/",
            views.CommentList.as_view(),
            name="common_comment_changelist",
        ),
        # Special case of the next line for user password changes in the user edit screen
        path(
            "detail/common/user/<path:id>/password/",
            RedirectView.as_view(url="/data/common/user/%(id)s/password/"),
        ),
        # Detail URL for an object, which internally redirects to the view for the last opened tab
        re_path(r"^detail/([^/]+)/([^/]+)/(.+)/$", views.detail),
        path("api/", APIIndexView),
        path("apps/", views.AppsView.as_view(), name="apps"),
        path("about/", views.AboutView, name="about"),
        path("scenarios/", views.ScenarioView, name="scenarios"),
        # Forgotten password
        re_path(
            r"^reset_password_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
            PasswordResetConfirmView.as_view(),
            name="reset_password_confirm",
        ),
        path(
            "reset_password/",
            ResetPasswordRequestView.as_view(),
            name="reset_password",
        ),
    ]

    rest_api_router.register(
        "common", "bucket", serializers.BucketAPI, serializers.BucketdetailAPI
    )
    rest_api_router.register(
        "common",
        "bucketdetail",
        serializers.BucketDetailAPI,
        serializers.BucketDetaildetailAPI,
    )
    rest_api_router.register(
        "common",
        "parameter",
        serializers.ParameterAPI,
        serializers.ParameterdetailAPI,
    )
    rest_api_router.register(
        "common",
        "attribute",
        serializers.AttributeAPI,
        serializers.AttributedetailAPI,
    )
    rest_api_router.register(
        "common", "comment", serializers.CommentAPI, serializers.CommentdetailAPI
    )
