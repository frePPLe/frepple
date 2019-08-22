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
from django.utils.autoreload import autoreload_started


def watchDjangoSettings(sender, **kwargs):
    sender.watch_file(os.path.join(settings.FREPPLE_CONFIGDIR, "djangosettings.py"))


class CommonConfig(AppConfig):
    name = "freppledb.common"
    verbose_name = "common"

    def ready(self):
        autoreload_started.connect(watchDjangoSettings)
