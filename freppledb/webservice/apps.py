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

import logging
import sys
import random
from threading import Thread
from time import sleep

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core import management
from django.db import DEFAULT_DB_ALIAS, connections, close_old_connections

logger = logging.getLogger(__name__)


def startWebService(request, **kwargs):
    """
    When a user logs in, we start loading all scenario models in memory if it isn't loaded already.
    """
    from freppledb.common.models import Scenario, Parameter

    # Random delay to avoid simultaneous web service starts
    sleep(random.uniform(0.0, 0.5))
    close_old_connections()

    active_scenarios = {
        i["name"]
        for i in Scenario.objects.using(DEFAULT_DB_ALIAS)
        .filter(status="In use")
        .values("name")
    }
    for i in settings.DATABASES:
        if (
            i in active_scenarios
            and Parameter.getValue("plan.webservice", i, "true").lower() == "true"
        ):
            try:
                management.call_command("runwebservice", database=i, daemon=True)
            except Exception as e:
                logger.warning("Can't launch webservice in scenario '%s': %s" % (i, e))
    connections.close_all()


def startWebServiceAsync(request, **kwargs):
    # Note: API requests don't start the web service
    if not hasattr(request, "api"):
        Thread(target=startWebService, args=(request,), kwargs=kwargs, daemon=True).start()


class WebServiceConfig(AppConfig):
    name = "freppledb.webservice"
    verbose_name = "planning engine web service"

    def ready(self):
        # Register a signal handler when somebody logs in
        if "test" not in sys.argv:
            user_logged_in.connect(
                startWebServiceAsync, dispatch_uid=startWebServiceAsync
            )
