#
# Copyright (C) 2019 by frePPLe bv
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

import os

from django.apps import AppConfig
from django.conf import settings
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.utils.autoreload import autoreload_started


def watchDjangoSettings(sender, **kwargs):
    sender.watch_file(os.path.join(settings.FREPPLE_CONFIGDIR, "djangosettings.py"))
    sender.watch_file(os.path.join(settings.FREPPLE_CONFIGDIR, "localsettings.py"))


@checks.register()
def check_python_packages(app_configs, **kwargs):
    """
    Check whether all required python packages are available.
    """
    errors = []
    for p in [
        ("cheroot", "cheroot"),
        ("portend", "portend"),
        ("rest_framework", "djangorestframework"),
        ("rest_framework_bulk", "djangorestframework-bulk"),
        ("rest_framework_filters", "djangorestframework-filters"),
        ("django_admin_bootstrapped", "django-admin-bootstrapped"),
        ("bootstrap3", "django-bootstrap3"),
        ("django_filters", "django-filter"),
        ("html5lib", "html5lib"),
        ("jdcal", "jdcal"),
        ("markdown", "markdown"),
        ("openpyxl", "openpyxl"),
        ("lxml", "lxml"),
        ("jwt", "PyJWT"),
        ("requests", "requests"),
        ("dateutil", "python-dateutil"),
        ("PIL", "pillow"),
        ("psutil", "psutil"),
        ("setuptools-rust", "setuptools-rust"),
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
            "django_admin_bootstrapped",
            "django.contrib.admin",
        ]
        for app in required_apps:
            if app not in settings.INSTALLED_APPS:
                missing.append(app)
        if missing:
            raise ImproperlyConfigured(
                "Missing required apps in INSTALLED_APPS: %s" % ", ".join(missing)
            )
