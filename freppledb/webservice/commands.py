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

from datetime import datetime
import os
import logging
import sys
from time import sleep
from daphne.cli import CommandLineInterface

from django.db import DEFAULT_DB_ALIAS, connections
from django.conf import settings
from django.core import management

import freppledb
from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.models import Parameter
from freppledb.common.utils import get_databases
from freppledb.execute.models import Task
from freppledb.webservice.utils import useWebService, createSolvers

logger = logging.getLogger(__name__)


class WebService:
    service = None

    @classmethod
    def start(cls, address, port):
        cls.service = CommandLineInterface()
        cls.service.run(
            (
                ":".join(settings.ASGI_APPLICATION.rsplit(".", 1)),
                "--bind",
                address,
                "--port",
                port,
            )
        )

    @classmethod
    def stop(cls):
        if cls.service:
            cls.service.server.stop()


@PlanTaskRegistry.register
class setDatabaseConnection(PlanTask):
    """
    Set a PostgreSQL connection string used by the core engine to
    connect to the database.
    http://www.postgresql.org/docs/10/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
    """

    description = "Setting database connection and cache"
    sequence = 90.5

    @staticmethod
    def getWeight(**kwargs):
        return 0.1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        # Database connection string
        res = ["client_encoding=utf-8", "connect_timeout=10"]
        if get_databases()[database]["NAME"]:
            res.append("dbname=%s" % get_databases()[database]["NAME"])
        if get_databases()[database]["USER"]:
            res.append("user=%s" % get_databases()[database]["USER"])
        if get_databases()[database]["PASSWORD"]:
            res.append("password=%s" % get_databases()[database]["PASSWORD"])
        if get_databases()[database]["HOST"]:
            res.append("host=%s" % get_databases()[database]["HOST"])
        if get_databases()[database]["PORT"]:
            res.append("port=%s" % get_databases()[database]["PORT"])
        frepple.settings.dbconnection = " ".join(res)
        frepple.settings.database = database
        frepple.settings.dbchannel = "frepple"

        # Cache settings
        frepple.cache.maximum = settings.CACHE_MAXIMUM
        frepple.cache.threads = settings.CACHE_THREADS
        frepple.cache.write_immediately = True
        frepple.cache.loglevel = Parameter.getValue("cache.loglevel", database, 0)


@PlanTaskRegistry.register
class StopWebService(PlanTask):
    description = "Stop web service"
    sequence = 999

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if useWebService(database) and "nowebservice" not in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "FREPPLE_TEST" in os.environ:
            server = get_databases()[database]["TEST"].get("FREPPLE_PORT", None)
        else:
            server = get_databases()[database].get("FREPPLE_PORT", None)
        if not server:
            return

        # The previous quoting server is shut down at the start of the planning
        # two reasons:
        #  - During the creation of the plan we would have 2 processes both writing
        #    to the same log file.
        #  - Avoid doubling the memory requirements.
        # Disadvantages are that 1) the web service is not available while the plan
        # is being generated, and 2) if the new plan fails for some reason we won't
        # have an active web service for a while.
        logger.info("Previous web service shutting down")

        # Connect to the url "/stop/"
        try:
            # Call the stopwebservice command to benefit from the emergency brake.
            management.call_command("stopwebservice", database=database, force=True)
        except Exception:
            # The service wasn't up
            pass

        # Clear the processid for extra robustness.
        # There should no longer a processid on any runplan task (except for the current task).
        # The command runwebservice expects the processid column to be correct.
        Task.objects.all().using(database).filter(
            processid__isnull=False, name="runplan"
        ).exclude(processid=os.getpid()).update(processid=None)

        # Give it some time to die
        sleep(2)


@PlanTaskRegistry.register
class RunWebService(PlanTask):
    description = "Run web service"
    sequence = 1000

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if useWebService(database) and "nowebservice" not in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "FREPPLE_TEST" in os.environ:
            server = get_databases()[database]["TEST"].get("FREPPLE_PORT", None)
        else:
            server = get_databases()[database].get("FREPPLE_PORT", None)
        if not server:
            logger.warning(
                "\nWeb service will not be activated: missing FREPPLE_PORT configuration for database %s"
                % database
            )
            return

        # Create solvers for the replanning solvers
        loglevel = int(Parameter.getValue("plan.loglevel", database, 0))
        createSolvers(loglevel=loglevel, database=database)

        # Start the web service
        logger.info("Web service starting at %s" % datetime.now().strftime("%H:%M:%S"))
        if PlanTaskRegistry.reg.task:
            PlanTaskRegistry.reg.task.finished = datetime.now()
            PlanTaskRegistry.reg.task.status = "Done"
            PlanTaskRegistry.reg.task.message = "Web service active"
            PlanTaskRegistry.reg.task.save(using=database)

        # Close all database connections.
        connections.close_all()
        if "FREPPLE_TEST" in os.environ:
            server = get_databases()[database]["TEST"].get("FREPPLE_PORT", None)
        else:
            server = get_databases()[database].get("FREPPLE_PORT", None)

        # Running the server
        os.environ["FREPPLE_DATABASE"] = database
        freppledb.mode = "ASGI"
        WebService.start(*server.split(":", 1))

        # Exit immediately, to avoid that any more messages are printed to the log file
        sys.exit(0)
