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
from io import BytesIO
from os.path import basename
from datetime import datetime
from time import localtime, strftime
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template import Template, RequestContext

from freppledb.execute.models import Task
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User
from freppledb.common.report import GridReport
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
            help="database where the task should be launched",
        )
        parser.add_argument(
            "--sender", default=settings.DEFAULT_FROM_EMAIL, help="sender of the email"
        )
        parser.add_argument("--recipient", help="a comma separated list of recipients")
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
                    settings.DATABASES[database]["FILEUPLOADFOLDER"],
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

            # create message
            message = EmailMessage(
                subject="Exported reports",
                body="",
                from_email=sender,
                to=correctedRecipients,
            )

            b = BytesIO()
            with ZipFile(file=b, mode="w", compression=ZIP_DEFLATED) as zf:
                processedFiles = 0
                for f in correctedReports:
                    task.message = "Compressing file %s" % basename(f)
                    task.status = (
                        str(int(processedFiles / len(correctedReports) * 90.0)) + "%"
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

            b.close()

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
    title = _("Email exported reports")
    index = 1250
    help_url = "user-guide/command-reference.html#emailreport"

    @staticmethod
    def getHTML(request):

        if (
            "FILEUPLOADFOLDER" in settings.DATABASES[request.database]
            and request.user.is_superuser
        ):
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
                        if file.endswith((".csv", ".csv.gz", ".log")):
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
                                        os.stat(
                                            os.path.join(exportfolder, file)
                                        ).st_size
                                    ),
                                    file.split(".")[0],
                                ]
                            )

            context = RequestContext(
                request,
                {
                    "filesexported": filesexported,
                    "user_email": request.user.email,
                    "all_reports": ",".join(map(str, all_reports)),
                    "initially_disabled": "" if len(all_reports) > 0 else "disabled",
                },
            )

            template = Template(
                """
        {% load i18n %}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/emailreport/">{% csrf_token %}
          <table>
            <tr>
              <td style="vertical-align:top; padding-left: 15px">
                <button type="submit" class="btn btn-primary" id="emailreport" value="email" {{initially_disabled}}>{% trans "email"|capfirst %}</button>
              </td>
              <td colspan='5' style="padding-left: 15px;">
                <p>{% trans "Emails the selected reports to a comma separated list of recipients. Files are zipped and attached to email." %}</p>
              </td>
            </tr>
            <tr>
              <td></td>
              <td><div>
                   <input type="checkbox" id="allcheckboxes" checked>
                   <strong>{% trans 'file name'|capfirst %}</strong></td>
                   </div>
              <td><strong>{% trans 'size'|capfirst %}</strong></td>
              <td><strong>{% trans 'last modified'|capfirst %}</strong></td>
              <td></td>
            </tr></form>
            {% for j in filesexported %}
            <tr data-file="{{j.0}}">
              <td></td>
              <td>
                  <input type="checkbox" id="{{j.3}}" checked>
                  {{j.0}}
              </td>
              <td>{{j.2}}</td>
              <td>{{j.1}}</td>
            </tr>
            {% endfor %}
            <tr>
                <td style="padding-left:15px; padding-top:10px"><strong>{% trans 'emails'|capfirst %}:</strong>
                </td>
                <td style="padding-top:10px" colspan="3">
                <input type="email" class="form-control" id="emails" name="recipient" multiple value="{{user_email}}">
                </td>
            </tr>
          </table>
          <input type="hidden" name="report" id="report" value="{{all_reports}}">
        </form>
        <script>
        function validateButton() {
            var reports = "";
            var first = true;
            {% for j in filesexported %}
              if ($('#{{j.3}}').is(':checked')) {
                  if (first) {
                    reports = reports + "{{j.0}}";
                    first = false
                  }
                  else {
                    reports = reports + ",{{j.0}}";
                  }
              }
            {% endfor %}
            $("#report").val(reports);
            var oneChecked = false;
            {% for j in filesexported %}
              oneChecked = oneChecked || $('#{{j.3}}').is(':checked');
            {% endfor %}
            var testEmail = /^([\w+-.%]+@[\w-.]+\.[A-Za-z]{2,},?)+$/;
            emails_ok = $("#emails").val() != '' && testEmail.test($("#emails").val());
            if (!emails_ok) {
               $("#emails").attr('data-original-title', '{% trans 'please correct invalid email addresses'|capfirst %}');
               $('#emails').tooltip('show');
            }
            else {
               $("#emails").tooltip('hide').attr('data-original-title', '{% trans 'please enter email addresses'|capfirst %}');
            }
            $('#emailreport').prop('disabled', !(oneChecked && emails_ok));

        }
        $("#emails").on('input', function () {
            validateButton();
        });
        $("#allcheckboxes").on("click", function(event) {
            var isChecked = $('#allcheckboxes').is(':checked');
            {% for j in filesexported %}
            $("#{{j.3}}").prop("checked", isChecked);
            {% endfor %}
            validateButton();
        });
        {% for j in filesexported %}
        $("#{{j.3}}").on("click", function(event) {
            var allChecked = true;
            {% for j in filesexported %}
              allChecked = allChecked && $('#{{j.3}}').is(':checked');
            {% endfor %}
            $("#allcheckboxes").prop("checked", allChecked);
            validateButton();
        });
        {% endfor %}
        </script>
        """
            )
            return template.render(context)
            # A list of translation strings from the above
            translated = (
                _("email"),
                _(
                    "Emails the selected reports to a comma separated list of recipients. Files are zipped and attached to email."
                ),
                _("file name"),
                _("size"),
                _("please correct invalid email addresses"),
                _("please enter email addresses"),
            )
        else:
            return None
