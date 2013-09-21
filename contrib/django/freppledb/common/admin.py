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

from datetime import datetime

from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

from freppledb.common.models import User, Parameter, Comment, Bucket, BucketDetail
from freppledb.common import MultiDBModelAdmin, MultiDBTabularInline
from freppledb.admin import admin_site


# Registering the User admin for our custom model.
# See http://stackoverflow.com/questions/16953302/django-custom-user-model-in-admin-relation-auth-user-does-not-exists
# to understand the need for this extra customization.
class MyUserCreationForm(UserCreationForm):
  def clean_username(self):
    username = self.cleaned_data["username"]
    try: User.objects.get(username=username)
    except User.DoesNotExist: return username
    raise forms.ValidationError(self.error_messages['duplicate_username'])

  class Meta(UserCreationForm.Meta):
    model = User

class MyUserAdmin(UserAdmin):
    save_on_top = True
    add_form = MyUserCreationForm

admin_site.register(Group, GroupAdmin)
admin_site.register(User, MyUserAdmin)


class ParameterForm(forms.ModelForm):
  class Meta:
    model = Parameter

  def clean(self):
    cleaned_data = self.cleaned_data
    name = cleaned_data.get("name")
    value = cleaned_data.get("value")
    # Currentdate parameter must be a date+time value
    if name == "currentdate":
      try: datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
      except:
        self._errors["value"] = ErrorList([_("Invalid date: expecting YYYY-MM-DD HH:MM:SS")])
        del cleaned_data["value"]
    return cleaned_data


class Parameter_admin(MultiDBModelAdmin):
  model = Parameter
  save_on_top = True
  form = ParameterForm
admin_site.register(Parameter, Parameter_admin)


class Comment_admin(MultiDBModelAdmin):
  model = Comment
  save_on_top = True
admin_site.register(Comment, Comment_admin)


class BucketDetail_inline(MultiDBTabularInline):
  model = BucketDetail
  max_num = 10
  extra = 3

class BucketDetail_admin(MultiDBModelAdmin):
  model = BucketDetail
  save_on_top = True
admin_site.register(BucketDetail, BucketDetail_admin)


class Bucket_admin(MultiDBModelAdmin):
  model = Bucket
  save_on_top = True
  inlines = [ BucketDetail_inline, ]
admin_site.register(Bucket, Bucket_admin)
