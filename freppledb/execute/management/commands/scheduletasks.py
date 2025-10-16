#
# Copyright (C) 2020 by frePPLe bv
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
from importlib import import_module
import os
from random import uniform
import re
from psycopg2.errors import SerializationFailure
from threading import Lock, Timer
import time
import zoneinfo

from django.conf import settings
from django.core.management import get_commands
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DEFAULT_DB_ALIAS, connections
from django.db.utils import OperationalError
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from ...models import ScheduledTask, Task
from freppledb import __version__
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User, Scenario
from freppledb.common.report import GridReport
from freppledb.common.utils import get_databases, sendEmail
from .runworker import launchWorker, runTask


class TaskScheduler:
    def __init__(self):
        self.sched = {}
        self.mutex = Lock()

    def start(self):
        with self.mutex:
            for db in (
                Scenario.objects.using(DEFAULT_DB_ALIAS)
                .filter(status="In use", info__has_key="has_schedule")
                .only("name")
            ):
                try:
                    with transaction.atomic(using=db.name, savepoint=False):
                        with connections[db.name].cursor() as cursor:
                            cursor.execute(
                                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
                            )
                            for s in (
                                ScheduledTask.objects.all()
                                .using(db.name)
                                .order_by("name")
                                .select_for_update(skip_locked=True)
                            ):
                                # Calculation of the next run is included in the save method
                                s.save(using=db.name, update_fields=["next_run"])
                except (SerializationFailure, OperationalError):
                    # Concurrent access by different webserver processes can happen.
                    # In that case, one of the transactions will abort. That's fine.
                    pass
        self.waitNextEvent()

    def waitNextEvent(self, database=None):
        with self.mutex:
            now = datetime.now()
            dbs = (
                Scenario.objects.using(DEFAULT_DB_ALIAS)
                .filter(status="In use", info__has_key="has_schedule")
                .only("name")
            )
            if database:
                dbs.filter(name=database)
            for db in dbs:
                t = (
                    ScheduledTask.objects.all()
                    .using(db.name)
                    .filter(next_run__isnull=False)
                    .order_by("next_run")
                    .only("next_run")
                    .first()
                )
                if t:
                    cur_schedule = self.sched.get(db.name, None)
                    if cur_schedule and cur_schedule["time"] > t.next_run:
                        cur_schedule["timer"].cancel()
                    self.sched[db.name] = {
                        "timer": Timer(
                            (t.next_run - now).total_seconds(),
                            self._tasklauncher,
                            kwargs={"database": db.name},
                        ),
                        "time": t.next_run,
                    }
                    self.sched[db.name]["timer"].start()

    @staticmethod
    def _tasklauncher(database=DEFAULT_DB_ALIAS):
        # Random delay to avoid races
        time.sleep(uniform(0.0, 0.200))

        # Note: use transaction and select_for_update to handle concurrent access
        now = datetime.now()
        created = False
        try:
            with transaction.atomic(using=database, savepoint=False):
                with connections[database].cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                    for schedule in (
                        ScheduledTask.objects.all()
                        .using(database)
                        .filter(next_run__isnull=False, next_run__lte=now)
                        .order_by("next_run", "name")
                        .select_for_update(skip_locked=True)
                    ):
                        Task(
                            name="scheduletasks",
                            submitted=now,
                            status="Waiting",
                            user=schedule.user,
                            arguments="--schedule='%s'" % schedule.name,
                        ).save(using=database)
                        # Calculation of the next run is included in the save method
                        schedule.save(using=database, update_fields=["next_run"])
                        created = True

            # Reschedule to run this task again at the next date
            if database in scheduler.sched:
                del scheduler.sched[database]
            scheduler.waitNextEvent(database=database)

            # Synchronously run the worker process
            if created:
                launchWorker(database)

        except (SerializationFailure, OperationalError):
            # Concurrent access by different webserver processes can happen.
            # In that case, one of the transactions will abort. That's fine.
            pass

    def status(self, msg=""):
        print("Scheduler status:", msg)
        for db, tm in self.sched.items():
            print("    ", tm["time"], db)


scheduler = TaskScheduler()


