#
# Copyright (C) 2016-2019 by frePPLe bv
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
import shlex
import os
import psutil

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from freppledb import VERSION
from freppledb.common.models import Parameter
from freppledb.common.utils import get_databases
from freppledb.input.models import Item
from freppledb.execute.models import Task
from freppledb.execute.management.commands.runplan import parseConstraints
from ...utils import waitTillRunning, checkRunning


class Command(BaseCommand):
    help = "This command starts the frePPLe web service."

    requires_system_checks = []

    def get_version(self):
        return VERSION

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--forcerestart",
            action="store_true",
            default=False,
            help="Restart the web service if it is already running.",
        )
        parser.add_argument(
            "--database", default=DEFAULT_DB_ALIAS, help="Nominates a specific database"
        )
        parser.add_argument(
            "--wait",
            action="store_true",
            default=False,
            help="Wait until the service is up and running",
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Optional task identifier",
        )
        parser.add_argument(
            "--daemon",
            dest="daemon",
            action="store_true",
            default=False,
            help="Run the planning engine as a daemon process for which we don't need to wait (default = False)",
        )
        parser.add_argument("--env", default="loadplan", help="environment variable")

    def handle(self, **options):
        # Validate the database option
        database = options["database"]
        if database not in get_databases():
            raise CommandError("No database settings known for '%s'" % database)

        # Update task when specified
        if options["task"]:
            try:
                task = Task.objects.all().using(database).get(pk=options["task"])
            except Exception:
                raise CommandError("Task identifier not found")
            if (
                task.started
                or task.finished
                or task.status != "Waiting"
                or task.name != "runwebservice"
            ):
                raise CommandError("Invalid task identifier")
            task.started = datetime.now()
            task.processid = os.getpid()
        else:
            task = None

        if not Item.objects.all().using(database).exists():
            if task:
                task.status = "Done"
                task.finished = datetime.now()
                task.message = "Skipped starting the service since there are no data."
                task.processid = None
                task.save(using=database)
            return

        already_running = checkRunning(database=database)
        if not options["forcerestart"] and already_running:
            # Already running, and we are not forcing a restart
            if task:
                task.status = "Done"
                task.finished = datetime.now()
                task.message = "Web service already running."
                task.processid = None
                task.save(using=database)
            return

        if not already_running:
            # Protection against race conditions.
            # There is a delay between the start of the web service and the
            # web service's port number being occupied.
            # During this time window we could launch the service multiple times.
            try:
                startingsvc = (
                    Task.objects.all()
                    .using(database)
                    .filter(
                        name="runplan",
                        arguments__icontains="loadplan",
                        processid__isnull=False,
                    )
                    .order_by("-id")
                    .only("processid")
                    .first()
                )
                if (
                    startingsvc
                    and psutil.Process(startingsvc.processid).status()
                    != psutil.STATUS_ZOMBIE
                ):
                    # We found a process of a starting web service!
                    if task:
                        task.status = "Done"
                        task.finished = datetime.now()
                        task.message = "Web service already starting."
                        task.processid = None
                        task.save(using=database)
                    return
            except Exception as e:
                pass

        try:
            # Retrieve constraint and plan type from the last run
            constraint = 4 + 16 + 32
            plantype = 1
            try:
                lastrun = (
                    Task.objects.all()
                    .using(database)
                    .filter(name="runplan")
                    .exclude(arguments__icontains="loadplan")
                    .order_by("-id")[0]
                )
                for i in shlex.split(lastrun.arguments or ""):
                    if "=" in i:
                        key, val = i.split("=")
                        if key == "--constraint":
                            constraint = parseConstraints(val)
                        elif key == "--plantype":
                            plantype = int(val)
            except Exception:
                pass

            kwargs = {
                "constraint": constraint,
                "plantype": plantype,
                "env": options["env"],
                "database": database,
            }
            if options["user"]:
                kwargs["user"] = options["user"]
            if options["daemon"]:
                kwargs["daemon"] = True
            else:
                kwargs["background"] = True
            management.call_command("runplan", **kwargs)

            if options["wait"]:
                # Wait until the service is up
                try:
                    waitTillRunning(database=database, timeout=180)
                except Exception:
                    raise CommandError("Web service didn't start timely")
        finally:
            if task:
                task.status = "Done"
                task.finished = datetime.now()
                task.processid = None
                task.save(using=database)

    # accordion template
    title = _("web service")
    index = 1500
    help_url = "command-reference.html#runwebservice"

    @staticmethod
    def getHTML(request):
        if (
            Parameter.getValue("plan.webservice", request.database, "true").lower()
            == "true"
        ):
            return render_to_string("commands/runwebservice.html", request=request)
        else:
            return None
