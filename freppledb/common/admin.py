#
# Copyright (C) 2007-2013 by frePPLe bv
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

from django import forms
from django.db import DEFAULT_DB_ALIAS
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .models import Attribute, User, Parameter, Comment, Follower, Bucket, BucketDetail
from .adminforms import MultiDBUserCreationForm, MultiDBModelAdmin
from freppledb.admin import data_site
from freppledb.boot import getAttributes


@admin.register(User, site=data_site)
class MyUserAdmin(UserAdmin, MultiDBModelAdmin):
    save_on_top = True

    add_form = MultiDBUserCreationForm
    add_fieldsets = (
        (
            _("Personal info"),
            {"fields": ("username", "first_name", "last_name", "email")},
        ),
        (_("password"), {"fields": ("password1", "password2")}),
        (_("scenario access"), {"fields": ("scenarios",)}),
    )

    change_user_password_template = "auth/change_password.html"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "passwordlink",
                    "first_name",
                    "last_name",
                    "email",
                    "avatar",
                    "last_login",
                    "date_joined",
                )
            },
        ),
        (
            _("Permissions in this scenario"),
            {"fields": ("is_active", "is_superuser", "groups", "user_permissions")},
        ),
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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.database != DEFAULT_DB_ALIAS:
            # Copy the lastlogin field from the main scenario
            User.synchronize(user=object_id, database=request.database)
        return super().change_view(request, object_id, form_url, extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("last_login", "date_joined", "passwordlink")
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        # Admin user can't be deleted.
        return not obj or obj.username != "admin"


class MyGroupAdminForm(forms.ModelForm):
    """
    ModelForm that adds an additional multiple select field for managing
    the users in the group.
    """

    users = forms.ModelMultipleChoiceField(
        User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple("Users", False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            initial_users = self.instance.user_set.values_list("pk", flat=True)
            self.initial["users"] = initial_users

    def save(self, *args, **kwargs):
        kwargs["commit"] = True
        return super().save(*args, **kwargs)

    def save_m2m(self):
        self.instance.user_set.clear()
        self.instance.user_set.add(*self.cleaned_data["users"])


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
    form = MyGroupAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                ]
            },
        ),
        (
            _("permissions and users"),
            {"fields": ["permissions", "users"]},
        ),
    )
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
    fieldsets = (
        (
            None,
            {
                "fields": ["name", "description", "value"]
                + [a[0] for a in getAttributes(Parameter) if a[3]]
            },
        ),
    )
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
    fieldsets = (
        (
            None,
            {
                "fields": ["bucket", "name", "startdate", "enddate"]
                + [a[0] for a in getAttributes(BucketDetail) if a[3]]
                + ["source"]
            },
        ),
    )
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
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "description",
                    "level",
                ]
                + [a[0] for a in getAttributes(Bucket) if a[3]]
                + ["source"]
            },
        ),
    )
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


@admin.register(Attribute, site=data_site)
class Attribute_admin(MultiDBModelAdmin):
    model = Attribute
    save_on_top = True
    exclude = ("source",)
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:common_attribute_change",
            "permission": "common.change_attribute",
        },
        {
            "name": "messages",
            "label": _("messages"),
            "view": "admin:common_attribute_comment",
        },
    ]
