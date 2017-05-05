#
# Copyright (C) 2017 by frePPLe bvba
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

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader, TemplateDoesNotExist
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives

from django.conf import settings
from django.views.generic import FormView
from freppledb.common.registration.forms import PasswordResetRequestForm, SetPasswordForm
from django.contrib import messages
from freppledb.common.models import User
from django.db.models.query_utils import Q
from django.contrib.auth import get_user_model


class ResetPasswordRequestView(FormView):
  template_name = "registration/forgotpassword_form.html"
  success_url = '/data/login/'
  form_class = PasswordResetRequestForm

  @staticmethod
  def validate_email_address(email):
    '''
    This method here validates the if the input is an email address or not. Its return type is boolean, True if the input is a email address or False if its not.
    '''
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

  def post(self, request, *args, **kwargs):
    '''
    A normal post request which takes input from field "email_or_username" (in ResetPasswordRequestForm).
    '''
    form = self.form_class(request.POST)
    if form.is_valid():
      data = form.cleaned_data["email_or_username"]
    if self.validate_email_address(data) is True:                 # uses the method written above
      '''
      If the input is an valid email address, then the following code will lookup for users associated with that email address. If found then an email will be sent to the address, else an error message will be printed on the screen.
      '''
      associated_users = User.objects.filter(Q(email=data) | Q(username=data))
      if associated_users.exists():
        for user in associated_users:
          c = {
              'email': user.email,
              'domain': request.META['HTTP_HOST'],
              'site_name': request.META['HTTP_HOST'],
              'uid': urlsafe_base64_encode(force_bytes(user.pk)),
              'user': user,
              'token': default_token_generator.make_token(user),
              'protocol': 'https' if request.is_secure() else 'http'
              }
          subject = loader.render_to_string('registration/password_reset_subject.txt', c)
          # Email subject *must not* contain newlines
          subject = ''.join(subject.splitlines())
          from_email = settings.DEFAULT_FROM_EMAIL
          message_txt = loader.render_to_string('registration/password_reset_email.txt', c)

          email_message = EmailMultiAlternatives(
            subject, message_txt,
            from_email, [user.email]
            )

          try:
            message_html = loader.render_to_string('registration/password_reset_email.html', c)
          except TemplateDoesNotExist:
            pass
          else:
            email_message.attach_alternative(message_html, 'text/html')
          email_message.send()
        result = self.form_valid(form)
        messages.success(request, 'An email has been sent to ' + data + ". Please check your inbox to continue resetting your password.")
        return result
      result = self.form_invalid(form)
      messages.error(request, 'No user is associated with this email address')
      return result
    else:
      '''
      If the input is an username, then the following code will lookup for users associated with that user. If found then an email will be sent to the user's address, else an error message will be printed on the screen.
      '''
      associated_users = User.objects.filter(username=data)
      if associated_users.exists():
        for user in associated_users:
          c = {
              'email': user.email,
              'domain': request.META['HTTP_HOST'],  # or your domain
              'site_name': request.META['HTTP_HOST'],
              'uid': urlsafe_base64_encode(force_bytes(user.pk)),
              'user': user,
              'token': default_token_generator.make_token(user),
              'protocol': 'https' if request.is_secure() else 'http'
              }
          subject = loader.render_to_string('registration/password_reset_subject.txt', c)
          # Email subject *must not* contain newlines
          subject = ''.join(subject.splitlines())
          from_email = settings.DEFAULT_FROM_EMAIL
          message_txt = loader.render_to_string('registration/password_reset_email.txt', c)

          email_message = EmailMultiAlternatives(
            subject, message_txt,
            from_email, [user.email]
            )

          try:
            message_html = loader.render_to_string('registration/password_reset_email.html', c)
          except TemplateDoesNotExist:
            pass
          else:
            email_message.attach_alternative(message_html, 'text/html')
          email_message.send()
        result = self.form_valid(form)
        messages.success(request, 'Email has been sent to ' + data + "'s email address. Please check your inbox to continue resetting your password.")
        return result
      result = self.form_invalid(form)
      messages.error(request, 'This username does not exist in the system.')
      return result
    messages.error(request, 'Invalid Input')
    return self.form_invalid(form)


class PasswordResetConfirmView(FormView):
  template_name = "registration/forgotpassword_form.html"
  success_url = '/'
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
        new_password = form.cleaned_data['new_password2']
        user.set_password(new_password)
        user.save()
        messages.success(request, 'Password has been reset.')
        return self.form_valid(form)
      else:
        messages.error(request, 'Password reset has not been unsuccessful.')
        return self.form_invalid(form)
    else:
      messages.error(request, 'The reset password link is no longer valid.')
      return self.form_invalid(form)
