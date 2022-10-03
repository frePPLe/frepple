#
# Copyright (C) 2007-2020 by frePPLe bv
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
import gzip
from importlib import import_module
from io import BytesIO
import json
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import NamedStyle, PatternFill
from openpyxl.comments import Comment as CellComment
import operator
import os
import re
import shlex
from time import sleep
from zipfile import ZipFile, ZIP_DEFLATED

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignKey
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.db import DEFAULT_DB_ALIAS
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.http import (
    Http404,
    HttpResponseRedirect,
    HttpResponseServerError,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseForbidden,
    StreamingHttpResponse,
    HttpResponseNotAllowed,
)
from django.contrib import messages
from django.utils.encoding import force_str
from django.utils.text import capfirst
from django.core.management import get_commands, call_command

from freppledb.admin import data_site
from freppledb.common.auth import basicauthentication
from freppledb.common.dataload import parseExcelWorksheet
from freppledb.common.models import Scenario, HierarchyModel
from freppledb.common.report import (
    GridFieldDuration,
    GridFieldBool,
    GridFieldLocalDateTime,
    GridReport,
    GridFieldText,
    GridFieldInteger,
    EXCLUDE_FROM_BULK_OPERATIONS,
    _getCellValue,
    matchesModelName,
)
from freppledb.common.views import sendStaticFile
from .models import Task, ScheduledTask
from .management.commands.runworker import launchWorker

import logging


logger = logging.getLogger(__name__)


class TaskReport(GridReport):
    """
    A list report to review the history of actions.
    """

    template = "execute/execute.html"
    title = _("Task status")
    basequeryset = (
        Task.objects.all()
        .extra(
            select={
                "duration": "case when status in ('Done', '100%%') then finished::timestamp(0) - started::timestamp(0) end"
            }
        )
        .select_related("user")
    )
    model = Task
    frozenColumns = 0
    multiselect = False
    editable = False
    height = 150
    default_sort = (0, "desc")
    help_url = "user-interface/execute.html"

    rows = (
        GridFieldInteger("id", title=_("identifier"), key=True),
        GridFieldText("name", title=_("name"), editable=False, align="center"),
        GridFieldLocalDateTime(
            "submitted", title=_("submitted"), editable=False, align="center"
        ),
        GridFieldLocalDateTime(
            "started", title=_("started"), editable=False, align="center"
        ),
        GridFieldLocalDateTime(
            "finished", title=_("finished"), editable=False, align="center"
        ),
        GridFieldText(
            "status",
            title=_("status"),
            editable=False,
            align="center",
            extra="formatter:status",
        ),
        GridFieldText(
            "logfile",
            title=_("log file"),
            width=80,
            editable=False,
            align="center",
            extra="formatter:logbutton",
        ),
        GridFieldText(
            "message",
            title=_("message"),
            editable=False,
            width=500,
            formatter="longstring",
        ),
        GridFieldText(
            "arguments", title=_("arguments"), formatter="longstring", editable=False
        ),
        GridFieldText(
            "user",
            title=_("user"),
            field_name="user__username",
            editable=False,
            align="center",
        ),
        GridFieldDuration(
            "duration",
            title=_("duration"),
            search=False,
            editable=False,
            align="center",
        ),
        GridFieldBool("cancelable", title="cancelable", hidden=True),
    )

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        # Loop over all accordion of all apps and directories
        accordions = set()
        accord = ""
        for commandname, appname in get_commands().items():
            try:
                accord = getattr(
                    import_module("%s.management.commands.%s" % (appname, commandname)),
                    "Command",
                )
                if getattr(accord, "index", -1) >= 0 and getattr(
                    accord, "getHTML", None
                ):
                    accord.name = commandname
                    accordions.add(accord)
            except Exception as e:
                logger.warning(
                    "Couldn't import getHTML method from %s.management.commands.%s: %s"
                    % (appname, commandname, e)
                )

        accordions = sorted(accordions, key=operator.attrgetter("index"))

        # Send to template
        return {"commandlist": accordions}

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        logfileslist = set(
            [
                x
                for x in os.listdir(settings.FREPPLE_LOGDIR)
                if x.endswith(".log")
                or (
                    x.lower().endswith(".dump")
                    and request.user.username in settings.SUPPORT_USERS
                )
            ]
        )
        for rec in basequery:
            yield {
                "id": rec.id,
                "name": rec.name,
                "submitted": rec.submitted,
                "started": rec.started,
                "finished": rec.finished,
                "status": rec.status,
                "logfile": rec.logfile if rec.logfile in logfileslist else None,
                "message": rec.message,
                "arguments": rec.arguments,
                "user__username": rec.user.username if rec.user else None,
                "duration": rec.duration,
                "cancelable": rec.processid is not None or rec.status == "Waiting",
            }

    @classmethod
    def extraJSON(reportclass, request):
        try:
            lastCompletedTask = (
                Task.objects.all()
                .using(request.database)
                .filter(status="Done")
                .order_by("-id")
                .only("id")[0]
            )
            return '"lastcompleted":%d,\n' % lastCompletedTask.id
        except Exception:
            return '"lastcompleted":0,\n'


