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

from datetime import datetime

from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from freppledb.common.models import User, Parameter, Comment, Bucket, BucketDetail
from freppledb.common.adminforms import MultiDBModelAdmin, MultiDBTabularInline
from freppledb.admin import data_site


class MyUserAdmin(UserAdmin, MultiDBModelAdmin):
  '''
  This class is a frePPLe specific override of its standard
  Django base class.
  '''
  save_on_top = True

  change_user_password_template = 'auth/change_password.html'

  fieldsets = (
    (None, {'fields': ('username', 'password')}),
    # Translators: Translation included with Django
    (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    (_('Permissions in this scenario'), {'fields': ('is_active', 'is_superuser',
                                   'groups', 'user_permissions')}),
    (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
  )

  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:common_user_change", "permission": 'common.change_user'},
    {"name": 'comments', "label": _("comments"), "view": "admin:common_user_comment"},
    # Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:common_user_history"},
    ]

  def get_readonly_fields(self, request, obj=None):
    if obj:
      return self.readonly_fields + ('last_login', 'date_joined')
    return self.readonly_fields

  def has_delete_permission(self, request, obj=None):
    # Users can't be deleted. Just mark them as inactive instead
    return False

data_site.register(User, MyUserAdmin)


class MyGroupAdmin(MultiDBModelAdmin):
  # This class re-implements the GroupAdmin class from
  # django.contrib.auth.admin, but without the performance optimization
  # trick it uses. Our version of the Admin is slower (as it generates much
  # more database queries), but it works on frepple's multi-database setups.
  search_fields = ('name',)
  ordering = ('name',)
  filter_horizontal = ('permissions',)
  save_on_top = True
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:auth_group_change", "permission": 'auth.change_group'},
    {"name": 'comments', "label": _("comments"), "view": "admin:auth_group_comment"},
    # Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:auth_group_history"},
    ]
data_site.register(Group, MyGroupAdmin)


class ParameterForm(forms.ModelForm):
  class Meta:
    model = Parameter
    fields = ('name', 'value', 'description')

  def clean(self):
    cleaned_data = self.cleaned_data
    name = cleaned_data.get("name")
    value = cleaned_data.get("value")
    # Currentdate parameter must be a date+time value
    if name == "currentdate":
      try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
      except:
        self._errors["value"] = ErrorList([_("Invalid date: expecting YYYY-MM-DD HH:MM:SS")])
        del cleaned_data["value"]
    return cleaned_data


class Parameter_admin(MultiDBModelAdmin):
  model = Parameter
  save_on_top = True
  form = ParameterForm
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:common_parameter_change", "permission": 'common.change_parameter'},
    {"name": 'comments', "label": _("comments"), "view": "admin:common_parameter_comment"},
    # Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:common_parameter_history"},
    ]
data_site.register(Parameter, Parameter_admin)


class Comment_admin(MultiDBModelAdmin):
  model = Comment
  save_on_top = True
data_site.register(Comment, Comment_admin)


class BucketDetail_inline(MultiDBTabularInline):
  model = BucketDetail
  max_num = 10
  extra = 3
  exclude = ('source',)


class BucketDetail_admin(MultiDBModelAdmin):
  model = BucketDetail
  save_on_top = True
  exclude = ('source', 'id')
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:common_bucketdetail_change", "permission": 'common.change_bucketdetail'},
    {"name": 'comments', "label": _("comments"), "view": "admin:common_bucketdetail_comment"},
    # Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:common_bucketdetail_history"},
    ]
data_site.register(BucketDetail, BucketDetail_admin)


class Bucket_admin(MultiDBModelAdmin):
  model = Bucket
  save_on_top = True
  inlines = [ BucketDetail_inline, ]
  exclude = ('source',)
  tabs = [
    {"name": 'edit', "label": _("edit"), "view": "admin:common_bucket_change", "permission": 'common.change_bucket'},
    {"name": 'comments', "label": _("comments"), "view": "admin:common_bucket_comment"},
    # Translators: Translation included with Django
    {"name": 'history', "label": _("History"), "view": "admin:common_bucket_history"},
    ]
data_site.register(Bucket, Bucket_admin)
