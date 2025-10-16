#
# Copyright (C) 2010-2020 by frePPLe bv
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

import gzip
import linecache
import os
import re
from io import BytesIO
from os.path import basename
from datetime import datetime
from time import localtime, strftime
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from freppledb.execute.models import Task
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User
from freppledb.common.report import GridReport, sizeof_fmt
from freppledb.common.utils import get_databases, sendEmail
from freppledb import __version__


class Command(BaseCommand):
    help = """
  This command will email reports found in the export folder to specific recipients.
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
            "--sender", default=settings.DEFAULT_FROM_EMAIL, help="sender of the email"
        )
        parser.add_argument("--recipient", help="a comma separated list of recipients")
        parser.add_argument(
            "--report", help="a comma separated list of reports to email"
        )

    @staticmethod
    def file_is_empty(file):
        if file.lower().endswith(".csv"):
            return len(linecache.getline(file, 2).strip()) == 0
        elif file.lower().endswith(".csv.gz"):
            with gzip.open(file, "rb") as f:
                for i, l in enumerate(f):
                    if i == 1:
                        return len(l.strip()) == 0
            return True
        return False

    def handle(self, **options):
        now = datetime.now()
        database = options["database"]
        if database not in get_databases():
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
                    or task.name not in ("emailreport")
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(
                    name="emailreport",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                )
            task.processid = os.getpid()
            task.save(using=database)

            if not settings.EMAIL_HOST:
                raise CommandError(
                    "No SMTP mail server is configured in your djangosettings.py file"
                )

            sender = options["sender"]
            recipient = options["recipient"]
            report = options["report"]

            if not sender:
                raise CommandError("No sender has been defined")

            if not recipient:
                raise CommandError("No recipient has been defined")

            if not report:
                raise CommandError("No report to email has been defined")

            # Make sure file exist in the export folder
            reports = report.split(",")
            correctedReports = []
            missingFiles = []
            for r in reports:
                if len(r.strip()) == 0:
                    continue
                path = os.path.join(
                    get_databases()[database]["FILEUPLOADFOLDER"],
                    "export",
                    r.strip(),
                )
                if not os.path.isfile(path):
                    missingFiles.append(r.strip())
                else:
                    correctedReports.append(path)

            if len(missingFiles) > 0:
                raise CommandError(
                    "Following files are missing in export folder: %s"
                    % (",".join(str(x) for x in missingFiles))
                )

            if len(correctedReports) == 0:
                raise CommandError("No report defined in options")

            # Validate email adresses
            recipients = recipient.split(",")
            correctedRecipients = []
            invalidEmails = []
            for r in recipients:
                if len(r.strip()) == 0:
                    continue
                if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", r.strip()):
                    invalidEmails.append(r.strip())
                else:
                    correctedRecipients.append(r.strip())

            if len(invalidEmails) > 0:
                raise CommandError(
                    "Invalid email formatting for following addresses: %s"
                    % (",".join(str(x) for x in invalidEmails))
                )
            if len(correctedRecipients) == 0:
                raise CommandError("No recipient defined in options")

            task.arguments = "--recipient=%s --report=%s" % (recipient, report)
            task.save(using=database)

            # Filter for reports that are a one-line report (only the header)
            for file in correctedReports[:]:
                if Command.file_is_empty(file):
                    correctedReports.remove(file)

            # Return if all reports are empty
            if len(correctedReports) == 0:
                task.processid = None
                task.message = "All reports are empty, no email will be sent."
                task.status = "Done"
                task.finished = datetime.now()
                return

            # create message
            body = ["Attached are your frepple reports.\n"]
            body_html = ["Attached are your frepple reports.<br>"]
            if getattr(settings, "EMAIL_URL_PREFIX", None):
                body.append("You can also download them directly:")
                body_html.append("You can also download them directly:")
                for f in correctedReports:
                    url = (
                        f"{settings.EMAIL_URL_PREFIX}"
                        f"{"" if database==DEFAULT_DB_ALIAS else "/%s" % database}"
                        f"/execute/downloadfromfolder/1/{basename(f)}/"
                    )
                    body.append(f"    {url}")
                    body_html.append(
                        f'&nbsp;&nbsp;&nbsp;<a href="{url}">{basename(f)}</a>'
                    )
            body.append("\nThanks for using frepple!\n")
            body_html.append("<br>Thanks for using frepple!<br>")
            message = sendEmail(
                to=correctedRecipients,
                subject=(
                    "Exported reports"
                    if database == DEFAULT_DB_ALIAS
                    else f"Exported reports from {database}"
                ),
                body="\n".join(body),
                body_html="<br>".join(body_html),
                send=False,
            )

            with BytesIO() as b:
                with ZipFile(file=b, mode="w", compression=ZIP_DEFLATED) as zf:
                    processedFiles = 0
                    for f in correctedReports:
                        task.message = "Compressing file %s" % basename(f)
                        task.status = (
                            str(int(processedFiles / len(correctedReports) * 90.0))
                            + "%"
                        )
                        task.save(using=database)
                        zf.write(filename=f, arcname=basename(f))
                        processedFiles = processedFiles + 1
                    zf.close()

                    # attach zip file
                    task.status = "90%"
                    task.message = "Sending email"
                    task.save(using=database)
                    message.attach("reports.zip", b.getvalue(), "application/zip")
                    # send email
                    message.send()

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

    title = _("Publish reports by email")
    index = 1800
    help_url = "command-reference.html#emailreport"

    @staticmethod
    def getHTML(request):
        if (
            "FILEUPLOADFOLDER" not in get_databases()[request.database]
            or not settings.EMAIL_HOST
            or not request.user.is_superuser
        ):
            return None

        # List available data files
        filesexported = []
        all_reports = []
        if "FILEUPLOADFOLDER" in get_databases()[request.database]:
            exportfolder = os.path.join(
                get_databases()[request.database]["FILEUPLOADFOLDER"], "export"
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
            "commands/emailreport.html",
            {
                "filesexported": filesexported,
                "user_email": request.user.email,
                "all_reports": ",".join(map(str, all_reports)),
                "initially_disabled": "" if len(all_reports) > 0 else "disabled",
            },
            request=request,
        )