@csrf_exempt
@basicauthentication(allow_logged_in=True)
def APITask(request, action):
    try:
        if action == "status":
            response = {}
            args = request.GET.getlist("id")
            if args:
                tasks = Task.objects.all().using(request.database).filter(id__in=args)
            else:
                tasks = (
                    Task.objects.all()
                    .using(request.database)
                    .filter(finished__isnull=True)
                    .exclude(status="Canceled")
                )
            for t in tasks:
                response[t.id] = {
                    "name": t.name,
                    "submitted": str(t.submitted),
                    "started": str(t.started),
                    "finished": str(t.finished),
                    "arguments": t.arguments,
                    "status": t.status,
                    "message": t.message,
                    "user": t.user.username if t.user else None,
                    "logfile": t.logfile,
                }
        elif action == "cancel":
            response = {}
            with transaction.atomic(using=request.database):
                args = request.GET.getlist("id")
                for t in (
                    Task.objects.all()
                    .using(request.database)
                    .select_for_update()
                    .filter(id__in=args)
                ):
                    if request.user.is_superuser or t.user == request.user:
                        if t.processid:
                            # Kill the process with signal 9
                            os.kill(t.processid, 9)
                            sleep(1)  # Wait for it to die
                            t.message = "Canceled process"
                            t.processid = None
                        elif t.status != "Waiting":
                            continue
                        t.status = "Canceled"
                        t.save(using=request.database)
                        response[t.id] = {
                            "name": t.name,
                            "submitted": str(t.submitted),
                            "started": str(t.started),
                            "finished": str(t.finished),
                            "arguments": t.arguments,
                            "status": t.status,
                            "message": t.message,
                            "user": t.user.username if t.user else None,
                        }
        elif action == "log":
            taskid = request.GET.get("id")
            if not taskid:
                return HttpResponseNotFound("Task or log file not found")
            try:
                task = Task.objects.all().using(request.database).get(id=taskid)
                if task and task.logfile:
                    return sendStaticFile(
                        request,
                        settings.FREPPLE_LOGDIR,
                        task.logfile,
                        headers={
                            "Content-Type": "application/octet-stream",
                            "Content-Disposition": 'inline; filename="frepple_%s_%s.log"'
                            % (request.database, taskid),
                        },
                    )
            except Exception as e:
                return HttpResponseNotFound("Task or log file not found")
        else:
            task = wrapTask(request, action)
            if task:
                response = {"taskid": task.id, "message": "Successfully launched task"}
            else:
                response = {"message": "No task was launched"}
    except Exception:
        response = {"message": "Exception launching task"}
    return HttpResponse(json.dumps(response), content_type="application/json")


@staff_member_required
@never_cache
@csrf_protect
def LaunchTask(request, action):
    try:
        if action == "exportworkbook":
            return exportWorkbook(request)
        elif action == "importworkbook":
            return StreamingHttpResponse(
                content_type="text/plain; charset=%s" % settings.DEFAULT_CHARSET,
                streaming_content=importWorkbook(request),
            )
        else:
            wrapTask(request, action)
            return HttpResponseRedirect("%s/execute/" % request.prefix)
    except Exception as e:
        logger.error("Error launching task: %s" % e)
        messages.add_message(
            request, messages.ERROR, force_str(_("Failure launching task"))
        )
        return HttpResponseRedirect("%s/execute/" % request.prefix)


