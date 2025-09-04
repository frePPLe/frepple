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
import sys

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.common.auth import getWebserviceAuthorization
from freppledb.common.commands import PlanTaskRegistry
from freppledb.common.models import Parameter
from freppledb.common.utils import get_databases

# Only a single service can be making updates at the same time
try:
    lock = asyncio.Lock()
except Exception:
    lock = None

# Solvers reusable for all services
mrp_solver = None
clean_solver = None
fcst_solver = None


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
        (host, port) = get_databases()[database]["TEST"]["FREPPLE_PORT"].split(":")
    else:
        (host, port) = get_databases()[database]["FREPPLE_PORT"].split(":")
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
        (host, port) = get_databases()[database]["TEST"]["FREPPLE_PORT"].split(":")
    else:
        (host, port) = get_databases()[database]["FREPPLE_PORT"].split(":")
    try:
        portend.occupied(host.replace("0.0.0.0", "localhost"), port, timeout=timeout)
    except Exception:
        raise Exception("Web service not running within within %s seconds" % timeout)


def waitTillNotRunning(database=DEFAULT_DB_ALIAS, timeout=60):
    """
    Raise an exception if the web service isn't stopped within the specified time.
    """
    if "FREPPLE_TEST" in os.environ:
        (host, port) = get_databases()[database]["TEST"]["FREPPLE_PORT"].split(":")
    else:
        (host, port) = get_databases()[database]["FREPPLE_PORT"].split(":")
    try:
        portend.free(host.replace("0.0.0.0", "localhost"), port, timeout=timeout)
    except Exception:
        raise Exception("Web service not stopped within %s seconds" % timeout)


def getWebServiceContext(request):
    if "FREPPLE_TEST" in os.environ:
        port = get_databases()[request.database]["TEST"].get("FREPPLE_PORT", None)
    else:
        port = get_databases()[request.database].get("FREPPLE_PORT", None)
    proxied = get_databases()[request.database].get(
        "FREPPLE_PORT_PROXIED",
        not settings.DEBUG
        and not ("freppleservice" in sys.argv or "runserver" in sys.argv)
        and "FREPPLE_TEST" not in os.environ,
    )
    if port and not proxied:
        port = port.replace("0.0.0.0", "localhost")
    return {
        "token": getWebserviceAuthorization(
            user=request.user.username, sid=request.user.id, exp=3600
        ),
        "port": port,
        "proxied": proxied,
    }


def createSolvers(loglevel=2, database=DEFAULT_DB_ALIAS):
    import frepple

    global clean_solver, mrp_solver, fcst_solver

    try:
        from freppledb.execute.management.commands.runplan import parseConstraints

        constraint = parseConstraints(os.environ["FREPPLE_CONSTRAINT"])
    except Exception:
        constraint = 4 + 16 + 32  # Default is with all constraints enabled
    clean_solver = frepple.solver_delete(loglevel=loglevel, constraint=constraint)
    mrp_solver = frepple.solver_mrp(
        loglevel=loglevel,
        constraints=constraint,
        erasePreviousFirst=False,
        plantype=1,
        lazydelay=int(Parameter.getValue("lazydelay", database, "86400")),
        minimumdelay=int(Parameter.getValue("plan.minimumdelay", database, "3600")),
        rotateresources=(
            Parameter.getValue("plan.rotateResources", database, "true").lower()
            == "true"
        ),
        iterationmax=int(Parameter.getValue("plan.iterationmax", database, "0")),
    )
    supplyplanningtask = PlanTaskRegistry.getTask(sequence=200)
    if supplyplanningtask:
        if hasattr(supplyplanningtask, "debugResource"):
            mrp_solver.userexit_resource = supplyplanningtask.debugResource
        if hasattr(supplyplanningtask, "debugDemand"):
            mrp_solver.userexit_demand = supplyplanningtask.debugDemand
        if hasattr(supplyplanningtask, "debugOperation"):
            mrp_solver.userexit_operation = supplyplanningtask.debugOperation

    if "freppledb.forecast" in settings.INSTALLED_APPS:
        from freppledb.forecast.commands import createForecastSolver

        fcst_solver = createForecastSolver(database)
        if fcst_solver:
            fcst_solver.loglevel = loglevel
