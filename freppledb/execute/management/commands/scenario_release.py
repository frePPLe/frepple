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
import subprocess


from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from freppledb.execute.models import Task, ScheduledTask
from freppledb.common.models import User, Scenario
from freppledb import __version__


class Command(BaseCommand):
    help = """
  This command copies the contents of a database into another.
  The original data in the destination database are lost.

  The pg_dump and psql commands need to be in the path, otherwise
  this command will fail.
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
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="unused parameter for this command",
        )

        parser.add_argument("destination", help="database to release")

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
        if "task" in options and options["task"]:
            try:
                task = (
                    Task.objects.all().using(DEFAULT_DB_ALIAS).get(pk=options["task"])
                )
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
        task.save(using=DEFAULT_DB_ALIAS)

        # Validate the arguments
        destination = options["destination"]
        destinationscenario = None
        try:
            task.arguments = "%s" % (destination,)
            task.save(using=DEFAULT_DB_ALIAS)
            try:
                destinationscenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(
                    pk=destination
                )
            except Exception:
                raise CommandError(
                    "No destination database defined with name '%s'" % destination
                )
            if destinationscenario.status != "In use":
                raise CommandError("Scenario to release is not in use")

            if destination == DEFAULT_DB_ALIAS:
                raise CommandError("Production scenario cannot be released")

            # Update the scenario table, set it free in the production database
            destinationscenario.status = "Free"
            destinationscenario.lastrefresh = datetime.today()
            destinationscenario.save(using=DEFAULT_DB_ALIAS)

            # Killing webservice
            if "freppledb.webservice" in settings.INSTALLED_APPS:
                management.call_command(
                    "stopwebservice", force=True, database=destination
                )

            # Logging message
            task.processid = None
            task.status = "Done"
            task.finished = datetime.now()

            # Update the task in the destination database
            task.message = "Scenario %s released" % (destination,)
            task.save(using=DEFAULT_DB_ALIAS)

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            if destinationscenario and destinationscenario.status == "Busy":
                if destination == DEFAULT_DB_ALIAS:
                    destinationscenario.status = "In use"
                else:
                    destinationscenario.status = "Free"
                destinationscenario.save(using=DEFAULT_DB_ALIAS)
            raise e

        finally:
            if task:
                task.processid = None
                task.save(using=DEFAULT_DB_ALIAS)
