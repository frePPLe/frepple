#
# Copyright (C) 2026 by frePPLe bv
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

import ctypes
from datetime import datetime, timedelta
import os
from pathlib import Path
from random import randint, uniform
import shutil
import site
import subprocess
import sys
from threading import Lock, Timer
import signal
import time

# Autodetect Python virtual enviroment
venv = os.environ.get("VIRTUAL_ENV", None)
if not venv:
    curdir = os.path.dirname(os.path.realpath(__file__))
    for candidate in (
        # Development layout
        os.path.join(curdir, "venv"),
        # Linux install layout
        os.path.join(curdir, "..", "share", "frepple", "venv"),
    ):
        if os.path.isfile(os.path.join(candidate, "bin", "python3")) and os.path.isfile(
            os.path.join(candidate, "bin", "activate")
        ):
            os.environ["VIRTUAL_ENV"] = candidate
            venv = candidate
            break

# Activate Python virtual environment
if venv:
    prev_length = len(sys.path)
    os.environ["PATH"] = os.pathsep.join(
        [os.path.join(venv, "bin")] + os.environ.get("PATH", "").split(os.pathsep)
    )
    path = os.path.realpath(
        os.path.join(
            venv,
            "lib",
            "python%d.%d" % sys.version_info[:2],
            "site-packages",
        )
    )
    site.addsitedir(path)
    sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]
    sys.real_prefix = sys.prefix
    sys.prefix = venv

# Assure frePPLe is found in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")

# Boot Django
import django

django.setup()

from psycopg2.errors import SerializationFailure

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DEFAULT_DB_ALIAS, connections
from django.db.utils import OperationalError

from freppledb import __version__
from freppledb.common.models import Scenario
from freppledb.execute.models import ScheduledTask, Task
from freppledb.execute.management.commands.runworker import launchWorker


class TaskScheduler:
    _instance = None
    _mutex = Lock()

    def __init__(self):
        self.sched = {}

    def __new__(cls, *args, **kwargs):
        # Singleton class, only 1 instance is created per process
        if cls._instance is None:
            with cls._mutex:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def start(self):
        with self._mutex:
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
                    # Concurrent access by different processes can happen.
                    # In that case, one of the transactions will abort. That's fine.
                    pass
        self.waitNextEvent()

    def waitNextEvent(self, database=None):
        with self._mutex:
            now = datetime.now()
            dbs = (
                Scenario.objects.using(DEFAULT_DB_ALIAS)
                .filter(status="In use", info__has_key="has_schedule")
                .only("name")
            )
            if database:
                dbs = dbs.filter(name=database)
            for db in dbs:
                t = (
                    ScheduledTask.objects.all()
                    .using(db.name)
                    .filter(next_run__isnull=False)
                    .order_by("next_run")
                    .only("next_run")
                    .first()
                )
                waiting_for = (t.next_run - now).total_seconds() if t else 0
                if waiting_for > 0:
                    cur_schedule = self.sched.get(db.name, None)
                    if not cur_schedule or cur_schedule["time"] > t.next_run:
                        if cur_schedule:
                            cur_schedule["timer"].cancel()
                        self.sched[db.name] = {
                            "timer": Timer(
                                waiting_for,
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

        # Keep things tidy
        Task.removeUnhealthyTasks(database)

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
            scheduler.sched.pop(database, None)
            scheduler.waitNextEvent(database=database)

            # Spawn the worker process
            if created:
                launchWorker(database)

        except (SerializationFailure, OperationalError):
            # Concurrent access by different webserver processes can happen.
            # In that case, one of the transactions will abort. That's fine.
            pass
        finally:
            connections[database].close()

    def handle_reload(self, signum, frame):
        self.waitNextEvent()

    def handle_shutdown(self, signum, frame):
        sys.exit(0)

    def status(self, msg=""):
        print("Scheduler status:", msg)
        for db, tm in self.sched.items():
            print("    ", tm["time"], db)

    @staticmethod
    def schedule(
        hour=None,
        minute=None,
        second=None,
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=True,
        friday=True,
        saturday=True,
        sunday=True,
    ):
        """Decorator that runs a function at the given time on the specified weekdays."""
        enabled_days = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
        fixed_hour = hour if hour is not None else randint(0, 23)
        fixed_minute = minute if minute is not None else randint(0, 59)
        fixed_second = second if second is not None else randint(0, 59)

        def decorator(func):
            def _schedule_next():
                now = datetime.now()
                for days_ahead in range(1, 8):
                    candidate = (now + timedelta(days=days_ahead)).replace(
                        hour=fixed_hour,
                        minute=fixed_minute,
                        second=fixed_second,
                        microsecond=0,
                    )
                    if enabled_days[candidate.weekday()]:
                        Timer((candidate - now).total_seconds(), _run).start()
                        return

            def _run():
                try:
                    func()
                except Exception as e:
                    print(f"Error running scheduled function {func.__name__}: {e}")
                finally:
                    _schedule_next()

            _schedule_next()
            return func

        return decorator


scheduler = TaskScheduler()

# Set the process name
ctypes.CDLL("libc.so.6").prctl(15, "frepple-sched".encode("utf-8"), 0, 0, 0)

# Install signal handlers
signal.signal(signal.SIGTERM, scheduler.handle_shutdown)
signal.signal(signal.SIGUSR1, scheduler.handle_reload)


# Run logrotate daily sometime in the first minute after midnight
if (
    shutil.which("logrotate")
    and os.access("/etc/frepple/logrotate.conf", os.R_OK)
    and os.access("/var/log/frepple", os.W_OK)
):

    @scheduler.schedule(hour=0, minute=0)
    def logrotate():
        subprocess.run(
            ["logrotate", "-f", "/etc/frepple/logrotate.conf", "--state", "/dev/null"],
            check=True,
        )
        cutoff_compress = time.time() + 9 + 24 * 3600
        for path in Path("/var/log/frepple").glob("*.log"):
            if path.stat().st_mtime < cutoff_compress:
                print("Compressing log file", path)
                subprocess.run(["gzip", str(path)], check=True)


# Wait indefinitely for events
scheduler.start()
try:
    while True:
        signal.pause()
except KeyboardInterrupt:
    pass
