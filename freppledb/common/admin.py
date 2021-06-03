#
# Copyright (C) 2007-2013 by frePPLe bv
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

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _

from .models import User, Parameter, Comment, Follower, Bucket, BucketDetail
from .adminforms import MultiDBUserCreationForm, MultiDBModelAdmin
from freppledb.admin import data_site


@admin.register(User, site=data_site)
class MyUserAdmin(UserAdmin, MultiDBModelAdmin):
    save_on_top = True

    add_form = MultiDBUserCreationForm
    add_fieldsets = (
        (
            _("Personal info"),
            {"fields": ("username", ("first_name", "last_name"), "email")},
        ),
        (_("password"), {"fields": ("password1", "password2")}),
        (_("scenario access"), {"fields": ("scenarios",)}),
    )

    change_user_password_template = "auth/change_password.html"
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "avatar")},
        ),
        (
            _("Permissions in this scenario"),
            {"fields": ("is_active", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:common_user_change",
            "permission": "common.change_user",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:common_user_comment",
        },
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("last_login", "date_joined")
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        # Users can't be deleted. Just mark them as inactive instead
        return False


@admin.register(Group, site=data_site)
class MyGroupAdmin(MultiDBModelAdmin):
    # This class re-implements the GroupAdmin class from
    # django.contrib.auth.admin, but without the performance optimization
    # trick it uses. Our version of the Admin is slower (as it generates much
    # more database queries), but it works on frepple's multi-database setups.
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)
    save_on_top = True
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:auth_group_change",
            "permission": "auth.change_group",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:auth_group_comment",
        },
    ]


@admin.register(Parameter, site=data_site)
class Parameter_admin(MultiDBModelAdmin):
    model = Parameter
    save_on_top = True
    exclude = ("source",)
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:common_parameter_change",
            "permission": "common.change_parameter",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:common_parameter_comment",
        },
    ]


@admin.register(Comment, site=data_site)
class Comment_admin(MultiDBModelAdmin):
    model = Comment
    save_on_top = True


@admin.register(Follower, site=data_site)
class Follower_admin(MultiDBModelAdmin):
    model = Follower
    exclude = ("user", "args")
    save_on_top = True


@admin.register(BucketDetail, site=data_site)
class BucketDetail_admin(MultiDBModelAdmin):
    model = BucketDetail
    save_on_top = True
    exclude = ("source", "id")
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:common_bucketdetail_change",
            "permission": "common.change_bucketdetail",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:common_bucketdetail_comment",
        },
    ]


@admin.register(Bucket, site=data_site)
class Bucket_admin(MultiDBModelAdmin):
    model = Bucket
    save_on_top = True
    exclude = ("source",)
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:common_bucket_change",
            "permission": "common.change_bucket",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:common_bucket_comment",
        },
    ]