class Command(BaseCommand):
    help = "Executes a group of tasks in sequence."
    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Specify the database to run in.",
        )
        parser.add_argument("--schedule", help="Name of the scheduled task to execute")
        parser.add_argument("--user", dest="user", help="User running the command")
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )

    def handle(self, *args, **options):
        if not options["schedule"]:
            # Executing Without schedule argument is a legacy from the
            # days the at-command was used to execute the schedule.
            return
        database = options["database"]
        if database not in get_databases():
            raise CommandError("No database settings known for '%s'" % database)
        try:
            schedule = ScheduledTask.objects.using(database).get(
                name=options["schedule"]
            )
        except ScheduledTask.DoesNotExist:
            raise CommandError(
                "No scheduled task found with name '%s' " % options["schedule"]
            )
        if "user" in options and options["user"]:
            try:
                user = User.objects.all().using(database).get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        task = None
        now = datetime.now()
        old_thread_locals = getattr(_thread_locals, "database", None)
        try:
            setattr(_thread_locals, "database", database)
            # Initialize the task
            if "task" in options and options["task"]:
                try:
                    task = Task.objects.all().using(database).get(pk=options["task"])
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name != "scheduletasks"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
                task.processid = os.getpid()
            else:
                task = Task(
                    name="scheduletasks",
                    submitted=now,
                    started=now,
                    status="0%",
                    arguments="--schedule='%s'" % schedule.name,
                    user=user,
                    processid=os.getpid(),
                )
            task.save(using=database)

            # The loop that actually executes the tasks
            tasklist = schedule.data.get("tasks", [])
            stepcount = len(tasklist)
            idx = 1
            failed = []
            for step in tasklist:
                steptask = Task(
                    name=step.get("name"),
                    submitted=datetime.now(),
                    arguments=step.get("arguments", ""),
                    user=user,
                    status="Waiting",
                )
                steptask.save(using=database)
                Task.objects.all().using(database).filter(pk=task.id).update(
                    message="Running task %s as step %s of %s"
                    % (steptask.id, idx, stepcount),
                    status="%d%%" % int((idx - 1) * 100.0 / stepcount),
                )
                runTask(steptask, database)

                # Check the status
                steptask = Task.objects.all().using(database).get(pk=steptask.id)
                if self.getStepTaskStatus(steptask) == "Failed":
                    failed.append(str(steptask.id))
                    if step.get("abort_on_failure", False):
                        task = Task.objects.all().using(database).get(pk=task.id)
                        task.message = "Failed at step %s of %s" % (idx, len(tasklist))
                        task.status = "Failed"
                        task.finished = datetime.now()
                        task.save(
                            using=database,
                            update_fields=["message", "status", "finished"],
                        )
                        raise Exception(task.message)
                idx += 1

            # Reread the task from the database and update it
            task = Task.objects.all().using(database).get(pk=task.id)
            task.processid = None
            if failed or not self.getScheduledTaskStatus(task, database):
                task.status = "Failed"
                if failed:
                    task.message = "Failed at tasks: %s" % ", ".join(failed)
                else:
                    task.message = task.check_message
                raise Exception(task.message)
            else:
                task.status = "Done"
                task.message = ""
            task.finished = datetime.now()
            task.save(
                using=database,
                update_fields=["message", "status", "finished", "processid"],
            )

            # Email on success
            if schedule.email_success:
                correctedRecipients = []
                for r in schedule.email_success.split(","):
                    r = r.strip()
                    if r and re.fullmatch(r"[^@]+@[^@]+\.[^@]+", r):
                        correctedRecipients.append(r.strip())
                if not settings.EMAIL_HOST:
                    task.message = (
                        "Can't send success e-mail: missing SMTP configuration"
                    )
                    task.save(
                        using=database,
                        update_fields=["message", "status", "finished", "processid"],
                    )
                elif not correctedRecipients:
                    task.message = "Can't send success e-mail: invalid recipients"
                    task.save(
                        using=database,
                        update_fields=["message", "status", "finished", "processid"],
                    )
                else:
                    try:
                        body = [f"Task {task.id} completed succesfully.\n"]
                        body_html = [f"Task {task.id} completed succesfully.<br>"]
                        if getattr(settings, "EMAIL_URL_PREFIX", None):
                            url = f"{settings.EMAIL_URL_PREFIX}{"" if database==DEFAULT_DB_ALIAS else "/%s" % database}/execute/"
                            body.append(f"Check the logs at {url}\n")
                            body_html.append(
                                f'Check the logs <a style="font-weight:bold" href="{url}">here</a><br>'
                            )
                        body.append("Thanks for using frepple!\n")
                        body_html.append("Thanks for using frepple!<br>")
                        sendEmail(
                            to=correctedRecipients,
                            subject=(
                                f"FrePPLe successfully executed {schedule.name}"
                                if database == DEFAULT_DB_ALIAS
                                else f"FrePPLe successfully executed {schedule.name} on {database}"
                            ),
                            body="\n".join(body),
                            body_html="<br>".join(body_html),
                        )
                    except Exception as e:
                        task.message = "Can't send success e-mail: %s" % e
                        task.save(
                            using=database,
                            update_fields=[
                                "message",
                                "status",
                                "finished",
                                "processid",
                            ],
                        )

        except Exception as e:
            if task:
                task = Task.objects.all().using(database).get(pk=task.id)
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
                task.processid = None
                task.save(
                    using=database,
                    update_fields=["message", "status", "finished", "processid"],
                )

                # Email on failure
                if schedule.email_failure:
                    correctedRecipients = []
                    for r in schedule.email_failure.split(","):
                        r = r.strip()
                        if r and re.fullmatch(r"[^@]+@[^@]+\.[^@]+", r):
                            correctedRecipients.append(r.strip())
                    if not settings.EMAIL_HOST:
                        task.message = (
                            "Can't send failure e-mail: missing SMTP configuration"
                        )
                        task.save(
                            using=database,
                            update_fields=[
                                "message",
                                "status",
                                "finished",
                                "processid",
                            ],
                        )
                    elif not correctedRecipients:
                        task.message = "Can't send failure e-mail: invalid recipients"
                        task.save(
                            using=database,
                            update_fields=[
                                "message",
                                "status",
                                "finished",
                                "processid",
                            ],
                        )
                    else:
                        try:
                            body = [f"Task {task.id} failed.\n"]
                            body_html = [f"Task {task.id} failed.<br>"]
                            if getattr(settings, "EMAIL_URL_PREFIX", None):
                                url = f"{settings.EMAIL_URL_PREFIX}{"" if database==DEFAULT_DB_ALIAS else "/%s" % database}/execute/"
                                body.append(f"Check the logs at {url}\n")
                                body_html.append(
                                    f'Check the logs <a style="font-weight:bold" href="{url}">here</a><br>'
                                )
                            body.append("Thanks for using frepple!\n")
                            body_html.append("Thanks for using frepple!<br>")
                            sendEmail(
                                to=correctedRecipients,
                                subject=(
                                    f"FrePPLe failed executing {schedule.name}"
                                    if database == DEFAULT_DB_ALIAS
                                    else f"FrePPLe failed executing {schedule.name} on {database}"
                                ),
                                body="\n".join(body),
                                body_html="<br>".join(body_html),
                            )
                        except Exception as e:
                            task.message = "Can't send failure e-mail: %s" % e
                            task.save(
                                using=database,
                                update_fields=[
                                    "message",
                                    "status",
                                    "finished",
                                    "processid",
                                ],
                            )
            raise e

        finally:
            setattr(_thread_locals, "database", old_thread_locals)

    def getStepTaskStatus(self, steptask):
        """
        This methods allows customizing pass-fail criteria of tasks.
        """
        return steptask.status

    def getScheduledTaskStatus(self, task, database):
        """
        This methods allows customizing pass-fail criteria of a complete scheduled task.
        """
        return True

    # accordion template
    title = _("Group and schedule tasks")
    index = 500

    help_url = "command-reference.html#scheduletasks"

    @classmethod
    def getHTML(cls, request, widget=False):
        try:
            commands = []
            for commandname, appname in get_commands().items():
                if commandname != "scheduletasks":
                    try:
                        cmd = getattr(
                            import_module(
                                "%s.management.commands.%s" % (appname, commandname)
                            ),
                            "Command",
                        )
                        if getattr(cmd, "index", -1) >= 0 and getattr(
                            cmd, "getHTML", None
                        ):
                            commands.append((cmd.index, commandname))
                    except Exception:
                        pass
            commands = [i[1] for i in sorted(commands)]
            offset = GridReport.getTimezoneOffset(request)
            schedules = [
                s.adjustForTimezone(offset)
                for s in ScheduledTask.objects.all()
                .using(request.database)
                .order_by("name")
            ]
            if not widget:
                schedules.append(ScheduledTask())  # Add an empty template
            return render_to_string(
                "commands/scheduletasks.html",
                {
                    "schedules": schedules,
                    "commands": commands,
                    "widget": widget,
                    "timezones": sorted(
                        [
                            (datetime.now(zoneinfo.ZoneInfo(i)).strftime("%z"), i)
                            for i in zoneinfo.available_timezones()
                        ]
                    ),
                    "default_timezone": settings.TIME_ZONE,
                },
                request=request,
            )
        except Exception as e:
            print(e)
