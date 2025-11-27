#
# Copyright (C) 2016 by frePPLe bv
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
import errno
import gzip
import importlib
import logging

from datetime import datetime
from time import localtime, strftime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models import Q
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils.encoding import force_str
from django.utils.formats import get_format
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

import freppledb
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User
from freppledb.common.report import GridReport, sizeof_fmt
from freppledb.common.utils import getStorageUsage, get_databases
from freppledb import __version__
from freppledb.execute.models import Task, DataExport
from freppledb.output.views import resource
from freppledb.output.views import buffer

logger = logging.getLogger(__name__)

delimiter = (
    ";" if get_format("DECIMAL_SEPARATOR", settings.LANGUAGE_CODE, True) == "," else ","
)


def timesince(st):
    return str(datetime.now() - st).split(".")[0]


class Command(BaseCommand):
    help = """
    Exports tables from the frePPLe database to CSV files in a folder
    """

    requires_system_checks = []

    # The "statements" variable is only used during a transition period
    # to give customers the time to migrate their legacy custom configuration.
    statements = [
        {
            "filename": "purchaseorder.csv.gz",
            "folder": "export",
            "sql": """COPY
                (select source, lastmodified, reference, status , reference, quantity,
                to_char(startdate,'%s HH24:MI:SS') as "ordering date",
                to_char(enddate,'%s HH24:MI:SS') as "receipt date",
                criticality, EXTRACT(EPOCH FROM delay) as delay,
                owner_id, item_id, location_id, supplier_id from operationplan
                where status <> 'confirmed' and type='PO')
                TO STDOUT WITH CSV HEADER DELIMITER '%s'"""
            % (settings.DATE_FORMAT_JS, settings.DATE_FORMAT_JS, delimiter),
        },
        {
            "filename": "distributionorder.csv.gz",
            "folder": "export",
            "sql": """COPY
                (select source, lastmodified, reference, status, reference, quantity,
                to_char(startdate,'%s HH24:MI:SS') as "ordering date",
                to_char(enddate,'%s HH24:MI:SS') as "receipt date",
                criticality, EXTRACT(EPOCH FROM delay) as delay,
                plan, destination_id, item_id, origin_id from operationplan
                where status <> 'confirmed' and type='DO')
                TO STDOUT WITH CSV HEADER DELIMITER '%s'"""
            % (settings.DATE_FORMAT_JS, settings.DATE_FORMAT_JS, delimiter),
        },
        {
            "filename": "manufacturingorder.csv.gz",
            "folder": "export",
            "sql": """COPY
                (select source, lastmodified, reference, status ,reference ,quantity,
                to_char(startdate,'%s HH24:MI:SS') as startdate,
                to_char(enddate,'%s HH24:MI:SS') as enddate,
                criticality, EXTRACT(EPOCH FROM delay) as delay,
                operation_id, owner_id, plan, item_id, batch
                from operationplan where status <> 'confirmed' and type='MO')
                TO STDOUT WITH CSV HEADER DELIMITER '%s'"""
            % (settings.DATE_FORMAT_JS, settings.DATE_FORMAT_JS, delimiter),
        },
        {
            "filename": "problems.csv.gz",
            "folder": "export",
            "sql": """COPY (
                select
                    entity, owner, name, description,
                    to_char(startdate,'%s HH24:MI:SS') as startdate,
                    to_char(enddate,'%s HH24:MI:SS') as enddate
                from out_problem
                where name <> 'material excess'
                order by entity, name, startdate
                ) TO STDOUT WITH CSV HEADER DELIMITER '%s'"""
            % (settings.DATE_FORMAT_JS, settings.DATE_FORMAT_JS, delimiter),
        },
        {
            "filename": "operationplanmaterial.csv.gz",
            "folder": "export",
            "sql": """COPY (
                select
                    item_id as item, location_id as location, quantity,
                    to_char(flowdate,'%s HH24:MI:SS') as date, onhand,
                    operationplan_id as operationplan, status
                from operationplanmaterial
                order by item_id, location_id, flowdate, quantity desc
                ) TO STDOUT WITH CSV HEADER DELIMITER '%s'"""
            % (settings.DATE_FORMAT_JS, delimiter),
        },
        {
            "filename": "operationplanresource.csv.gz",
            "folder": "export",
            "sql": """COPY (
                select
                    operationplanresource.resource_id as resource,
                    to_char(operationplan.startdate,'%s HH24:MI:SS') as startdate,
                    to_char(operationplan.enddate,'%s HH24:MI:SS') as enddate,
                    operationplanresource.setup,
                    operationplanresource.operationplan_id as operationplan,
                    operationplan.status
                from operationplanresource
                inner join operationplan on operationplan.reference = operationplanresource.operationplan_id
                order by operationplanresource.resource_id,
                operationplan.startdate,
                operationplanresource.quantity
                ) TO STDOUT WITH CSV HEADER DELIMITER '%s'"""
            % (settings.DATE_FORMAT_JS, settings.DATE_FORMAT_JS, delimiter),
        },
        {
            "filename": "capacityreport.csv.gz",
            "folder": "export",
            "report": resource.OverviewReport,
            "data": {
                "format": "csvlist",
                "buckets": "week",
                "horizontype": True,
                "horizonunit": "month",
                "horizonlength": 6,
            },
        },
        {
            "filename": "inventoryreport.csv.gz",
            "folder": "export",
            "report": buffer.OverviewReport,
            "data": {
                "format": "csvlist",
                "buckets": "week",
                "horizontype": True,
                "horizonunit": "month",
                "horizonlength": 6,
            },
        },
    ]

    if "freppledb.forecast" in settings.INSTALLED_APPS:
        from freppledb.forecast.views import OverviewReport as ForecastOverviewReport

        statements.append(
            {
                "filename": "forecastreport.csv.gz",
                "folder": "export",
                "report": ForecastOverviewReport,
                "data": {
                    "format": "csvlist",
                    "buckets": "month",
                    "horizontype": True,
                    "horizonunit": "month",
                    "horizonlength": 6,
                },
            }
        )

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to load the data into",
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )

    @classmethod
    def getExports(cls, database):
        if cls.statements == Command.statements:
            return list(DataExport.objects.all().using(database).order_by("name"))
        else:
            # Migrate old customized hardcode export on the fly
            tmp = []
            for r in cls.statements:
                if "sql" in r:
                    x = DataExport(name=r["filename"], sql=r["sql"])
                    x.no_wrapper = True
                elif "report" in r:
                    x = DataExport(
                        name=r["filename"],
                        report="%s.%s" % (r["report"].__module__, r["report"].__name__),
                        arguments=r.get("data", None),
                    )
                    if x.arguments:
                        x.arguments.pop("format", None)
                else:
                    raise Exception("Unknown export format")
                tmp.append(x)
            return tmp

    def handle(self, *args, **options):
        # Pick up the options
        now = datetime.now()
        self.database = options["database"]
        if self.database not in get_databases():
            raise CommandError("No database settings known for '%s'" % self.database)

        if options["user"]:
            try:
                self.user = (
                    User.objects.all()
                    .using(self.database)
                    .get(username=options["user"])
                )
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            self.user = None

        timestamp = now.strftime("%Y%m%d%H%M%S")
        if self.database == DEFAULT_DB_ALIAS:
            logfile = "exporttofolder-%s.log" % timestamp
        else:
            logfile = "exporttofolder_%s-%s.log" % (self.database, timestamp)

        try:
            handler = logging.FileHandler(
                os.path.join(settings.FREPPLE_LOGDIR, logfile), encoding="utf-8"
            )
            # handler.setFormatter(logging.Formatter(settings.LOGGING['formatters']['simple']['format']))
            logger.addHandler(handler)
            logger.propagate = False
        except Exception as e:
            print("Failed to open logfile %s: %s" % (logfile, e))

        # confirm there is enough storage to proceed
        maxstorage = getattr(settings, "MAXSTORAGE", 0) or 0
        if maxstorage:
            storageUsage = round(getStorageUsage() / 1024 / 1024)
            if storageUsage > maxstorage:
                raise CommandError(
                    """
                    Storage quota exceeded: %sMB <a href="/" class="text-decoration-underline">used out</a> of %sMB available. Please free some disk space and try again
                    """
                    % (storageUsage, maxstorage)
                )

        task = None
        errors = 0
        old_thread_locals = getattr(_thread_locals, "database", None)
        startofall = datetime.now()
        try:
            # Initialize the task
            setattr(_thread_locals, "database", self.database)
            if options["task"]:
                try:
                    task = (
                        Task.objects.all().using(self.database).get(pk=options["task"])
                    )
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name not in ("frepple_exporttofolder", "exporttofolder")
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
                task.logfile = logfile
                if not self.user and task.user:
                    self.user = task.user
            else:
                task = Task(
                    name="exporttofolder",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=self.user,
                    logfile=logfile,
                )
            task.arguments = " ".join(['"%s"' % i for i in args])
            task.processid = os.getpid()
            task.save(using=self.database)

            # Try to create the upload if doesn't exist yet
            if not os.path.isdir(get_databases()[self.database]["FILEUPLOADFOLDER"]):
                try:
                    os.makedirs(get_databases()[self.database]["FILEUPLOADFOLDER"])
                except Exception:
                    pass

            # Execute
            if os.path.isdir(get_databases()[self.database]["FILEUPLOADFOLDER"]):
                if not os.path.isdir(
                    os.path.join(
                        get_databases()[self.database]["FILEUPLOADFOLDER"], "export"
                    )
                ):
                    try:
                        os.makedirs(
                            os.path.join(
                                get_databases()[self.database]["FILEUPLOADFOLDER"],
                                "export",
                            )
                        )
                    except OSError as exception:
                        if exception.errno != errno.EEXIST:
                            raise

                logger.info("Started export to folder")
                task.status = "0%"
                task.save(using=self.database)

                i = 0
                exports = self.getExports(self.database)
                cnt = len(exports)

                for cfg in exports:
                    # Report progress
                    starting = datetime.now()
                    logger.info("Started export of %s" % cfg.name)
                    if task:
                        task.message = "Exporting %s" % cfg.name
                        task.save(using=self.database)

                    # Make sure export folder exists
                    exportFolder = os.path.join(
                        get_databases()[self.database]["FILEUPLOADFOLDER"], "export"
                    )
                    if not os.path.isdir(exportFolder):
                        os.makedirs(exportFolder)

                    try:
                        filename = os.path.join(exportFolder, cfg.name)
                        if cfg.report:
                            # Export from report class (standard or custom)

                            # Create a dummy request
                            factory = RequestFactory()
                            request = factory.get("/dummy/", cfg.arguments)
                            if self.user:
                                request.user = self.user
                            else:
                                request.user = User.objects.all().get(username="admin")
                            request.database = self.database
                            request.LANGUAGE_CODE = settings.LANGUAGE_CODE

                            # Identify the report to export
                            n = cfg.report.rsplit(".", 1)
                            if n[0] == "freppledb.reportmanager.models.SQLReport":
                                if "freppledb.reportmanager" in settings.INSTALLED_APPS:
                                    # Exporting a custom report
                                    from freppledb.reportmanager.models import SQLReport
                                    from freppledb.reportmanager.views import (
                                        ReportManager,
                                    )

                                    reportclass = ReportManager
                                    report = SQLReport.objects.using(self.database).get(
                                        id=int(cfg.report.rsplit(".", 1)[1])
                                    )
                                    if (
                                        not report.public
                                        and self.user
                                        and report.user != self.user
                                    ):
                                        raise Exception("No access to this report")
                                    else:
                                        request.report = report
                                        args = [report.id]
                                else:
                                    # Custom export still exists, but reportmanager app is disabled
                                    raise Exception(
                                        "No custom reports can be export. Install the 'reportmanager' app to enable."
                                    )
                            else:
                                # Exporting a standard report
                                reportclass = getattr(
                                    importlib.import_module(n[0]), n[1]
                                )
                                args = []

                            # Initialize the report
                            if hasattr(reportclass, "initialize"):
                                reportclass.initialize(request)
                            if hasattr(reportclass, "rows"):
                                if callable(reportclass.rows):
                                    request.rows = reportclass.rows(request, *args)
                                else:
                                    request.rows = reportclass.rows
                            if hasattr(reportclass, "crosses"):
                                if callable(reportclass.crosses):
                                    request.crosses = reportclass.crosses(
                                        request, *args
                                    )
                                else:
                                    request.crosses = reportclass.crosses
                            if reportclass.hasTimeBuckets:
                                reportclass.getBuckets(request)

                            # Write the report file
                            if cfg.name.lower().endswith(".gz"):
                                datafile = gzip.open(filename, "wb")
                            else:
                                datafile = open(filename, "wb")
                            if cfg.name.lower().endswith(".xlsx"):
                                reportclass._generate_spreadsheet_data(
                                    request,
                                    [request.database],
                                    datafile,
                                    *args,
                                    **(cfg.arguments or {}),
                                )
                            elif cfg.name.lower().endswith((".csv", ".csv.gz")):
                                for r in reportclass._generate_csv_data(
                                    request,
                                    [request.database],
                                    *args,
                                    **(cfg.arguments or {}),
                                ):
                                    datafile.write(
                                        r.encode(settings.CSV_CHARSET)
                                        if isinstance(r, str)
                                        else r
                                    )
                            else:
                                raise Exception(
                                    "Unknown output format for %s" % cfg.name
                                )
                        elif cfg.sql:
                            # Exporting using SQL
                            if cfg.name.lower().endswith(".csv.gz"):
                                datafile = gzip.open(filename, "wb")
                            elif cfg.name.lower().endswith(".csv"):
                                datafile = open(filename, "wb")
                            else:
                                raise Exception(
                                    "Exports based on an SQL query can only be created in .csv or .csv.gz format"
                                )

                            with connections[
                                (
                                    self.database
                                    if f"{self.database}_report"
                                    not in get_databases(True)
                                    else f"{self.database}_report"
                                )
                            ].cursor() as cursor:
                                cursor.copy_expert(
                                    (
                                        cfg.sql
                                        if getattr(cfg, "no_wrapper", False)
                                        else f"COPY(select * from ({cfg.sql}) as t) TO STDOUT WITH CSV HEADER DELIMITER '{delimiter}'"
                                    ),
                                    datafile,
                                )
                        else:
                            logger.error(f"Skipping export of {cfg.name}: Unknown type")
                            continue
                        datafile.close()
                        i += 1
                        logger.info(
                            f"Finished export of {cfg.name} ({os.stat(filename).st_size} bytes) in {timesince(starting)}"
                        )
                    except (ImportError, AttributeError):
                        # The export configuration can refer to non-existing reports.
                        # For instance after an app is uninstalled.
                        errors += 1
                        logger.error(
                            f"Failed to export {cfg.name}: Unknown report {cfg.report}"
                        )
                    except Exception as e:
                        errors += 1
                        logger.error(
                            f"Failed to export {cfg.name} after {timesince(starting)}: {e}"
                        )
                        if task:
                            task.message = "Failed to export %s" % cfg.name

                    task.status = str(int(i / cnt * 100)) + "%"
                    task.save(using=self.database)

                logger.info("Exported %s files" % (cnt - errors))

            else:
                errors += 1
                logger.error("Failed, folder does not exist")
                task.message = "Destination folder does not exist"
                task.save(using=self.database)

        except Exception as e:
            logger.error("Failed to export: %s" % e)
            errors += 1
            if task:
                task.message = "Failed to export"

        finally:
            logger.info("End of export to folder in %s\n" % timesince(startofall))
            if task:
                if not errors:
                    task.status = "100%"
                    task.message = "Exported %s data files" % (cnt)
                else:
                    task.status = "Failed"
                    task.message = "Exported %s data files, %s failed" % (
                        cnt - errors,
                        errors,
                    )
                task.finished = datetime.now()
                task.processid = None
                task.save(using=self.database)
            setattr(_thread_locals, "database", old_thread_locals)

    # accordion template
    title = _("Export plan result")
    index = 1200
    help_url = "command-reference.html#exporttofolder"

    @classmethod
    def getHTML(cls, request):
        if (
            "FILEUPLOADFOLDER" not in get_databases()[request.database]
            or not request.user.is_superuser
        ):
            return None

        # List available data files
        data_exports = cls.getExports(request.database)
        if "FILEUPLOADFOLDER" in get_databases()[request.database]:
            exportfolder = os.path.join(
                get_databases()[request.database]["FILEUPLOADFOLDER"], "export"
            )
            tzoffset = GridReport.getTimezoneOffset(request)
            if os.path.isdir(exportfolder):
                for f in data_exports:
                    full_file = os.path.join(exportfolder, f.name)
                    if os.access(full_file, os.R_OK):
                        stat = os.stat(full_file)
                        f.timestamp = strftime(
                            "%Y-%m-%d %H:%M:%S",
                            localtime(stat.st_mtime + tzoffset.total_seconds()),
                        )
                        f.size = sizeof_fmt(stat.st_size)

        if "freppledb.reportmanager" in settings.INSTALLED_APPS:
            from freppledb.reportmanager.models import SQLReport

            customreports = sorted(
                [
                    (r.name, r.id)
                    for r in SQLReport.objects.using(request.database)
                    .filter(Q(public=True) | Q(user_id=request.user.id))
                    .only("id", "name")
                ]
            )
        else:
            customreports = []

        # TODO hard coded list of possible reports should be replaced with a dynamic query
        reports = [
            freppledb.output.views.resource.OverviewReport,
            freppledb.output.views.demand.OverviewReport,
            freppledb.output.views.buffer.OverviewReport,
            freppledb.output.views.operation.OverviewReport,
            freppledb.output.views.operation.DistributionReport,
            freppledb.output.views.operation.PurchaseReport,
        ]
        if "freppledb.forecast" in settings.INSTALLED_APPS:
            reports.append(freppledb.forecast.views.OverviewReport)
        return render_to_string(
            "commands/exporttofolder.html",
            {
                "data_exports": data_exports,
                "reports": sorted(
                    [
                        [
                            capfirst(force_str(r.title)),
                            "%s.%s" % (r.__module__, r.__name__),
                        ]
                        for r in reports
                    ]
                ),
                "customreports": customreports,
            },
            request=request,
        )
