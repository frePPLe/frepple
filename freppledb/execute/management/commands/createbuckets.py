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
from datetime import timedelta, datetime, date

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.formats import date_format
from django.template.loader import render_to_string

from freppledb.common.middleware import _thread_locals
from freppledb.common.models import Bucket, BucketDetail
from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb.common.localization import parseLocalizedDateTime
from freppledb import __version__


class Command(BaseCommand):
    help = """
      This command initializes the date bucketization table in the database.
      """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            help="Unused deprecated argument",
        )
        parser.add_argument(
            "--end",
            help="Unused deprecated argument",
        )
        parser.add_argument(
            "--weekstart",
            type=int,
            default=1,
            choices=[0, 1, 2, 3, 4, 5, 6],
            help="First day of a week: 0=sunday, 1=monday (default), 2=tuesday, 3=wednesday, 4=thursday, 5=friday, 6=saturday",
        ),
        parser.add_argument(
            "--format-day",
            default="%Y-%m-%d",
            help="Format template for a daily bucket",
        ),
        parser.add_argument(
            "--format-week",
            default="%y W%W",
            help="Format template for a weekly bucket",
        ),
        parser.add_argument(
            "--format-month",
            default="%b %y",
            help="Format template for a monthly bucket",
        ),
        parser.add_argument(
            "--format-quarter",
            default="%y Q%q",
            help="Format template for a quarterly bucket",
        ),
        parser.add_argument(
            "--format-year", default="%Y", help="Format template for a yearly bucket"
        ),
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to populate date information into",
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )

    def formatDate(self, curdate, template):
        fmt = template
        if "%q" in fmt:
            month = int(curdate.strftime("%m"))  # an integer in the range 1 - 12
            quarter = (month - 1) // 3 + 1  # an integer in the range 1 - 4
            fmt = fmt.replace("%q", str(quarter))
        return curdate.strftime(fmt)

    def handle(self, **options):
        # Make sure the debug flag is not set!
        # When it is set, the django database wrapper collects a list of all sql
        # statements executed and their timings. This consumes plenty of memory
        # and cpu time.
        tmp_debug = settings.DEBUG
        settings.DEBUG = False

        # Pick up the options
        weekstart = int(options["weekstart"])
        database = options["database"]
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)
        if options["user"]:
            try:
                user = User.objects.all().using(database).get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None
        self.isoweeknumber = "%V" in options["format_week"]

        now = datetime.now()
        task = None
        old_thread_locals = getattr(_thread_locals, "database", None)
        try:
            # Initialize the task
            setattr(_thread_locals, "database", database)
            if options["task"]:
                if options["task"] > 0:
                    try:
                        task = (
                            Task.objects.all().using(database).get(pk=options["task"])
                        )
                    except Task.DoesNotExist:
                        raise CommandError("Task identifier not found")
                    if (
                        task.started
                        or task.finished
                        or task.status != "Waiting"
                        or task.name not in ("frepple_createbuckets", "createbuckets")
                    ):
                        raise CommandError("Invalid task identifier")
                    task.status = "0%"
                    task.started = now
            else:
                task = Task(
                    name="createbuckets",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                    arguments="--weekstart=%s" % (weekstart),
                )
            if task:
                task.processid = os.getpid()
                task.save(using=database)

            # Hardcoded horizon
            curdate = datetime(2017, 1, 1)
            enddate = datetime(2030, 1, 1)

            with transaction.atomic(using=database, savepoint=False):
                # Delete previous contents
                with connections[database].cursor() as cursor:
                    cursor.execute(
                        "delete from common_bucketdetail where bucket_id in ('year','quarter','month','week','day')"
                    )
                    cursor.execute(
                        "delete from common_bucket where name in ('year','quarter','month','week','day')"
                    )

                # Create buckets
                y = Bucket(name="year", description="Yearly time buckets", level=1)
                q = Bucket(
                    name="quarter", description="Quarterly time buckets", level=2
                )
                m = Bucket(name="month", description="Monthly time buckets", level=3)
                w = Bucket(name="week", description="Weeky time buckets", level=4)
                d = Bucket(name="day", description="Daily time buckets", level=5)
                y.save(using=database)
                q.save(using=database)
                m.save(using=database)
                w.save(using=database)
                d.save(using=database)

                # Loop over all days in the chosen horizon
                prev_year = None
                prev_quarter = None
                prev_month = None
                prev_week = None
                while curdate < enddate:
                    month = int(
                        curdate.strftime("%m")
                    )  # an integer in the range 1 - 12
                    quarter = (month - 1) // 3 + 1  # an integer in the range 1 - 4
                    year = int(curdate.strftime("%Y"))
                    dayofweek = int(
                        curdate.strftime("%w")
                    )  # day of the week, 0 = sunday, 1 = monday, ...
                    year_start = datetime(year, 1, 1)
                    year_end = datetime(year + 1, 1, 1)
                    week_start = curdate - timedelta(
                        (dayofweek + 6) % 7 + 1 - weekstart
                    )
                    week_end = curdate - timedelta((dayofweek + 6) % 7 - 6 - weekstart)

                    # Create buckets
                    if year != prev_year:
                        prev_year = year
                        BucketDetail(
                            bucket=y,
                            name=self.formatDate(curdate, options["format_year"]),
                            startdate=year_start,
                            enddate=year_end,
                        ).save(using=database)
                    if quarter != prev_quarter:
                        prev_quarter = quarter
                        BucketDetail(
                            bucket=q,
                            name=self.formatDate(curdate, options["format_quarter"]),
                            startdate=date(year, quarter * 3 - 2, 1),
                            enddate=date(
                                year + quarter // 4,
                                quarter * 3 + 1 - 12 * (quarter // 4),
                                1,
                            ),
                        ).save(using=database)
                    if month != prev_month:
                        prev_month = month
                        BucketDetail(
                            bucket=m,
                            name=self.formatDate(curdate, options["format_month"]),
                            startdate=date(year, month, 1),
                            enddate=date(
                                year + month // 12, month + 1 - 12 * (month // 12), 1
                            ),
                        ).save(using=database)
                    if week_start != prev_week:
                        prev_week = week_start
                        # we need to avoid weeks 00
                        # we will therefore take the name of the week starting the monday
                        # included in that week
                        BucketDetail(
                            bucket=w,
                            name=self.formatDate(
                                week_start
                                + timedelta(
                                    days=(
                                        (10 if self.isoweeknumber else 7)
                                        - week_start.weekday()
                                    )
                                    % 7
                                ),
                                options["format_week"],
                            ),
                            startdate=week_start,
                            enddate=week_end,
                        ).save(using=database)
                    BucketDetail(
                        bucket=d,
                        name=self.formatDate(curdate.date(), options["format_day"]),
                        startdate=curdate,
                        enddate=curdate + timedelta(1),
                    ).save(using=database)

                    # Next date
                    curdate = curdate + timedelta(1)

            # Log success
            if task:
                task.status = "Done"
                task.finished = datetime.now()

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            raise e

        finally:
            if task:
                task.processid = None
                task.save(using=database)
            settings.DEBUG = tmp_debug
            setattr(_thread_locals, "database", old_thread_locals)

    # accordion template
    title = _("Generate buckets")
    index = 2100
    help_url = "command-reference.html#createbuckets"

    @staticmethod
    def getHTML(request):
        if request.user.has_perm("auth.run_db"):
            return render_to_string(
                "commands/createbuckets.html",
                {
                    "startdate": datetime(2017, 1, 1),
                    "enddate": datetime(2030, 12, 31),
                },
                request=request,
            )
        else:
            return None
