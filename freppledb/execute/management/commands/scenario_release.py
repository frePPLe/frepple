#
# Copyright (C) 2010-2019 by frePPLe bv
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

from datetime import datetime
import os

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.execute.models import Task
from freppledb.common.models import User, Scenario
from freppledb import __version__


class Command(BaseCommand):
    help = """
      This command releases a scenario. It changes its status from "In use" to "Free".
      """

    requires_system_checks = False

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

            # Killing webservice
            if "freppledb.webservice" in settings.INSTALLED_APPS:
                management.call_command("stopwebservice", force=True, database=database)

            # Logging message
            task.processid = None
            task.status = "Done"
            task.finished = datetime.now()

            # Update the task in the destination database
            task.message = "Scenario %s released" % (database,)
            task.save(using=database)

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
