#
# Copyright (C) 2010-2020 by frePPLe bv
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
from ftplib import FTP, FTP_TLS
from datetime import datetime
import pysftp
from time import localtime, strftime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from freppledb.execute.models import Task
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User
from freppledb.common.report import GridReport
from freppledb import __version__


class Command(BaseCommand):
    help = """
  This command will upload reports from the export folder to sftp or ftps server configured in djangosettings.
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
            help="database where the task should be launched",
        )
        parser.add_argument(
            "--report", help="a comma separated list of reports to email"
        )

    def handle(self, **options):
        now = datetime.now()
        database = options["database"]
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)

        # Pick up options
        if options["user"]:
            try:
                user = User.objects.all().get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        task = None
        try:
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
                    or task.name not in ("uploadreport")
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(
                    name="uploadreport",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                )
            task.processid = os.getpid()
            task.save(using=database)

            if not settings.FTP_PROTOCOL:
                raise CommandError(
                    "No protocol is configured in your djangosettings.py file"
                )

            if not settings.FTP_HOST:
                raise CommandError(
                    "No FTP server is configured in your djangosettings.py file"
                )

            if not settings.FTP_PORT:
                raise CommandError(
                    "No FTP port is configured in your djangosettings.py file"
                )

            if not settings.FTP_USER:
                raise CommandError(
                    "No FTP user is configured in your djangosettings.py file"
                )

            if not settings.FTP_PASSWORD:
                raise CommandError(
                    "No FTP password is configured in your djangosettings.py file"
                )

            report = options["report"]

            if not report:
                raise CommandError("No report to upload has been defined")

            # Make sure file exist in the export folder
            reports = report.split(",")
            correctedReports = []
            missingFiles = []
            for r in reports:
                if len(r.strip()) == 0:
                    continue
                path = os.path.join(
                    settings.DATABASES[database]["FILEUPLOADFOLDER"],
                    "export",
                    r.strip(),
                )
                if not os.path.isfile(path):
                    missingFiles.append(r.strip())
                else:
                    correctedReports.append((path, r.strip()))

            if len(missingFiles) > 0:
                raise CommandError(
                    "Following files are missing in export folder: %s"
                    % (",".join(str(x) for x in missingFiles))
                )

            if len(correctedReports) == 0:
                raise CommandError("No valid report defined in options")

            task.arguments = "--report=%s" % (report,)
            task.status = "15%"
            task.message = "Uploading reports"
            task.save(using=database)

            # SFTP
            if settings.FTP_PROTOCOL.strip().upper() == "SFTP":
                cinfo = {
                    "host": settings.FTP_HOST,
                    "username": settings.FTP_USER,
                    "password": settings.FTP_PASSWORD,
                    "port": settings.FTP_PORT,
                }
                conn = pysftp.Connection(**cinfo)

                with conn.cd(settings.FTP_FOLDER):
                    for r in correctedReports:
                        conn.put(r[0])

                # Closes the connection
                conn.close()

            elif settings.FTP_PROTOCOL.strip().upper() in ["FTPS", "FTP"]:
                session = (
                    FTP(settings.FTP_HOST, settings.FTP_USER, settings.FTP_PASSWORD)
                    if settings.FTP_PROTOCOL.strip().upper() == "FTP"
                    else FTP_TLS(
                        settings.FTP_HOST, settings.FTP_USER, settings.FTP_PASSWORD
                    )
                )
                session.cwd(settings.FTP_FOLDER)
                for r in correctedReports:
                    file = open(r[0], "rb")
                    session.storbinary("STOR %s" % (r[1],), file)
                    file.close()
                session.quit()

            else:
                raise CommandError(
                    "FTP_PROTOCOL in djangosettings.py file is not supported"
                )

            # Logging message
            task.processid = None
            task.message = ""
            task.status = "Done"
            task.finished = datetime.now()

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            raise e

        finally:
            setattr(_thread_locals, "database", None)
            if task:
                task.processid = None
                task.save(using=database)

    # accordion template
    title = _("Publish reports by FTP")
    index = 1275
    help_url = "command-reference.html#uploadreport"

    @staticmethod
    def getHTML(request):

        if (
            "FILEUPLOADFOLDER" not in settings.DATABASES[request.database]
            or not settings.FTP_HOST
            or not settings.FTP_USER
            or not settings.FTP_PASSWORD
            or not settings.FTP_PORT
            or not settings.FTP_PROTOCOL
            or not request.user.is_superuser
        ):
            return None

        # Function to convert from bytes to human readabl format
        def sizeof_fmt(num):
            for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
                if abs(num) < 1024.0:
                    return "%3.1f%sB" % (num, unit)
                num /= 1024.0
            return "%.1f%sB" % (num, "Yi")

        # List available data files
        filesexported = []
        all_reports = []
        if "FILEUPLOADFOLDER" in settings.DATABASES[request.database]:
            exportfolder = os.path.join(
                settings.DATABASES[request.database]["FILEUPLOADFOLDER"], "export"
            )
            if os.path.isdir(exportfolder):
                tzoffset = GridReport.getTimezoneOffset(request)
                for file in os.listdir(exportfolder):
                    if file.endswith((".xlsx", ".xlsx.gz", ".csv", ".csv.gz", ".log")):
                        all_reports.append(file)
                        filesexported.append(
                            [
                                file,
                                strftime(
                                    "%Y-%m-%d %H:%M:%S",
                                    localtime(
                                        os.stat(
                                            os.path.join(exportfolder, file)
                                        ).st_mtime
                                        + tzoffset.total_seconds()
                                    ),
                                ),
                                sizeof_fmt(
                                    os.stat(os.path.join(exportfolder, file)).st_size
                                ),
                                file.replace(".", "\\\\."),
                            ]
                        )

        return render_to_string(
            "commands/uploadreport.html",
            {
                "filesexported": filesexported,
                "all_reports": ",".join(map(str, all_reports)),
                "initially_disabled": "" if len(all_reports) > 0 else "disabled",
            },
            request=request,
        )
