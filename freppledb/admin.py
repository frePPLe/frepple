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

from importlib import import_module

from django.conf import settings
from django.contrib.admin.sites import AdminSite, AlreadyRegistered
from django.contrib.admin.forms import AuthenticationForm
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _


class freppleAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. Note that both fields may be case-sensitive."
        ),
        "inactive": _("This user is inactive."),
    }

    def confirm_login_allowed(self, user):
        if not getattr(user, "databases", None):
            raise ValidationError(_("This account is inactive."), code="inactive")


class freppleAdminSite(AdminSite):
    login_form = freppleAuthenticationForm

    def register(self, model_or_iterable, admin_class=None, force=False, **options):
        try:
            super().register(model_or_iterable, admin_class, **options)
        except AlreadyRegistered:
            # Ignore exception if the model is already registered. It indicates that
            # another app has already registered it.
            if force:
                # Unregister the previous one and register ourselves
                self.unregister(model_or_iterable)
                super().register(model_or_iterable, admin_class, **options)


# Create two admin sites where all our apps will register their models
data_site = freppleAdminSite(name="data")

# Adding the admin modules of each installed application.
for app in settings.INSTALLED_APPS:
    try:
        mod = import_module("%s.admin" % app)
    except ImportError as e:
        # Silently ignore if its the admin module which isn't found
        if str(e) not in (
            "No module named %s.admin" % app,
            "No module named '%s.admin'" % app,
        ):
            raise e