def wrapTask(request, action):
    # Allow only post
    if request.method != "POST":
        raise Exception("Only post requests allowed")
    # Parse the posted parameters as arguments for an asynchronous task to add to the queue.    TODO MAKE MODULAR WITH SEPERATE TASK CLASS
    worker_database = request.database

    now = datetime.now()
    task = None
    args = request.POST or request.GET

    # A
    if action == "runplan":
        if not request.user.has_perm("auth.generate_plan"):
            raise Exception("Missing execution privileges")
        constraint = 0
        for value in args.getlist("constraint"):
            try:
                constraint += int(value)
            except Exception:
                pass
        task = Task(name="runplan", submitted=now, status="Waiting", user=request.user)
        task.arguments = "--constraint=%s --plantype=%s" % (
            constraint,
            args.get("plantype", 1),
        )
        env = []
        for value in args.getlist("env"):
            env.append(value)
        if env:
            task.arguments = "%s --env=%s" % (task.arguments, ",".join(env))
        task.save(using=request.database)
    # C
    elif action == "empty":
        if not request.user.has_perm("auth.run_db"):
            raise Exception("Missing execution privileges")
        task = Task(name="empty", submitted=now, status="Waiting", user=request.user)
        models = ",".join(args.getlist("models"))
        if models:
            task.arguments = "--models=%s" % (models)
        task.save(using=request.database)
    # D
    elif action == "loaddata":
        if not request.user.has_perm("auth.run_db"):
            raise Exception("Missing execution privileges")
        task = Task(
            name="loaddata",
            submitted=now,
            status="Waiting",
            user=request.user,
            arguments=args["fixture"],
        )
        task.save(using=request.database)
        # Also run the workflow upon loading of manufacturing_demo or distribution_demo
        if args.get("regenerateplan", False) == "true":
            active_modules = "supply"
            task = Task(
                name="runplan", submitted=now, status="Waiting", user=request.user
            )
            task.arguments = "--constraint=15 --plantype=1 --env=%s --background" % (
                active_modules,
            )
            task.save(using=request.database)
    # E
    elif action == "scenario_copy":
        worker_database = DEFAULT_DB_ALIAS
        if "copy" in args:
            if not request.user.has_perm("common.copy_scenario"):
                raise Exception("Missing execution privileges")
            source = args.get("source", request.database)
            worker_database = source
            destination = args.get("destination", False)
            dumpfile = args.get("dumpfile")
            if destination and destination != DEFAULT_DB_ALIAS:
                force = args.get("force", False)
                arguments = "%s %s" % (source, destination)
                if dumpfile:
                    arguments = "--dumpfile=%s %s" % (dumpfile, arguments)
                if force:
                    arguments += " --force"
                task = Task(
                    name="scenario_copy",
                    submitted=now,
                    status="Waiting",
                    user=request.user,
                    arguments=arguments,
                )
                task.save(using=source)
        elif "release" in args:
            if not request.user.has_perm("common.release_scenario"):
                raise Exception("Missing execution privileges")

            worker_database = request.database

            if request.database != DEFAULT_DB_ALIAS:
                task = Task(
                    name="scenario_release",
                    submitted=now,
                    status="Waiting",
                    user=request.user,
                    arguments="--database=%s"
                    % (args["database"] if "database" in args else request.database,),
                )
                task.save(using=request.database)
        elif "promote" in args:
            if not request.user.has_perm("common.promote_scenario"):
                raise Exception("Missing execution privileges")
            source = args.get("source", request.database)
            worker_database = source
            destination = args.get("destination", False)
            if destination and destination == DEFAULT_DB_ALIAS:
                arguments = "--promote %s %s" % (source, destination)
                task = Task(
                    name="scenario_copy",
                    submitted=now,
                    status="Waiting",
                    user=request.user,
                    arguments=arguments,
                )
                task.save(using=source)
        elif "update" in args:
            # Note: update is immediate and synchronous.
            if not request.user.has_perm("common.release_scenario"):
                raise Exception("Missing execution privileges")
            scenario = args["scenario"]
            sc = Scenario.objects.using(DEFAULT_DB_ALIAS).get(name=scenario)
            sc.description = args.get("description", None)
            sc.save(update_fields=["description"], using=DEFAULT_DB_ALIAS)
        else:
            raise Exception("Invalid scenario task")
    # G
    elif action == "createbuckets":
        if not request.user.has_perm("auth.run_db"):
            raise Exception("Missing execution privileges")
        task = Task(
            name="createbuckets", submitted=now, status="Waiting", user=request.user
        )
        arguments = []
        start = args.get("start", None)
        if start:
            arguments.append("--start=%s" % start)
        end = args.get("end", None)
        if end:
            arguments.append("--end=%s" % end)
        weekstart = args.get("weekstart", None)
        if weekstart:
            arguments.append("--weekstart=%s" % weekstart)
        format_day = args.get("format-day", None)
        if format_day:
            arguments.append('--format-day="%s"' % format_day)
        format_week = args.get("format-week", None)
        if format_week:
            arguments.append('--format-week="%s"' % format_week)
        format_month = args.get("format-month", None)
        if format_month:
            arguments.append('--format-month="%s"' % format_month)
        format_quarter = args.get("format-quarter", None)
        if format_quarter:
            arguments.append('--format-quarter="%s"' % format_quarter)
        format_year = args.get("format-year", None)
        if format_year:
            arguments.append('--format-year="%s"' % format_year)
        if arguments:
            task.arguments = " ".join(arguments)
        task.save(using=request.database)
    else:
        # Generic task wrapper

        # Find the command and verify we have permissions to run it
        command = None
        for commandname, appname in get_commands().items():
            if commandname == action:
                try:
                    c = getattr(
                        import_module(
                            "%s.management.commands.%s" % (appname, commandname)
                        ),
                        "Command",
                    )
                    if c.index >= 0:
                        if getattr(c, "getHTML", None) and c.getHTML(request):
                            # Command class has getHTML method
                            command = c
                            break
                        else:
                            for p in c.__bases__:
                                # Parent command class has getHTML method
                                if getattr(p, "getHTML", None) and p.getHTML(request):
                                    command = c
                                    break
                            if command:
                                break
                except Exception:
                    pass  # Silently ignore failures
        if not command:
            raise Exception("Invalid task name '%s'" % action)
        # Create a task
        arguments = []
        for arg, val in args.lists():
            if arg != "csrfmiddlewaretoken":
                arguments.append("--%s=%s" % (arg, shlex.quote(",".join(val))))
        task = Task(name=action, submitted=now, status="Waiting", user=request.user)
        if arguments:
            task.arguments = " ".join(arguments)
        task.save(using=request.database)

    # Launch a worker process
    if task:
        launchWorker(database=worker_database)
    return task


