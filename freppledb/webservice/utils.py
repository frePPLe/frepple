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

import asyncio
import os
import portend
from datetime import datetime, timedelta

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.common.models import Parameter

# Only a single service can be making updates at the same time
lock = asyncio.Lock()


def useWebService(database=DEFAULT_DB_ALIAS):
    if "FREPPLE_TEST" in os.environ:
        # Tests run without the webservice by default
        return os.environ["FREPPLE_TEST"] == "webservice"
    else:
        param = Parameter.getValue("plan.webservice", database, "true")
        return param.lower() == "true"


def checkRunning(database=DEFAULT_DB_ALIAS, timeout=1.0):
    """
    Returns True if the web service is running.
    """
    if "FREPPLE_TEST" in os.environ:
        (host, port) = settings.DATABASES[database]["TEST"]["FREPPLE_PORT"].split(":")
    else:
        (host, port) = settings.DATABASES[database]["FREPPLE_PORT"].split(":")
    try:
        portend.free(host.replace("0.0.0.0", "localhost"), port, timeout=timeout)
        return False
    except Exception:
        return True


def waitTillRunning(database=DEFAULT_DB_ALIAS, timeout=180):
    """
    Raise an exception if the service isn't running within the specified time.
    """
    if "FREPPLE_TEST" in os.environ:
        (host, port) = settings.DATABASES[database]["TEST"]["FREPPLE_PORT"].split(":")
    else:
        (host, port) = settings.DATABASES[database]["FREPPLE_PORT"].split(":")
    try:
        portend.occupied(host.replace("0.0.0.0", "localhost"), port, timeout=timeout)
    except Exception:
        raise Exception("Web service not running within within %s seconds" % timeout)


def waitTillNotRunning(database=DEFAULT_DB_ALIAS, timeout=60):
    """
    Raise an exception if the web service isn't stopped within the specified time.
    """
    if "FREPPLE_TEST" in os.environ:
        (host, port) = settings.DATABASES[database]["TEST"]["FREPPLE_PORT"].split(":")
    else:
        (host, port) = settings.DATABASES[database]["FREPPLE_PORT"].split(":")
    try:
        portend.free(host.replace("0.0.0.0", "localhost"), port, timeout=timeout)
    except Exception:
        raise Exception("Web service not stopped within %s seconds" % timeout)
