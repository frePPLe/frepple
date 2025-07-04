#
# Copyright (C) 2019 by frePPLe bv
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

import os
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.utils.autoreload import autoreload_started


def watchDjangoSettings(sender, **kwargs):
    for f in ["djangosettings.py", "localsettings.py", "wsgi.py"]:
        sender.extra_files.add(Path(os.path.join(settings.FREPPLE_CONFIGDIR, f)))


@checks.register()
def check_python_packages(app_configs, **kwargs):
    """
    Check whether all required python packages are available.
    """
    errors = []
    for p in [
        ("portend", "portend"),
        ("rest_framework", "djangorestframework"),
        ("rest_framework_bulk", "djangorestframework-bulk"),
        ("bootstrap3", "django-bootstrap3"),
        ("django_filters", "django-filter"),
        ("html5lib", "html5lib"),
        ("jdcal", "jdcal"),
        ("openpyxl", "openpyxl"),
        ("lxml", "lxml"),
        ("jwt", "PyJWT"),
        ("requests", "requests"),
        ("dateutil", "python-dateutil"),
        ("PIL", "pillow"),
        ("psutil", "psutil"),
        ("pysftp", "pysftp"),
    ]:
        try:
            __import__(p[0])
        except ModuleNotFoundError:
            errors.append(
                checks.Error(
                    "Missing python package '%s'" % p[1],
                    hint="Install with 'pip3 install %s'" % p[1],
                    obj=None,
                    id="frepple.dependency",
                )
            )
    return errors


class CommonConfig(AppConfig):
    name = "freppledb.common"
    verbose_name = "common"

    def ready(self):
        autoreload_started.connect(watchDjangoSettings)

        # Validate all required modules are activated
        missing = []
        required_apps = [
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "freppledb.boot",
            "freppledb.input",
            "freppledb.output",
            "freppledb.execute",
            "freppledb.common",
            "freppledb.archive",
            "django_filters",
            "rest_framework",
            "django.contrib.admin",
        ]
        for app in required_apps:
            if app not in settings.INSTALLED_APPS:
                missing.append(app)
        if missing:
            raise ImproperlyConfigured(
                "Missing required apps in INSTALLED_APPS: %s" % ", ".join(missing)
            )

        user_logged_in.disconnect(dispatch_uid="update_last_login")
