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

from datetime import datetime, timedelta
import logging
from multiprocessing import Process
import operator
import os
import shlex
from subprocess import Popen
import sys
from threading import Thread
import time

from django.conf import settings
from django.core.management import get_commands, load_command_class

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections

from freppledb import __version__, runCommand
from freppledb.common.models import Parameter
from freppledb.common.middleware import _thread_locals
from freppledb.common.utils import get_databases
from freppledb.execute.models import Task


logger = logging.getLogger(__name__)


class WorkerAlive(Thread):
    def __init__(self, database=DEFAULT_DB_ALIAS):
        self.database = database
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        while True:
            try:
                p = (
                    Parameter.objects.all()
                    .using(self.database)
                    .get_or_create(pk="Worker alive")[0]
                )
                p.value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                p.save(update_fields=["value"])
            except Exception:
                pass
            time.sleep(5)


def checkActive(database=DEFAULT_DB_ALIAS):
    try:
        p = Parameter.objects.all().using(database).get(pk="Worker alive")
        return datetime.now() - datetime.strptime(
            p.value, "%Y-%m-%d %H:%M:%S"
        ) <= timedelta(0, 5)
    except Exception:
        return False


def launchWorker(database=DEFAULT_DB_ALIAS):
    os.environ["FREPPLE_CONFIGDIR"] = settings.FREPPLE_CONFIGDIR
    if not checkActive(database):
        if os.path.isfile(os.path.join(settings.FREPPLE_APP, "frepplectl.py")):
            if "python" in sys.executable:
                # Development layout
                Popen(
                    [
                        sys.executable,  # Python executable
                        os.path.join(settings.FREPPLE_APP, "frepplectl.py"),
                        "runworker",
                        "--database=%s" % database,
                    ]
                )
            else:
                # Deployment on Apache web server
                Popen(
                    [
                        "python",
                        os.path.join(settings.FREPPLE_APP, "frepplectl.py"),
                        "runworker",
                        "--database=%s" % database,
                    ],
                    creationflags=0x08000000,
                )
        else:
            # Linux standard installation
            Popen(["frepplectl", "runworker", "--database=%s" % database])


def command_accepts_user_argument(command_name):
    app_name = get_commands()[command_name]
    command = load_command_class(app_name, command_name)
    parser = command.create_parser("", command_name)
    for action in parser._actions:
        if "--user" in action.option_strings:
            return True
    return False


def runTask(task, database):
    task.started = datetime.now()
    # Verify the command exists
    exists = False
    for commandname in get_commands():
        if commandname == task.name:
            exists = True
            break

    if not exists:
        # No such task exists
        logger.error("Task %s not recognized" % task.name)
        task.status = "Failed"
        task.processid = None
        task.save(using=database)
    else:
        # Close all database connections to assure the parent and child
        # process don't share them.
        connections.close_all()
        # Spawn a new command process
        args = []
        kwargs = {"database": database, "task": task.id, "verbosity": 0}
        if task.user and command_accepts_user_argument(task.name):
            kwargs["user"] = task.user.username
        background = "background" in task.arguments if task.arguments else False
        if task.arguments:
            for i in shlex.split(task.arguments or ""):
                if "=" in i:
                    key, val = i.split("=")
                    kwargs[key.strip("--").replace("-", "_")] = val
                else:
                    args.append(i)
        child = Process(
            target=runCommand,
            args=(task.name, *args),
            kwargs=kwargs,
            name="frepplectl %s" % task.name,
        )
        child.start()

        # Normally, the child will update the processid.
        # Just to make sure, we do it also here.
        task.processid = child.pid
        task.save(update_fields=["processid"], using=database)

        # Wait for the child to finish
        child.join()

        # Read the task again from the database and update it
        task = Task.objects.all().using(database).get(pk=task.id)
        task.processid = None
        if (
            task.status not in ("Done", "Failed")
            or not task.finished
            or not task.started
        ) and task.status != "Canceled":
            now = datetime.now()
            if not task.started:
                task.started = now
            if not background:
                if not task.finished:
                    task.finished = now
                if task.status not in ("Done", "Failed"):
                    task.status = "Done"
            task.save(using=database)
        if "FREPPLE_TEST" not in os.environ:
            logger.debug(
                "Worker %s for database '%s' finished task %d at %s: success"
                % (
                    os.getpid(),
                    get_databases()[database]["NAME"],
                    task.id,
                    datetime.now(),
                )
            )


