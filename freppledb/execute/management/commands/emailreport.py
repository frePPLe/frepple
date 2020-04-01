#
# Copyright (C) 2010-2020 by frePPLe bvba
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
import re
import subprocess
from io import BytesIO
from os.path import basename
from datetime import datetime
from zipfile import ZipFile

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template import Template, RequestContext

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):
    help = """
  This command will email reports found in the export folder to specific recipients.
  """

    requires_system_checks = False

    def get_version(self):
        return VERSION

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
            help="Unused argument for this command",
        )
        parser.add_argument(
            "--sender", default=settings.DEFAULT_FROM_EMAIL, help="sender of the email"
        )
        parser.add_argument(
            "--recipient", help="a semi-colon separated list of recipients"
        )
        parser.add_argument(
            "--report", help="a semi-colon separated list of reports to email"
        )

    def handle(self, **options):
        # Make sure the debug flag is not set!
        # When it is set, the django database wrapper collects a list of all sql
        # statements executed and their timings. This consumes plenty of memory
        # and cpu time.
        tmp_debug = settings.DEBUG
        settings.DEBUG = False

        # Pick up options
        if options["user"]:
            try:
                user = User.objects.all().get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        sender = options["sender"]
        recipient = options["recipient"]
        report = options["report"]

        if not sender:
            raise CommandError("No sender has been defined")

        if not recipient:
            raise CommandError("No recipient has been defined")

        if not report:
            raise CommandError("No report to email has been defined")

        database = options["database"]

        # Make sure file exist in the export folder
        reports = report.split(";")
        correctedReports = []
        missingFiles = []
        for r in reports:
            if len(r.strip()) == 0:
                continue
            path = os.path.join(
                settings.DATABASES[database]["FILEUPLOADFOLDER"], "export", r.strip()
            )
            if not os.path.isfile(path):
                missingFiles.append(r.strip())
            else:
                correctedReports.append(path)

        if len(missingFiles) > 0:
            raise CommandError(
                "Following files are missing in export folder: %s"
                % (";".join(str(x) for x in missingFiles))
            )

        if len(correctedReports) == 0:
            raise CommandError("No report defined in options")

        # Validate email adresses
        recipients = recipient.split(";")
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
                % (";".join(str(x) for x in invalidEmails))
            )
        if len(correctedRecipients) == 0:
            raise CommandError("No recipient defined in options")

        now = datetime.now()
        task = None
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
                name="emailreport", submitted=now, started=now, status="0%", user=user
            )
        task.processid = os.getpid()
        task.save(using=database)

        try:
            task.arguments = "--recipient=%s --report=%s" % (recipient, report)
            task.save(using=database)

            # create message
            message = EmailMessage(
                subject="Exported reports",
                body="",
                from_email=sender,
                to=correctedRecipients,
            )

            b = BytesIO()
            with ZipFile(b, mode="w") as zf:
                for f in correctedReports:
                    zf.write(f, basename(f))
                zf.close()

                # attach zip file
                message.attach("reports.zip", b.getvalue(), "application/zip")

                # send email
                message.send()
            b.close()

            # Logging message
            task.processid = None
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

    # accordion template
    title = _("Email reports")
    index = 1250
    help_url = "user-guide/command-reference.html#email-report"

    @staticmethod
    def getHTML(request):

        return None
