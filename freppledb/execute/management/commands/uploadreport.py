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
        old_thread_locals = getattr(_thread_locals, "database", None)
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

            ftp_protocol = (
                settings.FTP_PROTOCOL[database]
                if isinstance(settings.FTP_PROTOCOL, dict)
                and database in settings.FTP_PROTOCOL
                else (
                    None
                    if isinstance(settings.FTP_PROTOCOL, dict)
                    else settings.FTP_PROTOCOL
                )
            )

            ftp_host = (
                settings.FTP_HOST[database]
                if isinstance(settings.FTP_HOST, dict) and database in settings.FTP_HOST
                else (
                    None if isinstance(settings.FTP_HOST, dict) else settings.FTP_HOST
                )
            )

            ftp_port = (
                settings.FTP_PORT[database]
                if isinstance(settings.FTP_PORT, dict) and database in settings.FTP_PORT
                else (
                    None if isinstance(settings.FTP_PORT, dict) else settings.FTP_PORT
                )
            )

            ftp_user = (
                settings.FTP_USER[database]
                if isinstance(settings.FTP_USER, dict) and database in settings.FTP_USER
                else (
                    None if isinstance(settings.FTP_USER, dict) else settings.FTP_USER
                )
            )

            ftp_password = (
                settings.FTP_PASSWORD[database]
                if isinstance(settings.FTP_PASSWORD, dict)
                and database in settings.FTP_PASSWORD
                else (
                    None
                    if isinstance(settings.FTP_PASSWORD, dict)
                    else settings.FTP_PASSWORD
                )
            )

            ftp_folder = (
                settings.FTP_FOLDER[database]
                if isinstance(settings.FTP_FOLDER, dict)
                and database in settings.FTP_FOLDER
                else (
                    None
                    if isinstance(settings.FTP_FOLDER, dict)
                    else settings.FTP_FOLDER
                )
            )

            if not ftp_protocol:
                raise CommandError(
                    "No protocol is configured in your djangosettings.py file"
                )

            if not ftp_host:
                raise CommandError(
                    "No FTP server is configured in your djangosettings.py file"
                )

            if not ftp_port:
                raise CommandError(
                    "No FTP port is configured in your djangosettings.py file"
                )

            if not ftp_user:
                raise CommandError(
                    "No FTP user is configured in your djangosettings.py file"
                )

            if not ftp_password:
                raise CommandError(
                    "No FTP password is configured in your djangosettings.py file"
                )

            if not ftp_folder:
                raise CommandError(
                    "No FTP folder is configured in your djangosettings.py file"
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
            if ftp_protocol.strip().upper() == "SFTP":
                cinfo = {
                    "host": ftp_host,
                    "username": ftp_user,
                    "password": ftp_password,
                    "port": ftp_port,
                }
                conn = pysftp.Connection(**cinfo)

                with conn.cd(ftp_folder):
                    for r in correctedReports:
                        conn.put(r[0])

                # Closes the connection
                conn.close()

            elif ftp_protocol.strip().upper() in ["FTPS", "FTP"]:
                session = (
                    FTP(ftp_host, ftp_user, ftp_password)
                    if ftp_protocol.strip().upper() == "FTP"
                    else FTP_TLS(ftp_host, ftp_user, ftp_password)
                )
                session.cwd(ftp_folder)
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
            setattr(_thread_locals, "database", old_thread_locals)
            if task:
                task.processid = None
                task.save(using=database)

    # accordion template
    title = _("Publish reports by FTP")
    index = 1275
    help_url = "command-reference.html#uploadreport"

    @staticmethod
    def getHTML(request):

        database = request.database
        ftp_protocol = (
            settings.FTP_PROTOCOL[database]
            if isinstance(settings.FTP_PROTOCOL, dict)
            and database in settings.FTP_PROTOCOL
            else (
                None
                if isinstance(settings.FTP_PROTOCOL, dict)
                else settings.FTP_PROTOCOL
            )
        )

        ftp_host = (
            settings.FTP_HOST[database]
            if isinstance(settings.FTP_HOST, dict) and database in settings.FTP_HOST
            else (None if isinstance(settings.FTP_HOST, dict) else settings.FTP_HOST)
        )

        ftp_port = (
            settings.FTP_PORT[database]
            if isinstance(settings.FTP_PORT, dict) and database in settings.FTP_PORT
            else (None if isinstance(settings.FTP_PORT, dict) else settings.FTP_PORT)
        )

        ftp_user = (
            settings.FTP_USER[database]
            if isinstance(settings.FTP_USER, dict) and database in settings.FTP_USER
            else (None if isinstance(settings.FTP_USER, dict) else settings.FTP_USER)
        )

        ftp_password = (
            settings.FTP_PASSWORD[database]
            if isinstance(settings.FTP_PASSWORD, dict)
            and database in settings.FTP_PASSWORD
            else (
                None
                if isinstance(settings.FTP_PASSWORD, dict)
                else settings.FTP_PASSWORD
            )
        )

        ftp_folder = (
            settings.FTP_FOLDER[database]
            if isinstance(settings.FTP_FOLDER, dict) and database in settings.FTP_FOLDER
            else (
                None if isinstance(settings.FTP_FOLDER, dict) else settings.FTP_FOLDER
            )
        )

        if (
            "FILEUPLOADFOLDER" not in settings.DATABASES[request.database]
            or not ftp_host
            or not ftp_user
            or not ftp_password
            or not ftp_port
            or not ftp_protocol
            or not ftp_folder
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
