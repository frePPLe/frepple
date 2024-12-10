#
# Copyright (C) 2024 by frePPLe bv
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

# The allauth python package is NOT installed by default in frepple.
# You will need to install it yourself.
from allauth.account.utils import user_field
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.auth_backends import AuthenticationBackend
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from django.db import DEFAULT_DB_ALIAS

from freppledb.common.auth import MultiDBBackend
from freppledb.common.models import User


class CustomAuthenticationBackend(AuthenticationBackend):
    pass


class CustomAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        next = request.session.get("next", None)
        if next:
            return next
        else:
            return super().get_login_redirect_url(request)

    def add_message(self, *args, **kwargs):
        # Disable default behavior of displaying a message upon login
        return

    # def is_open_for_signup(self, request):
    #     """
    #     If the external authentication also handles authorization, you leave
    #     this function commented out.

    #     If you'll manage authorization in frepple, you need to:
    #     - Uncomment this function
    #     - Assure the setting SOCIALACCOUNT_AUTO_SIGNUP is set to False
    #       in your djangosettings.py
    #     Note that external accounts will be linked to the frepple users by
    #     their email. Make sure each frepple user has a unique email.
    #     """
    #     return False


class CustomAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.user.id:
            return
        try:
            # If user exists, connect the account to the existing account and login
            user = User.objects.using(DEFAULT_DB_ALIAS).get(
                email=sociallogin.user.email
            )
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        dflt = super().populate_user(request, sociallogin, data)
        if not data.get("username", None) and data.get("name", None):
            user_field(dflt, "username", data["name"])
        return dflt
