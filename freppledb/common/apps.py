#
# Copyright (C) 2019 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
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