@staff_member_required
@never_cache
@csrf_protect
def CancelTask(request, taskid):
    # Allow only post
    if (
        request.method != "POST"
        or request.headers.get("x-requested-with") != "XMLHttpRequest"
    ):
        raise Http404("Only ajax post requests allowed")
    try:
        task = Task.objects.all().using(request.database).get(pk=taskid)
        if task.processid:
            # Kill the process with signal 9
            os.kill(task.processid, 9)
            task.message = "Canceled process"
            task.processid = None
        elif task.status != "Waiting":
            return HttpResponseServerError("Task isn't running or waiting to run")
        task.status = "Canceled"
        task.save(using=request.database)
        # Just in case, to cover corner cases
        launchWorker(database=request.database)
        return HttpResponse(content="OK")
    except ProcessLookupError:
        # Already dead, just clean up from task table
        task.message = "Canceled process"
        task.processid = None
        task.status = "Canceled"
        task.save(using=request.database)
        return HttpResponse(content="OK")
    except PermissionError:
        if os.name == "nt":
            # Windows doesn't report us why it failed. We just clean things up.
            task.message = "Canceled process"
            task.processid = None
            task.status = "Canceled"
            task.save(using=request.database)
            return HttpResponse(content="OK")
        else:
            return HttpResponseServerError("No permission to kill this task")
    except Exception as e:
        if os.name == "nt":
            # Windows doesn't report us why it failed. We just clean things up.
            task.message = "Canceled process"
            task.processid = None
            task.status = "Canceled"
            task.save(using=request.database)
            return HttpResponse(content="OK")
        else:
            logger.error("Error canceling task: %s" % e)
            return HttpResponseServerError("Error canceling task")


@staff_member_required
@never_cache
def DownloadLogFile(request, taskid):
    filename = Task.objects.using(request.database).get(id=taskid).logfile
    if (
        filename.lower().endswith(".dump")
        and request.user.username not in settings.SUPPORT_USERS
    ) or not filename.lower().endswith((".log", ".dump")):
        return HttpResponseNotFound(force_str(_("Error")))
    return sendStaticFile(
        request,
        settings.FREPPLE_LOGDIR,
        filename,
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Disposition": 'inline; filename="%s"' % filename,
        },
    )


@staff_member_required
@never_cache
def DeleteLogFile(request, taskid):
    if request.method != "POST":
        return HttpResponseNotAllowed(
            ["post"], content="Only POST request method is allowed"
        )
    filename = Task.objects.using(request.database).get(id=taskid).logfile
    if (
        filename.lower().endswith(".dump")
        and request.user.username not in settings.SUPPORT_USERS
    ) or not filename.lower().endswith((".log", ".dump")):
        return HttpResponseNotFound(force_str(_("Error")))
    try:
        os.remove(os.path.join(settings.FREPPLE_LOGDIR, filename))
        Task.objects.using(request.database).filter(id=taskid).update(logfile=None)
        return HttpResponse(content="OK")
    except Exception as e:
        logger.error("Couldn't delete log file: %s" % e)
        return HttpResponseForbidden(force_str(_("Couldn't delete file")))


@staff_member_required
@never_cache
def logfile(request, taskid):
    """
    This view shows the frePPLe log file of the last planning run in this database.
    """
    try:
        filename = Task.objects.using(request.database).get(id=taskid).logfile
        if not filename.lower().endswith(".log"):
            return HttpResponseNotFound(force_str(_("Error")))

        f = open(os.path.join(settings.FREPPLE_LOGDIR, filename), "rb")
    except Exception:
        logdata = "File not found"
    else:
        try:
            f.seek(-1, os.SEEK_END)
            if f.tell() >= 50000:
                # Too big to display completely
                f.seek(-50000, os.SEEK_END)
                d = f.read(50000)
                d = d[d.index(b"\n") :]  # Strip the first, incomplete line
                logdata = (
                    force_str(_("Displaying only the last 50K from the log file"))
                    + "...\n\n..."
                    + d.decode("utf8", "ignore")
                )
            else:
                # Displayed completely
                f.seek(0, os.SEEK_SET)
                logdata = f.read(50000).decode("utf8", "ignore")
        finally:
            f.close()

    return render(
        request,
        "execute/logfrepple.html",
        {
            "title": " ".join([force_str(capfirst(_("log file"))), taskid]),
            "logdata": logdata,
            "taskid": taskid,
        },
    )


