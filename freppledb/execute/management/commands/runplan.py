#
# Copyright (C) 2007-2013 by frePPLe bv
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
from datetime import datetime
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
from django.template import Template, RequestContext

import freppledb.common.commands
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User
from freppledb.execute.models import Task
from freppledb import __version__


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
            type=int,
            default=15,
            choices=range(0, 16),
            help="Constraints to be considered: 1=lead time, 4=capacity, 8=release fence",
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
                ""
                if "partition" not in options
                else "partition%s-" % options["partition"],
                timestamp,
            )
        else:
            logfile = "frepple_%s-%s%s.log" % (
                database,
                ""
                if "partition" not in options
                else "partition%s-" % options["partition"],
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
                constraint = int(options["constraint"])
                if constraint < 0 or constraint > 15:
                    raise ValueError("Invalid constraint: %s" % options["constraint"])
            else:
                constraint = 15
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
            if options["env"]:
                task.arguments = "--constraint=%d --plantype=%d --env=%s" % (
                    constraint,
                    plantype,
                    options["env"],
                )
                for i in options["env"].split(","):
                    j = i.split("=")
                    if len(j) == 1:
                        os.environ[j[0]] = "1"
                    else:
                        os.environ[j[0]] = j[1]
            else:
                task.arguments = "--constraint=%d --plantype=%d" % (
                    constraint,
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
    def getHTML(request):

        if request.user.has_perm("auth.generate_plan"):
            # Collect optional tasks
            planning_options = freppledb.common.commands.PlanTaskRegistry.getLabels(
                database=request.database
            )
            plantype = "2"
            constraint = 15
            current_options = [i[0] for i in planning_options]
            lastrun = (
                Task.objects.all()
                .using(request.database)
                .filter(name="runplan")
                .exclude(arguments__contains="loadplan")
                .order_by("-id")
                .only("arguments")
                .first()
            )
            if lastrun and lastrun.arguments:
                # Copy all settings from the previous run by this user
                for i in shlex.split(lastrun.arguments):
                    if "=" in i:
                        key, val = i.split("=")
                        key = key.strip("--")
                        if key == "constraint":
                            try:
                                constraint = int(val)
                            except Exception:
                                pass
                        elif key == "plantype":
                            plantype = val
                        elif key == "env":
                            try:
                                current_options = val.split(",")
                            except Exception:
                                pass

            context = RequestContext(
                request,
                {
                    "planning_options": planning_options,
                    "current_options": current_options,
                    "capacityconstrained": constraint & 4,
                    "materialconstrained": constraint & 2,
                    "leadtimeconstrained": constraint & 1,
                    "fenceconstrained": constraint & 8,
                    "plantype": plantype,
                },
            )

            template = Template(
                """
        {%% load i18n %%}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/runplan/">{%% csrf_token %%}
          <table>
          <tr>
            <td style="vertical-align:top; padding: 15px">
                <button type="submit" class="btn btn-primary">{%% trans "launch"|capfirst %%}</button>
            </td>
            <td  style="padding: 15px;">%s<br><br>
          {%% if planning_options %%}
          <p {%% if planning_options|length <= 1 %%}style="display: none"{%% endif %%}><b>{%% filter capfirst %%}%s{%% endfilter %%}</b><br>
          {%% for b in planning_options %%}
          <label for="option_{{b.0}}"><input type="checkbox" name="env" {%% if b.0 in current_options %%}checked {%% endif %%}value="{{b.0}}" id="option_{{b.0}}"/>&nbsp;&nbsp;{{b.1}}</label><br>
          {%% endfor %%}
          </p>
          {%% endif %%}
          <p><b>%s</b><br>
          <input type="radio" id="plantype1" name="plantype" {%% if plantype != '2' %%}checked {%% endif %%}value="1"/>
          <label for="plantype1">%s
          <span class="fa fa-question-circle" style="display:inline-block;"></span></label><br>
          <input type="radio" id="plantype2" name="plantype" {%% if plantype == '2' %%}checked {%% endif %%}value="2"/>
          <label for="plantype2">%s
              <span class="fa fa-question-circle" style="display:inline-block;"></span></label><br>
              </p>
              <p>
              <b>{%% filter capfirst %%}%s{%% endfilter %%}</b><br>
              <label for="cb4"><input type="checkbox" name="constraint" {%% if capacityconstrained %%}checked {%% endif %%}value="4" id="cb4"/>&nbsp;&nbsp;%s</label><br>
              <label for="cb1"><input type="checkbox" name="constraint" {%% if leadtimeconstrained %%}checked {%% endif %%}value="1" id="cb1"/>&nbsp;&nbsp;%s</label><br>
              <label for="cb8"><input type="checkbox" name="constraint" {%% if fenceconstrained %%}checked {%% endif %%}value="8" id="cb8"/>&nbsp;&nbsp;%s</label><br>
              </p>
            </td>
          </tr>
          </table>
        </form>
      """
                % (
                    force_str(
                        _(
                            "Load all input data, run the planning algorithm, and export the results."
                        )
                    ),
                    force_str(_("optional planning steps")),
                    force_str(_("Plan type")),
                    force_str(
                        _(
                            '<span data-toggle="tooltip" data-placement="top" data-html="true" data-original-title="Generate a supply plan that respects all constraints.<br>In case of shortages the demand is planned late or short.">Constrained plan</span>'
                        )
                    ),
                    force_str(
                        _(
                            '<span data-toggle="tooltip" data-placement="top" data-html="true" data-original-title="Generate a supply plan that shows material, capacity and operation problems that prevent the demand from being planned in time.<br>The demand is always met completely and on time.">Unconstrained plan</span>'
                        )
                    ),
                    force_str(_("constraints")),
                    force_str(_("Capacity: respect capacity limits")),
                    force_str(_("Lead time: do not plan in the past")),
                    force_str(
                        _("Release fence: do not plan within the release time window")
                    ),
                )
            )
            return template.render(context)
        else:
            return None
