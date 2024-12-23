#
# Copyright (C) 2010-2019 by frePPLe bv
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

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections

from freppledb.execute.models import Task
from freppledb.common.models import User, Scenario
from freppledb import __version__


class Command(BaseCommand):
    help = """
      This command releases a scenario. It changes its status from "In use" to "Free".
      """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command"),

        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument(
            "--database", default=DEFAULT_DB_ALIAS, help="The scenario to be released."
        )

    def handle(self, **options):
        if options["user"]:
            try:
                user = User.objects.all().get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        # Synchronize the scenario table with the settings
        Scenario.syncWithSettings()

        now = datetime.now()
        task = None
        database = options["database"]
        if "task" in options and options["task"]:
            try:
                task = Task.objects.all().using(database).get(pk=options["task"])
            except Exception:
                raise CommandError("Task identifier not found")
            if (
                task.started
                or task.finished
                or task.status != "Waiting"
                or task.name != "scenario_release"
            ):
                raise CommandError("Invalid task identifier")
            task.status = "0%"
            task.started = now
        else:
            task = Task(
                name="scenario_release",
                submitted=now,
                started=now,
                status="0%",
                user=user,
            )
        task.processid = os.getpid()
        task.save(using=database)

        # Validate the arguments
        try:
            releasedScenario = None
            try:
                releasedScenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(
                    pk=database
                )
            except Exception:
                raise CommandError(
                    "No destination database defined with name '%s'" % database
                )
            if database == DEFAULT_DB_ALIAS:
                raise CommandError("Production scenario cannot be released.")
            if releasedScenario.status != "In use":
                raise CommandError("Scenario to release is not in use")

            # Update the scenario table, set it free in the production database
            releasedScenario.status = "Free"
            releasedScenario.lastrefresh = datetime.today()
            releasedScenario.save(using=DEFAULT_DB_ALIAS)

            # Update the user table, remove the scenario from the user's list
            with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
                cursor.execute(
                    """
                    update common_user 
                    set databases = array_remove(databases, %s) 
                    where %s = any(databases)
                    """,
                    (database, database),
                )

            # Emptying the data of the released scenario
            try:
                with connections[database].cursor() as cursor:
                    cursor.execute(
                        "select tablename from pg_tables where schemaname='public'"
                    )
                    for t in cursor.fetchall():
                        cursor.execute("drop table if exists %s cascade" % t)
                task = None
            except Exception as e:
                # Silently continue if data cleansing failes
                print("Failed to empty the scenario data: %s" % (e,))

            # Killing webservice
            if "freppledb.webservice" in settings.INSTALLED_APPS:
                management.call_command("stopwebservice", force=True, database=database)

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            if releasedScenario and releasedScenario.status == "Busy":
                releasedScenario.status = "Free"
                releasedScenario.save(using=DEFAULT_DB_ALIAS)
            raise e

        finally:
            if task:
                task.processid = None
                task.save(using=database)

    index = 1501

    @staticmethod
    def getHTML(request):
        # Returning an empty string will:
        #  - add the task to the task list dropdown for the task scheduler
        #  - hide it as a panel in the main task list
        return ""