class FileManager:
    """
    Class to upload and download files from a folder.
    The folder code argument indicates which folder to use:
    - 0: file upload folder
    - 1: export subdirectory of the file upload folder
    """

    all_extensions = (
        ".xlsx",
        ".xlsm",
        ".csv",
        ".csv.gz",
        ".cpy",
        ".cpy.gz",
        ".sql",
        ".sql.gz",
    )

    @staticmethod
    def getFolderInfo(request, foldercode):
        if foldercode == "0":
            # File upload folder
            return (
                settings.DATABASES[request.database]["FILEUPLOADFOLDER"],
                FileManager.all_extensions,
            )
        elif foldercode == "1":
            # Export folder
            return (
                os.path.join(
                    settings.DATABASES[request.database]["FILEUPLOADFOLDER"], "export"
                ),
                None,  # No upload here
            )
        else:
            raise Http404("Invalid folder code")

    @staticmethod
    def cleanFolder(foldercode, database=DEFAULT_DB_ALIAS):
        if foldercode == 0:
            folder = settings.DATABASES[database]["FILEUPLOADFOLDER"]
            extensions = FileManager.all_extensions
        elif foldercode == 1:
            folder = os.path.join(
                settings.DATABASES[database]["FILEUPLOADFOLDER"], "export"
            )
            extensions = None
        else:
            raise Exception("Invalid folder code")
        if os.path.isdir(folder):
            for filename in os.listdir(folder):
                if (
                    not extensions or filename.lower().endswith(extensions)
                ) and not filename.lower().endswith(".log"):
                    try:
                        os.remove(os.path.join(folder, filename))
                    except Exception:
                        pass

    @staticmethod
    @csrf_exempt
    @basicauthentication(allow_logged_in=True)
    @staff_member_required
    @never_cache
    def uploadFiletoFolder(request, foldercode):
        if request.method != "POST":
            return HttpResponseNotAllowed(
                ["post"], content="Only POST request method is allowed"
            )

        if len(list(request.FILES.items())) == 0:
            return HttpResponseNotFound("Missing file selection in request")
        errorcount = 0
        response = HttpResponse()
        folder, extensions = FileManager.getFolderInfo(request, foldercode)

        # Try to create the upload if doesn't exist yet
        if not os.path.isdir(settings.DATABASES[request.database]["FILEUPLOADFOLDER"]):
            try:
                os.makedirs(settings.DATABASES[request.database]["FILEUPLOADFOLDER"])
            except Exception:
                errorcount += 1
                response.write("Upload folder doesn't exist")

        if not errorcount:
            # Directory exists and we can upload files into it
            for filename, content in request.FILES.items():
                try:
                    # Validate file name
                    clean_filename = re.split(r"/|:|\\", filename)[-1]
                    cleanpath = os.path.normpath(os.path.join(folder, clean_filename))
                    if (
                        not cleanpath.startswith(folder)
                        or not extensions
                        or not clean_filename.lower().endswith(extensions)
                    ):
                        logger.error(
                            "Failed file upload: incorrect file name '%s'" % filename
                        )
                        response.write(
                            "%s: %s\n"
                            % (
                                clean_filename,
                                _("Filename extension must be among %(ext)s")
                                % {"ext": ", ".join(extensions)},
                            )
                        )
                        errorcount += 1
                        continue

                    # Write to a file
                    with open(cleanpath, "wb") as thetarget:
                        for chunk in content.chunks():
                            thetarget.write(chunk)

                    response.write(
                        force_str(
                            "%s: <strong>%s</strong><br>" % (clean_filename, _("OK"))
                        )
                    )
                except Exception as e:
                    logger.error("Failed file upload: %s" % e)
                    response.write(
                        "%s: <strong>%s</strong><br>"
                        % (clean_filename, _("Upload failed"))
                    )
                    errorcount += 1
            response.write(force_str("%s" % capfirst(_("finished"))))
        if errorcount:
            response.status_code = 400
            response.reason_phrase = "%s files failed to upload correctly" % errorcount
        return response

    @staticmethod
    @csrf_exempt
    @basicauthentication(allow_logged_in=True)
    @staff_member_required
    @never_cache
    def deleteFilefromFolder(request, foldercode, files):
        if request.method != "DELETE":
            return HttpResponseNotAllowed(
                ["delete"], content="Only DELETE request method is allowed"
            )
        folder, extensions = FileManager.getFolderInfo(request, foldercode)
        if extensions is None:
            extensions = FileManager.all_extensions

        fileerrors = force_str(_("Error deleting file"))
        errorcount = 0
        filelist = list()
        if files == "AllFiles":
            if os.path.isdir(folder):
                for filename in os.listdir(folder):
                    clean_filename = re.split(r"/|:|\\", filename)[-1]
                    if clean_filename.lower().endswith(
                        extensions
                    ) and not clean_filename.lower().endswith(".log"):
                        filelist.append(clean_filename)
        else:
            clean_filename = re.split(r"/|:|\\", files)[-1]
            if os.path.isdir(folder):
                filelist.append(clean_filename)
            else:
                logger.error("Failed file deletion: folder does not exist")
                errorcount += 1
                fileerrors = fileerrors + " / " + clean_filename

        for clean_filename in filelist:
            try:
                cleanpath = os.path.normpath(os.path.join(folder, clean_filename))
                if cleanpath.startswith(folder):
                    os.remove(cleanpath)
            except FileNotFoundError:
                logger.error("Failed file deletion: file does not exist")
            except Exception as e:
                logger.error("Failed file deletion: %s" % e)
                errorcount += 1
                fileerrors = fileerrors + " / " + clean_filename

        if errorcount > 0:
            return HttpResponseServerError(fileerrors)
        else:
            return HttpResponse(content="OK")

    @staticmethod
    @csrf_exempt
    @basicauthentication(allow_logged_in=True)
    @staff_member_required
    @never_cache
    def downloadFilefromFolder(request, foldercode, filename=None):
        if request.method != "GET":
            return HttpResponseNotAllowed(
                ["get"], content="Only GET request method is allowed"
            )
        folder, extensions = FileManager.getFolderInfo(request, foldercode)
        if not extensions:
            extensions = FileManager.all_extensions
        if filename:
            # Download a single file
            try:
                clean_filename = re.split(r"/|:|\\", filename)[0]
                cleanpath = os.path.normpath(os.path.join(folder, clean_filename))
                if not cleanpath.startswith(folder):
                    logger.warning("Failed file download: %s" % filename)
                    return HttpResponseNotFound(force_str(_("Error")))
                if not os.path.isfile(cleanpath):
                    if os.path.isfile("%s.gz" % cleanpath):
                        # File exists in compressed format
                        clean_filename = "%s.gz" % clean_filename
                    else:
                        logger.warning("Failed file download: %s" % filename)
                        return HttpResponseNotFound(force_str(_("Error")))
                return sendStaticFile(
                    request,
                    folder,
                    clean_filename,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Content-Disposition": 'inline; filename="%s"' % clean_filename,
                    },
                )
            except Exception as e:
                logger.error("Failed file download: %s" % e)
                return HttpResponseNotFound(force_str(_("Error")))
        else:
            # Download all files
            b = BytesIO()
            with ZipFile(file=b, mode="w", compression=ZIP_DEFLATED) as zf:
                if os.path.isdir(folder):
                    for filename in os.listdir(folder):
                        fullfilename = os.path.join(folder, filename)
                        if filename.endswith(extensions) and os.access(
                            fullfilename, os.R_OK
                        ):
                            if filename.endswith(".gz"):
                                # Put the uncompressed file in the zip file
                                with gzip.open(fullfilename, "rb") as datafile:
                                    zf.writestr(
                                        os.path.basename(filename[:-3]),
                                        datafile.read(),
                                    )
                            else:
                                zf.write(
                                    filename=fullfilename,
                                    arcname=os.path.basename(filename),
                                )
            response = HttpResponse(b.getvalue(), content_type="application/zip")
            response["Content-Disposition"] = 'attachment; filename="frepple.zip"'
            return response