class Command(BaseCommand):
    help = """Processes the job queue of a database.
    The command is intended only to be used internally by frePPLe, not by an API or user.
    """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to load data from and export results into",
        )
        parser.add_argument(
            "--continuous",
            action="store_true",
            default=False,
            help="Keep the worker alive after the queue is empty",
        )

    def handle(self, *args, **options):
        # Pick up the options
        database = options["database"]
        if database not in get_databases():
            raise CommandError("No database settings known for '%s'" % database)
        continuous = options["continuous"]

        # Use the test database if we are running the test suite
        if "FREPPLE_TEST" in os.environ:
            for db in get_databases():
                connections[db].close()
                get_databases()[db]["NAME"] = get_databases()[db]["TEST"]["NAME"]

        # Check if a worker already exists
        if checkActive(database):
            if "FREPPLE_TEST" not in os.environ:
                logger.debug(
                    "Worker for database '%s' already active"
                    % get_databases()[database]["NAME"]
                )
            return

        # Spawn a worker-alive thread
        WorkerAlive(database).start()

        # Process the queue
        if "FREPPLE_TEST" not in os.environ:
            logger.debug(
                "Worker %s for database '%s' starting to process jobs"
                % (os.getpid(), get_databases()[database]["NAME"])
            )
        idle_loop_done = False
        old_thread_locals = getattr(_thread_locals, "database", None)
        setattr(_thread_locals, "database", database)
        while True:
            try:
                task = (
                    Task.objects.all()
                    .using(database)
                    .filter(status="Waiting")
                    .order_by("id")[0]
                )
                idle_loop_done = False
            except Exception:
                # No more tasks found
                if continuous:
                    time.sleep(5)
                    continue
                else:
                    # Special case: we need to permit a single idle loop before shutting down
                    # the worker. If we shut down immediately, a newly launched task could think
                    # that a worker is already running - while it just shut down.
                    if idle_loop_done:
                        break
                    else:
                        idle_loop_done = True
                        time.sleep(5)
                        continue
            try:
                if "FREPPLE_TEST" not in os.environ:
                    logger.debug(
                        "Worker %s for database '%s' starting task %d at %s"
                        % (
                            os.getpid(),
                            get_databases()[database]["NAME"],
                            task.id,
                            datetime.now(),
                        )
                    )
                runTask(task, database)
            except Exception as e:
                try:
                    # Read the task again from the database and update.
                    task = Task.objects.all().using(database).get(pk=task.id)
                    task.status = "Failed"
                    now = datetime.now()
                    if not task.started:
                        task.started = now
                    task.finished = now
                    task.message = str(e)
                    task.save(using=database)
                    if "FREPPLE_TEST" not in os.environ:
                        logger.debug(
                            "Worker %s for database '%s' finished task %d at %s: failed"
                            % (
                                os.getpid(),
                                get_databases()[database]["NAME"],
                                task.id,
                                datetime.now(),
                            )
                        )
                except Exception:
                    # It's possible the database is release by now and we can't updte the task
                    pass

        # Remove the parameter again
        try:
            Parameter.objects.all().using(database).get(pk="Worker alive").delete()
        except Exception:
            pass
        setattr(_thread_locals, "database", old_thread_locals)

        # Remove log files exceeding the configured disk space allocation
        totallogs = 0
        filelist = []
        for x in os.listdir(settings.FREPPLE_LOGDIR):
            if x.endswith((".log", ".dump")):
                filename = os.path.join(settings.FREPPLE_LOGDIR, x)
                # needs try/catch because log files may still be open or being used and Windows does not like it
                try:
                    size = os.path.getsize(filename)
                    filelist.append(
                        {
                            "name": filename,
                            "size": size,
                            "creation": os.path.getctime(filename),
                        }
                    )
                    totallogs += size
                except Exception:
                    pass

        todelete = totallogs - settings.MAXTOTALLOGFILESIZE * 1024 * 1024
        filelist.sort(key=operator.itemgetter("creation"))
        for fordeletion in filelist:
            if todelete > 0:
                try:
                    os.remove(fordeletion["name"])
                    todelete -= fordeletion["size"]
                except Exception:
                    pass
            else:
                break

        # Exit
        if "FREPPLE_TEST" not in os.environ:
            logger.debug(
                "Worker %s for database '%s' finished all jobs in the queue and exits"
                % (os.getpid(), get_databases()[database]["NAME"])
            )
