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
from django.core.exceptions import ImproperlyConfigured
from django.utils.autoreload import autoreload_started


def watchDjangoSettings(sender, **kwargs):
    sender.watch_file(os.path.join(settings.FREPPLE_CONFIGDIR, "djangosettings.py"))


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
            "bootstrap3",
            "freppledb.boot",
            "freppledb.input",
            "freppledb.output",
            "freppledb.execute",
            "freppledb.common",
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