@staff_member_required
@never_cache
def scheduletasks(request):
    if request.headers.get(
        "x-requested-with"
    ) != "XMLHttpRequest" or request.method not in ("POST", "DELETE"):
        return HttpResponseNotAllowed("Only post and delete ajax requests are allowed")
    try:
        data = json.loads(request.body.decode(request.encoding))
        oldname = data.get("oldname", None)
        name = data.get("name", None)
        if not name and not oldname:
            return HttpResponse("Missing name attribute", status=400)
        elif request.method == "POST":
            if not request.user.has_perm("execute.add_scheduledtask"):
                return HttpResponse("Couldn't add or update scheduled task", status=401)
            obj, created = ScheduledTask.objects.using(request.database).get_or_create(
                name=oldname if oldname else name
            )
            if created:
                obj.user = request.user
            elif (
                not request.user.is_superuser
                and obj.user.username != request.user.username
            ):
                return HttpResponse(
                    "This task can only be updated by superusers and %s"
                    % obj.user.username,
                    status=401,
                )
            fld = data.get("email_failure", None)
            if fld:
                obj.email_failure = fld
            fld = data.get("email_success", None)
            if fld:
                obj.email_success = fld
            fld = data.get("data", None)
            if isinstance(fld, dict):
                obj.data = fld
            if oldname and name and oldname != name:
                # Rename the task
                obj.name = name
                ScheduledTask.objects.using(request.database).filter(
                    name=oldname
                ).delete()
            obj.adjustForTimezone(-GridReport.getTimezoneOffset(request))
            obj.save(using=request.database)
            call_command("scheduletasks", database=request.database)
            obj.adjustForTimezone(GridReport.getTimezoneOffset(request))
            return HttpResponse(
                content=obj.next_run.strftime("%Y-%m-%d %H:%M:%S")
                if obj.next_run
                else ""
            )
        elif request.method == "DELETE":
            if not request.user.has_perm("execute.delete_scheduledtask"):
                return HttpResponse("Couldn't delete scheduled task", status=401)
            elif (
                ScheduledTask.objects.using(request.database)
                .filter(name=name)
                .delete()[0]
            ):
                return HttpResponse(content="OK")
            else:
                return HttpResponse("Couldn't delete scheduled task", status=400)
    except Exception as e:
        logger.error("Error updating scheduled task: %s" % e)
        return HttpResponseServerError("Error updating scheduled task")


