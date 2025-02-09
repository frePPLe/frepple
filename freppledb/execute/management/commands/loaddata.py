#
# Copyright (C) 2018 by frePPLe bv
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

from django.apps import apps
from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands import loaddata
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import User, addAttributesFromDatabase
from freppledb.common.middleware import _thread_locals
from freppledb.common.report import getCurrentDate
from freppledb.execute.models import Task

class Command(loaddata.Command):
    @staticmethod
    def getHTML(request):
        # Loop over all fixtures of all apps and directories
        fixtures = set()
        folders = list(settings.FIXTURE_DIRS)
        for app in apps.get_app_configs():
            if not app.name.startswith("django"):
                folders.append(
                    os.path.join(os.path.dirname(app.path), app.label, "fixtures")
                )
        for f in folders:
            try:
                for root, dirs, files in os.walk(f):
                    for i in files:
                        if i.endswith(".json"):
                            fixtures.add(i.split(".")[0])
            except Exception:
                pass  # Silently ignore failures
        fixtures = sorted(fixtures)

        return render_to_string(
            "commands/loaddata.html", {"fixtures": fixtures}, request=request
        )

    title = _("Load a dataset")
    index = 1800
    help_url = "command-reference.html#loaddata"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--task",
            dest="task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument("--user", dest="user", help="User running the command")

    def handle(self, *fixture_labels, **options):
        # get the database object
        database = options["database"]
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)

        now = datetime.now()
        task = None
        old_thread_locals = getattr(_thread_locals, "database", None)
        try:
            setattr(_thread_locals, "database", database)
            # Initialize the task
            if options["task"]:
                try:
                    task = Task.objects.all().using(database).get(pk=options["task"])
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name != "loaddata"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
                task.processid = os.getpid()
                task.save(
                    using=database, update_fields=["started", "status", "processid"]
                )
            else:
                if options["user"]:
                    try:
                        user = (
                            User.objects.all()
                            .using(database)
                            .get(username=options["user"])
                        )
                    except Exception:
                        raise CommandError("User '%s' not found" % options["user"])
                else:
                    user = None
                task = Task(
                    name="loaddata",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                    arguments=" ".join(fixture_labels),
                )
                task.processid = os.getpid()
                task.save(using=database)

            # Excecute the standard django command
            super().handle(*fixture_labels, **options)

            # Modify the database tables to reflect all attributes
            if database == DEFAULT_DB_ALIAS:
                addAttributesFromDatabase()

            # Modify the forecastplan table to reflect all measures
            if "freppledb.forecast" in settings.INSTALLED_APPS:
                from freppledb.forecast.models import ForecastPlan

                ForecastPlan.refreshTableColumns(database)

            # if the fixture doesn't contain the 'demo' word, let's not apply loaddata post-treatments
            if "FREPPLE_TEST" in os.environ:
                return
            if not any("demo" in f.lower() for f in fixture_labels):
                # Task update
                task.status = "Done"
                task.finished = datetime.now()
                task.processid = None
                task.save(using=database, update_fields=["status", "finished"])
                return

            with transaction.atomic(using=database, savepoint=False):
                if self.verbosity > 2:
                    print("updating fixture to current date")

                offset = (datetime.now() - getCurrentDate(database)).days

                # update currentdate to now
                cursor = connections[database].cursor()
                cursor.execute(
                    """
                    update common_parameter set value = 'today' where name = 'currentdate'
                    """
                )

                # update demand due dates
                cursor.execute(
                    """
                    update demand set due = due + %s * interval '1 day'
                    """,
                    (offset,),
                )

                # update PO/DO/MO due dates
                cursor.execute(
                    """
                      update operationplan
                      set startdate = startdate + %s * interval '1 day',
                          enddate = enddate + %s * interval '1 day'
                    """,
                    2 * (offset,),
                )

                # Update archive tables
                if "freppledb.archive" in settings.INSTALLED_APPS:
                    # ax_manager table needs to be updated in the right order.
                    # Otherwise we can get duplicates.
                    cursor.execute(
                        "select snapshot_date from ax_manager order by snapshot_date %s"
                        % ("asc" if offset < 0 else "desc")
                    )
                    for ax in cursor.fetchall():
                        cursor.execute(
                            """
                            update ax_manager
                            set snapshot_date = snapshot_date + %s * interval '1 day'
                            where snapshot_date = %s
                            """,
                            (offset, ax[0]),
                        )
                    cursor.execute(
                        """
                        update ax_buffer set
                          snapshot_date_id = snapshot_date_id + %s * interval '1 day'
                        """,
                        (offset,),
                    )
                    cursor.execute(
                        """
                        update ax_demand set
                          snapshot_date_id = snapshot_date_id + %s * interval '1 day',
                          due = due + %s * interval '1 day',
                          deliverydate = deliverydate + %s * interval '1 day'
                        """,
                        3 * (offset,),
                    )
                    cursor.execute(
                        """
                        update ax_operationplan set
                          snapshot_date_id = snapshot_date_id + %s * interval '1 day',
                          startdate = startdate + %s * interval '1 day',
                          enddate = enddate + %s * interval '1 day',
                          due = due + %s * interval '1 day'
                        """,
                        4 * (offset,),
                    )

                # Task update
                task.status = "Done"
                task.finished = datetime.now()
                task.processid = None
                task.save(using=database, update_fields=["status", "finished"])

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
                task.processid = None
                task.save(
                    using=database, update_fields=["status", "finished", "message"]
                )
            raise CommandError("%s" % e)

        finally:
            setattr(_thread_locals, "database", old_thread_locals)
