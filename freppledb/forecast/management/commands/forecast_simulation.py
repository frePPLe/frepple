#
# Copyright (C) 2023 by frePPLe bv
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
from dateutil.parser import parse
import os

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

from freppledb import VERSION
from freppledb.common.models import User, Parameter, BucketDetail
from freppledb.common.utils import get_databases
from freppledb.execute.models import Task


class Command(BaseCommand):
    help = """
      Runs a simulation to measure the historical forecast accuracy.

      The simulation sets back to "current date - N periods" ago. It computes the
      forecast, and compares the actual orders and forecast in period "current
      date - N + 1".
      The process is then repeated for period "current date - N + 1" period to
      estimate the forecast error in period "current date - N + 2".
      The final output is thus an estimation of the forecast accuracy over time.

      Warning: During the simulation, the current_date parameter is changing.
      No other calculation processes and user interface actions should be run
      during the simulation, as they would incorrectly use the manipulated
      current_date value.
      """

    requires_system_checks = []

    def get_version(self):
        return VERSION

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--history",
            type=int,
            default=12,
            help="Number of periods in the past to step back",
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to load data from and export results into",
        )
        parser.add_argument(
            "--task",
            dest="task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )

    def handle(self, **options):
        # Pick up the options
        database = options["database"]
        if database not in get_databases():
            raise CommandError("No database settings known for '%s'" % database)
        if options["user"]:
            try:
                user = User.objects.all().using(database).get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        now = datetime.now()
        task = None
        currentdate = None
        param = None
        created = False
        try:
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
                    or task.name != "forecast_simulation"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(
                    name="forecast_simulation",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                )

            # Validate options
            history = int(options["history"])
            if history < 0:
                raise ValueError("Invalid history: %s" % options["history"])
            task.arguments = "--history=%d" % history

            # Log task
            task.processid = os.getpid()
            task.save(using=database)

            # Get current date
            param, created = (
                Parameter.objects.all()
                .using(database)
                .get_or_create(name="currentdate")
            )
            currentdate = param.value
            try:
                curdate = parse(param.value)
            except Exception:
                curdate = datetime.now().replace(microsecond=0)

            # Loop over all buckets in the simulation horizon
            cal = Parameter.getValue("forecast.calendar", database)
            bckt_list = [
                i
                for i in BucketDetail.objects.all()
                .using(database)
                .filter(bucket__name=cal, startdate__lt=curdate)
                .order_by("startdate")
            ]
            bckt_list = bckt_list[-history:]
            if not bckt_list:
                raise Exception("No calendar buckets found")
            idx = 0
            for bckt in bckt_list:
                # Start message
                task.status = "%.0f%%" % (100.0 * idx / history)
                task.message = "Simulating period %s" % bckt.startdate.date()
                task.save(using=database)
                idx += 1

                # Update currentdate parameter
                param.value = bckt.startdate.date().strftime("%Y-%m-%d %H:%M:%S")
                param.save(using=database)

                # Run simulation
                management.call_command(
                    "runplan", database=database, env="fcst,nowebservice"
                )

                # Uncomment the next line to stop the simulation here and check the
                # intermediate results in the database
                # input("finished %s" % bckt.startdate.date())

            # Task update
            task.status = "Done"
            task.message = "Simulated from %s till %s" % (
                bckt_list[0].startdate.date(),
                bckt_list[-1].startdate.date(),
            )
            task.finished = datetime.now()

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            raise e

        finally:
            # Restore original current date parameter
            if created:
                Parameter.objects.all().using(database).get(name="currentdate").delete()
            elif param:
                param.value = currentdate
                param.save(using=database)

            # Final task status
            if task:
                task.processid = None
                task.save(using=database)