def exportWorkbook(request):
    # Create a workbook
    wb = Workbook(write_only=True)

    # Create a named style for the header row
    headerstyle = NamedStyle(name="headerstyle")
    headerstyle.fill = PatternFill(fill_type="solid", fgColor="70c4f4")
    wb.add_named_style(headerstyle)
    readlonlyheaderstyle = NamedStyle(name="readlonlyheaderstyle")
    readlonlyheaderstyle.fill = PatternFill(fill_type="solid", fgColor="d0ebfb")
    wb.add_named_style(readlonlyheaderstyle)

    # Loop over all selected entity types
    exportConfig = {"anonymous": request.POST.get("anonymous", False)}
    ok = False
    for entity_name in request.POST.getlist("entities"):
        try:
            # Initialize
            (app_label, model_label) = entity_name.split(".")
            model = apps.get_model(app_label, model_label)
            # Verify access rights
            permname = get_permission_codename("change", model._meta)
            if not request.user.has_perm("%s.%s" % (app_label, permname)):
                continue

            # Never export some special administrative models
            if model in EXCLUDE_FROM_BULK_OPERATIONS:
                continue

            # Create sheet
            ok = True
            ws = wb.create_sheet(title=force_str(model._meta.verbose_name))

            # Build a list of fields and properties
            fields = []
            modelfields = []
            header = []
            source = False
            lastmodified = False
            owner = False
            comment = None
            try:
                # The admin model of the class can define some fields to exclude from the export
                exclude = data_site._registry[model].exclude
            except Exception:
                exclude = None
            for i in model._meta.fields:
                if isinstance(i, AutoField) and i.primary_key:
                    # Don't export automatically generated primary keys.
                    # We rely on the natural for restoring the data.
                    continue
                elif i.name in ["lft", "rght", "lvl"]:
                    continue  # Skip some fields of HierarchyModel
                elif i.name == "source":
                    source = i  # Put the source field at the end
                elif i.name == "lastmodified":
                    lastmodified = i  # Put the last-modified field at the very end
                elif not (exclude and i.name in exclude):
                    fields.append(i.column)
                    modelfields.append(i)
                    cell = WriteOnlyCell(ws, value=force_str(i.verbose_name).title())
                    if i.editable:
                        cell.style = "headerstyle"
                        if isinstance(i, ForeignKey):
                            cell.comment = CellComment(
                                force_str(
                                    _("Values in this field must exist in the %s table")
                                    % force_str(i.remote_field.model._meta.verbose_name)
                                ),
                                "Author",
                            )
                        elif i.choices:
                            cell.comment = CellComment(
                                force_str(
                                    _("Accepted values are: %s")
                                    % ", ".join([c[0] for c in i.choices])
                                ),
                                "Author",
                            )
                    else:
                        cell.style = "readlonlyheaderstyle"
                        if not comment:
                            comment = CellComment(
                                force_str(_("Read only")),
                                "Author",
                                height=20,
                                width=80,
                            )
                        cell.comment = comment
                    header.append(cell)
                    if i.name == "owner":
                        owner = True
            if hasattr(model, "propertyFields"):
                if callable(model.propertyFields):
                    props = model.propertyFields(request)
                else:
                    props = model.propertyFields
                for i in props:
                    if i.export:
                        fields.append(i.name)
                        cell = WriteOnlyCell(
                            ws, value=force_str(i.verbose_name).title()
                        )
                        if i.editable:
                            cell.style = "headerstyle"
                            if isinstance(i, ForeignKey):
                                cell.comment = CellComment(
                                    force_str(
                                        _(
                                            "Values in this field must exist in the %s table"
                                        )
                                        % force_str(
                                            i.remote_field.model._meta.verbose_name
                                        )
                                    ),
                                    "Author",
                                )
                        elif i.choices:
                            cell.comment = CellComment(
                                force_str(
                                    _("Accepted values are: %s")
                                    % ", ".join([c[0] for c in i.choices])
                                ),
                                "Author",
                            )
                        else:
                            cell.style = "readlonlyheaderstyle"
                            if not comment:
                                comment = CellComment(
                                    force_str(_("Read only")),
                                    "Author",
                                    height=20,
                                    width=80,
                                )
                            cell.comment = comment
                        header.append(cell)
                        modelfields.append(i)
            if source:
                fields.append("source")
                cell = WriteOnlyCell(ws, value=force_str(_("source")).title())
                cell.style = "headerstyle"
                header.append(cell)
                modelfields.append(source)
            if lastmodified:
                fields.append("lastmodified")
                cell = WriteOnlyCell(ws, value=force_str(_("last modified")).title())
                cell.style = "readlonlyheaderstyle"
                if not comment:
                    comment = CellComment(
                        force_str(_("Read only")), "Author", height=20, width=80
                    )
                cell.comment = comment
                header.append(cell)
                modelfields.append(lastmodified)

            # Write a formatted header row
            ws.append(header)

            # Add an auto-filter to the table
            ws.auto_filter.ref = "A1:%s1048576" % get_column_letter(len(header))

            # Use the default manager
            if issubclass(model, HierarchyModel):
                model.rebuildHierarchy(database=request.database)
                query = (
                    model.objects.all().using(request.database).order_by("lvl", "pk")
                )
            elif owner:
                # First export records with empty owner field
                query = (
                    model.objects.all().using(request.database).order_by("-owner", "pk")
                )
            else:
                query = model.objects.all().using(request.database).order_by("pk")

            # Special annotation of the export query
            if hasattr(model, "export_objects"):
                query = model.export_objects(query, request)

            # Loop over all records
            for rec in query.values_list(*fields):
                cells = []
                fld = 0
                for f in rec:
                    cells.append(
                        _getCellValue(
                            f, field=modelfields[fld], exportConfig=exportConfig
                        )
                    )
                    fld += 1
                ws.append(cells)
        except Exception:
            pass  # Silently ignore the error and move on to the next entity.

    # Not a single entity to export
    if not ok:
        raise Exception(_("Nothing to export"))

    # Write the excel from memory to a string and then to a HTTP response
    output = BytesIO()
    wb.save(output)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        content=output.getvalue(),
    )
    response["Content-Disposition"] = 'attachment; filename="frepple.xlsx"'
    response["Cache-Control"] = "no-cache, no-store"
    return response


