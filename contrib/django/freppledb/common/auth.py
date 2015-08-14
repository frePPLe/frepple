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

from django.contrib.auth.backends import ModelBackend
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from freppledb.common.models import User


class EmailBackend(ModelBackend):
  '''
  This customized authentication allows logging in using either
  the user name or the user email address.
  '''
  def authenticate(self, username=None, password=None):
    try:
      validate_email(username)
      # The user name looks like an email address
      user = User.objects.get(email=username)
      if user.check_password(password):
        return user
    except User.DoesNotExist:
      # Run the default password hasher once to reduce the timing
      # difference between an existing and a non-existing user.
      # See django ticket #20760
      User().set_password(password)
    except ValidationError:
      # The user name isn't an email address
      try:
        user = User.objects.get(username=username)
        if user.check_password(password):
          return user
      except User.DoesNotExist:
        # Run the default password hasher once to reduce the timing
        # difference between an existing and a non-existing user.
        # See django ticket #20760
        User().set_password(password)


    def get_user(self, user_id):
      '''
      This is identical to django.contrib.auth.backends.ModelBackend.get_user
      with a small performance optimization.
      '''
      try:
        return User.objects.get(pk=user_id)
      except User.DoesNotExist:
        return None
