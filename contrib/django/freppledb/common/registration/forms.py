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
from django import forms


class PasswordResetRequestForm(forms.Form):
  email_or_username = forms.CharField(label=("Email Or Username"), max_length=254)


class SetPasswordForm(forms.Form):
  """
  A form that lets a user change set their password without entering the old
  password
  """
  error_messages = {
    'password_mismatch': ("The two password fields didn't match."),
    }
  new_password1 = forms.CharField(label=("New password"),
                                  widget=forms.PasswordInput)
  new_password2 = forms.CharField(label=("New password confirmation"),
                                  widget=forms.PasswordInput)

  def clean_new_password2(self):
    password1 = self.cleaned_data.get('new_password1')
    password2 = self.cleaned_data.get('new_password2')
    if password1 and password2:
      if password1 != password2:
        raise forms.ValidationError(
          self.error_messages['password_mismatch'],
          code='password_mismatch',
          )
    return password2