def importWorkbook(request):
    """
    This method reads a spreadsheet in Office Open XML format (typically with
    the extension .xlsx or .ods).
    Each entity has a tab in the spreadsheet, and the first row contains
    the fields names.
    """
    # Build a list of all contenttypes
    all_models = [
        (ct.model_class(), ct.pk)
        for ct in ContentType.objects.all()
        if ct.model_class()
    ]
    try:
        # Find all models in the workbook
        for filename, file in request.FILES.items():
            yield "<strong>" + force_str(
                _("Processing file")
            ) + " " + filename + "</strong><br>"
            if filename.endswith(".xls"):
                yield _(
                    "Files in the old .XLS excel format can't be read.<br>Please convert them to the new .XLSX format."
                )
                continue
            elif (
                file.content_type
                != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ):
                yield _("Unsupported file format.")
                continue
            wb = load_workbook(filename=file, data_only=True)
            models = []
            for ws_name in wb.sheetnames:
                # Find the model
                model = None
                contenttype_id = None
                for m, ct in all_models:
                    if matchesModelName(ws_name, m):
                        model = m
                        contenttype_id = ct
                        break
                if not model or model in EXCLUDE_FROM_BULK_OPERATIONS:
                    yield '<div class="alert alert-warning">' + force_str(
                        _("Ignoring data in worksheet: %s") % ws_name
                    ) + "</div>"
                elif not request.user.has_perm(
                    "%s.%s"
                    % (
                        model._meta.app_label,
                        get_permission_codename("add", model._meta),
                    )
                ):
                    # Check permissions
                    yield '<div class="alert alert-danger">' + force_str(
                        _("You don't permissions to add: %s") % ws_name
                    ) + "</div>"
                else:
                    deps = set([model])
                    GridReport.dependent_models(model, deps)
                    models.append((ws_name, model, contenttype_id, deps))

            # Sort the list of models, based on dependencies between models
            models = GridReport.sort_models(models)

            # Process all rows in each worksheet
            yield (
                '<div class="table-responsive">'
                '<table class="table table-condensed" style="white-space: nowrap;"><tbody>'
            )
            for ws_name, model, contenttype_id, dependencies in models:
                with transaction.atomic(using=request.database):
                    yield '<tr style="text-align: center"><th colspan="5">%s %s<div class="recordcount pull-right"></div></th></tr>' % (
                        capfirst(_("worksheet")),
                        ws_name,
                    )
                    numerrors = 0
                    numwarnings = 0
                    firsterror = True
                    ws = wb[ws_name]
                    for error in parseExcelWorksheet(
                        model,
                        ws,
                        user=request.user,
                        database=request.database,
                        ping=True,
                    ):
                        if error[0] == logging.DEBUG:
                            # Yield some result so we can detect disconnect clients and interrupt the upload
                            yield "<tr class='hidden' data-cnt='%s'>" % error[1]
                            continue
                        if firsterror and error[0] in (logging.ERROR, logging.WARNING):
                            yield '<tr><th class="sr-only">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s%s%s</th></tr>' % (
                                capfirst(_("worksheet")),
                                capfirst(_("row")),
                                capfirst(_("field")),
                                capfirst(_("value")),
                                capfirst(_("error")),
                                " / ",
                                capfirst(_("warning")),
                            )
                            firsterror = False
                        if error[0] == logging.ERROR:
                            yield '<tr><td class="sr-only">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s: %s</td></tr>' % (
                                ws_name,
                                error[1] if error[1] else "",
                                error[2] if error[2] else "",
                                error[3] if error[3] else "",
                                capfirst(_("error")),
                                error[4],
                            )
                            numerrors += 1
                        elif error[1] == logging.WARNING:
                            yield '<tr><td class="sr-only">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s: %s</td></tr>' % (
                                ws_name,
                                error[1] if error[1] else "",
                                error[2] if error[2] else "",
                                error[3] if error[3] else "",
                                capfirst(_("warning")),
                                error[4],
                            )
                            numwarnings += 1
                        else:
                            yield '<tr class=%s><td class="sr-only">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                                "danger" if numerrors > 0 else "success",
                                ws_name,
                                error[1] if error[1] else "",
                                error[2] if error[2] else "",
                                error[3] if error[3] else "",
                                error[4],
                            )
            yield "</tbody></table></div>"
            yield "<div><strong>%s</strong><br><br></div>" % _("Done")
    except GeneratorExit:
        logger.warning("Connection Aborted")
    except Exception as e:
        yield "Import aborted: %s" % e
        logger.error("Exception importing workbook: %s" % e)
