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

import os
from datetime import datetime, timedelta
import psutil
import shlex
import subprocess
import time
from time import sleep

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.template import RequestContext
from django.template.loader import render_to_string

import freppledb.common.commands
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User
from freppledb.common.report import GridReport
from freppledb.execute.models import Task
from freppledb import __version__


def parseConstraints(val):
    try:
        cstrnts = int(val)
    except Exception:
        cstrnts = 0
        for v in val.split(","):
            c = v.strip().lower()
            if c == "capa":
                cstrnts += 4
            elif c == "lt":
                cstrnts += 16 + 32
            elif c == "mfg_lt":
                cstrnts += 16
            elif c == "po_lt":
                cstrnts += 32
    return cstrnts


def constraintString(val):
    if val == 0:
        return "0"
    c = []
    if val & 4:
        c.append("capa")
    if val & 16 or val & 1:
        c.append("mfg_lt")
    if val & 32 or val & 1:
        c.append("po_lt")
    return ",".join(c)


class Command(BaseCommand):
    help = "Runs frePPLe to generate a plan"

    requires_system_checks = []

    def get_version(self):
        return __version__

    @staticmethod
    def process_exists(pid):
        if not pid:
            return False
        try:
            return psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
        except Exception:
            return False

    def add_arguments(self, parser):
        parser.add_argument("--user", dest="user", help="User running the command")
        parser.add_argument(
            "--constraint",
            dest="constraint",
            type=str,
            default="capa,mfg_lt,po_lt,fence",
            help="Constraints to be considered: capa, mfg_lt, po_lt, fence, lt",
        )
        parser.add_argument(
            "--plantype",
            dest="plantype",
            type=int,
            choices=[1, 2],
            default=1,
            help="Plan type: 1=constrained, 2=unconstrained",
        )
        parser.add_argument(
            "--database",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to load data from and export results into",
        )
        parser.add_argument(
            "--task",
            dest="task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument(
            "--env",
            dest="env",
            help="A comma separated list of extra settings passed as environment variables to the engine",
        )
        parser.add_argument(
            "--background",
            dest="background",
            action="store_true",
            default=False,
            help="Run the planning engine in the background (default = False)",
        )
        parser.add_argument(
            "--daemon",
            dest="daemon",
            action="store_true",
            default=False,
            help="Run the planning engine as a daemon process for which we don't need to wait (default = False)",
        )

    def handle(self, **options):
        # Set the server timezone to the TIME_ZONE parameter of djangosettings
        # unsupported by windows
        if not os.name == "nt":
            os.environ["TZ"] = settings.TIME_ZONE
            time.tzset()

        # Pick up the options
        now = datetime.now()

        if "database" in options:
            database = options["database"] or DEFAULT_DB_ALIAS
        else:
            database = DEFAULT_DB_ALIAS
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)
        if "user" in options and options["user"]:
            try:
                user = User.objects.all().using(database).get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        timestamp = now.strftime("%Y%m%d%H%M%S")
        if database == DEFAULT_DB_ALIAS:
            logfile = "frepple-%s%s.log" % (
                (
                    ""
                    if "partition" not in options
                    else "partition%s-" % options["partition"]
                ),
                timestamp,
            )
        else:
            logfile = "frepple_%s-%s%s.log" % (
                database,
                (
                    ""
                    if "partition" not in options
                    else "partition%s-" % options["partition"]
                ),
                timestamp,
            )

        task = None
        old_thread_locals = getattr(_thread_locals, "database", None)
        try:
            # Initialize the task
            setattr(_thread_locals, "database", database)
            if "task" in options and options["task"]:
                try:
                    task = Task.objects.all().using(database).get(pk=options["task"])
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name not in ("runplan", "odoo_import", "odoo_export")
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
                task.logfile = logfile
            else:
                task = Task(
                    name="runplan",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                    logfile=logfile,
                )

            # Validate options
            if "constraint" in options:
                constraint = parseConstraints(options["constraint"])
            else:
                constraint = 4 + 16 + 32
            if "plantype" in options:
                plantype = int(options["plantype"])
            else:
                plantype = 1

            # Reset environment variables
            # TODO avoid having to delete the environment variables. Use options directly?
            for label in freppledb.common.commands.PlanTaskRegistry.getLabels(
                database=database
            ):
                if "env" in options:
                    # Options specified
                    if label[0] in os.environ:
                        del os.environ[label[0]]
                else:
                    # No options specified - default to activate them all
                    os.environ[label[0]] = "1"

            # Set environment variables
            if task.name != "odoo_import":
                if options["env"]:
                    task.arguments = (
                        "--constraint=%s --plantype=%d --env=%s"
                        % (
                            constraintString(constraint),
                            plantype,
                            options["env"],
                        )                    
                    )
                    for i in options["env"].split(","):
                        j = i.split("=")
                        if len(j) == 1:
                            os.environ[j[0]] = "1"
                        else:
                            os.environ[j[0]] = j[1]
                else:
                    task.arguments = "--constraint=%s --plantype=%d" % (
                        constraintString(constraint),
                        plantype,
                    )
            if options["background"]:
                task.arguments += " --background"
            if options["daemon"]:
                task.arguments += " --daemon"
            if "cluster" in options:
                task.arguments += " --cluster=%s" % options["cluster"]

            # Log task
            # Different from the other tasks the frepple engine will write the processid
            task.save(using=database)

            # Locate commands.py
            cmd = freppledb.common.commands.__file__

            def setlimits():
                import resource

                if settings.MAXMEMORYSIZE:
                    resource.setrlimit(
                        resource.RLIMIT_AS,
                        (
                            settings.MAXMEMORYSIZE * 1024 * 1024,
                            (settings.MAXMEMORYSIZE + 10) * 1024 * 1024,
                        ),
                    )
                if settings.MAXCPUTIME:
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (settings.MAXCPUTIME, settings.MAXCPUTIME + 5),
                    )
                # Limiting the file size is a bit tricky as this limit not only applies to the log
                # file, but also to temp files during the export
                # if settings.MAXTOTALLOGFILESIZE:
                #  resource.setrlimit(
                #    resource.RLIMIT_FSIZE,
                #   (settings.MAXTOTALLOGFILESIZE * 1024 * 1024, (settings.MAXTOTALLOGFILESIZE + 1) * 1024 * 1024)
                #   )

            # Make sure the forecast engine uses the same correct timezone
            os.environ["PGTZ"] = settings.TIME_ZONE

            # Prepare environment
            if task.name == "odoo_import":
                os.environ["nowebservice"] = "1"
                os.environ["odoo_read_1"] = "1"
            os.environ["FREPPLE_PLANTYPE"] = str(plantype)
            os.environ["FREPPLE_CONSTRAINT"] = str(constraint)
            os.environ["FREPPLE_TASKID"] = str(task.id)
            os.environ["FREPPLE_DATABASE"] = database
            os.environ["FREPPLE_LOGFILE"] = logfile
            os.environ["FREPPLE_PROCESSNAME"] = settings.DATABASES[database][
                "NAME"
            ].replace("demo", "")
            os.environ["PATH"] = (
                settings.FREPPLE_HOME
                + os.pathsep
                + os.environ["PATH"]
                + os.pathsep
                + settings.FREPPLE_APP
            )
            if os.path.isfile(os.path.join(settings.FREPPLE_HOME, "libfrepple.so")):
                os.environ["LD_LIBRARY_PATH"] = settings.FREPPLE_HOME
            if "DJANGO_SETTINGS_MODULE" not in os.environ:
                os.environ["DJANGO_SETTINGS_MODULE"] = "freppledb.settings"
            os.environ["PYTHONPATH"] = os.path.normpath(settings.FREPPLE_APP)
            libdir = os.path.join(os.path.normpath(settings.FREPPLE_HOME), "lib")
            if os.path.isdir(libdir):
                # Folders used by the Windows version
                os.environ["PYTHONPATH"] += os.pathsep + libdir
                if os.path.isfile(os.path.join(libdir, "library.zip")):
                    os.environ["PYTHONPATH"] += os.pathsep + os.path.join(
                        libdir, "library.zip"
                    )

            if options["background"] or options["daemon"]:
                # Execute as background process on Windows
                if os.name == "nt":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen(
                        ["frepple", cmd],
                        creationflags=0x08000000,
                        startupinfo=startupinfo,
                    )
                else:
                    # Execute as background process on Linux
                    subprocess.Popen(["frepple", cmd], preexec_fn=setlimits)
            else:
                if os.name == "nt":
                    # Execute in foreground on Windows
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    ret = subprocess.call(["frepple", cmd], startupinfo=startupinfo)
                else:
                    # Execute in foreground on Linux
                    ret = subprocess.call(["frepple", cmd], preexec_fn=setlimits)
                if ret != 0 and ret != 2:
                    # Return code 0 is a successful run
                    # Return code is 2 is a run cancelled by a user. That's shown in the status field.
                    raise Exception("Failed with exit code %d" % ret)

            if options["background"]:
                # Wait for the background task to be ready
                while True:
                    sleep(5)
                    t = Task.objects.using(database).get(pk=task.id)
                    if t.status in ["100%", "Canceled", "Failed", "Done"]:
                        break
                    if not self.process_exists(t.processid):
                        t.status = "Failed"
                        t.processid = None
                        t.save(update_fields=["processid", "status"], using=database)
                        break
            else:
                # Reread the task from the database and update it
                task = Task.objects.all().using(database).get(pk=task.id)
                task.processid = None
                task.status = "Done"
                task.finished = datetime.now()
                task.save(
                    update_fields=["processid", "status", "finished"], using=database
                )

        except Exception as e:
            if task:
                task = Task.objects.all().using(database).get(pk=task.id)
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
                task.processid = None
                task.save(using=database)
            raise e

        finally:
            setattr(_thread_locals, "database", old_thread_locals)

    # accordion template
    title = _("Create a plan")
    index = 0

    help_url = "command-reference.html#runplan"

    @staticmethod
    def getHTML(request, widget=False):
        if request.user.has_perm("auth.generate_plan"):
            # Collect optional tasks
            planning_options = freppledb.common.commands.PlanTaskRegistry.getLabels(
                database=request.database
            )
            plantype = "2"
            constraint = 4 + 16 + 32
            current_options = [i[0] for i in planning_options]
            lastrun = (
                Task.objects.all()
                .using(request.database)
                .filter(name="runplan")
                .exclude(arguments__contains="loadplan")
                .order_by("-id")
                .first()
            )
            if lastrun and lastrun.arguments:
                # Copy all settings from the previous run by this user
                for i in shlex.split(lastrun.arguments or ""):
                    if "=" in i:
                        key, val = i.split("=")
                        key = key.strip("--")
                        if key == "constraint":
                            constraint = parseConstraints(val)
                        elif key == "plantype":
                            plantype = val
                        elif key == "env":
                            try:
                                current_options = val.split(",")
                            except Exception:
                                pass
                offset = GridReport.getTimezoneOffset(request)
                if lastrun.started:
                    lastrun.started += offset
                if lastrun.finished:
                    lastrun.finished += offset
                if lastrun.submitted:
                    lastrun.submitted += offset
            return render_to_string(
                "commands/runplan.html",
                {
                    "planning_options": planning_options,
                    "current_options": current_options,
                    "capa_constrained": constraint & 4,
                    "lt_constrained": constraint & 1,
                    "mfg_lt_constrained": constraint & (16 + 1),
                    "po_lt_constrained": constraint & (32 + 1),
                    "fence_constrained": constraint & 8,
                    "plantype": plantype,
                    "widget": widget,
                    "lastrun": lastrun,
                },
                request=request,
            )
        else:
            return None
