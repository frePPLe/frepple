#
# Copyright (C) 2017 by frePPLe bv
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

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader, TemplateDoesNotExist
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives

from django.conf import settings
from django.views.generic import FormView
from freppledb.common.registration.forms import (
    PasswordResetRequestForm,
    SetPasswordForm,
)
from django.contrib import messages
from freppledb.common.models import User
from django.db.models.query_utils import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from ..utils import sendEmail


class ResetPasswordRequestView(FormView):
    template_name = "registration/forgotpassword_form.html"
    success_url = "/data/login/"
    form_class = PasswordResetRequestForm

    @staticmethod
    def validate_email_address(email):
        """
        This method here validates the if the input is an email address or not. Its return type is boolean, True if the input is a email address or False if its not.
        """
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

    def post(self, request, *args, **kwargs):
        """
        A normal post request which takes input from field "email_or_username" (in ResetPasswordRequestForm).
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data["email_or_username"]
        if self.validate_email_address(data):
            associated_users = User.objects.filter(
                Q(email__iexact=data) | Q(username__iexact=data)
            )
        else:
            associated_users = User.objects.filter(username=data)
        if associated_users.exists():
            for user in associated_users:
                sendEmail(
                    to=user.email,
                    subject=_("Password Reset"),
                    body=_(
                        "\nDear {{user}},\n\n"
                        "You're receiving this email because you requested a password reset for your user account.\n\n"
                        "Please go to the following page and choose a new password:\n"
                        "   {{url}}{% url 'reset_password_confirm' uidb64=uid token=token %}\n\n"
                        "Thanks for using frepple!\n\n"
                    ),
                    body_html=_(
                        "Dear {{user}},<br><br>"
                        "You're receiving this email because you requested a password reset for your user account.<br>"
                        'Please choose a new password on <a style="font-weight:bold" href="{{url}}{% url "reset_password_confirm" uidb64=uid token=token %}">this page</a><br>'
                        "<br>Thanks for using frepple!<br><br>"
                    ),
                    user=user.username,
                    url=f"{"https" if request.is_secure() else "http"}://"
                    f"{request.META["HTTP_HOST"]}",
                    uid=urlsafe_base64_encode(force_bytes(user.pk)),
                    token=default_token_generator.make_token(user),
                )
            result = self.form_valid(form)
            messages.success(
                request,
                "An email has been sent to "
                + data
                + ". Please check your inbox to continue resetting your password.",
            )
            return result
        else:
            messages.error(request, "No user is associated with this email address")
            return self.form_invalid(form)


class PasswordResetConfirmView(FormView):
    template_name = "registration/forgotpassword_form.html"
    success_url = "/"
    form_class = SetPasswordForm

    def post(self, request, uidb64=None, token=None, *arg, **kwargs):
        """
        View that checks the hash in a password reset link and presents a
        form for entering a new password.
        """
        UserModel = get_user_model()
        form = self.form_class(request.POST)
        assert uidb64 is not None and token is not None  # checked by URLconf
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            if form.is_valid():
                new_password = form.cleaned_data["new_password2"]
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password has been reset.")
                return self.form_valid(form)
            else:
                messages.error(request, "Password reset has not been unsuccessful.")
                return self.form_invalid(form)
        else:
            messages.error(request, "The reset password link is no longer valid.")
            return self.form_invalid(form)
