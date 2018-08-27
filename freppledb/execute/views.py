#
# Copyright (C) 2007-2013 by frePPLe bvba
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

import json
import os
import sys
import re
from datetime import datetime
from subprocess import Popen
from importlib import import_module
import operator

from django.conf import settings
from django.views import static
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.db import DEFAULT_DB_ALIAS
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponse
from django.http import HttpResponseNotFound, StreamingHttpResponse, HttpResponseNotAllowed
from django.contrib import messages
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.core.management import get_commands

from freppledb.execute.models import Task
from freppledb.common.auth import basicauthentication
from freppledb.common.models import Scenario
from freppledb.common.report import exportWorkbook, importWorkbook
from freppledb.common.report import GridReport, GridFieldDateTime, GridFieldText, GridFieldInteger
from freppledb.execute.management.commands.runworker import checkActive

import logging
logger = logging.getLogger(__name__)


class TaskReport(GridReport):
  '''
  A list report to review the history of actions.
  '''
  template = 'execute/execute.html'
  title = _('Task status')
  basequeryset = Task.objects.all()
  model = Task
  frozenColumns = 0
  multiselect = False
  editable = False
  height = 150
  default_sort = (0, 'desc')
  help_url = 'user-guide/user-interface/execute.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), editable=False, align='center'),
    GridFieldDateTime('submitted', title=_('submitted'), editable=False, align='center'),
    GridFieldDateTime('started', title=_('started'), editable=False, align='center'),
    GridFieldDateTime('finished', title=_('finished'), editable=False, align='center'),
    GridFieldText('status', title=_('status'), editable=False, align='center', extra="formatter:status"),
    GridFieldText('logfile', title=_('log file'), width=80, editable=False, align='center', extra="formatter:logbutton"),
    GridFieldText('message', title=_('message'), editable=False, width=500, formatter='longstring'),
    GridFieldText('arguments', title=_('arguments'), editable=False),
    #. Translators: Translation included with Django
    GridFieldText('user', title=_('user'), field_name='user__username', editable=False, align='center'),
    )


  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    # Loop over all accordion of all apps and directories
    accordions = set()
    accord = ''
    for commandname, appname in get_commands().items():
      try:
        accord = getattr(import_module('%s.management.commands.%s' % (appname, commandname)), 'Command')
        if accord.index >= 0 and getattr(accord, 'getHTML', None):
          accordions.add(accord)
      except Exception:
        pass  # Silently ignore failures

    accordions = sorted(accordions, key=operator.attrgetter('index'))

    # Send to template
    return {'commandlist': accordions}


  @classmethod
  def query(reportclass, request, basequery, sortsql='1 asc'):
    logfileslist = set([x for x in os.listdir(settings.FREPPLE_LOGDIR) if x.endswith('.log')])
    for rec in basequery:
      yield {
        'id': rec.id,
        'name': rec.name,
        'submitted': rec.submitted,
        'started': rec.started,
        'finished': rec.finished,
        'status': rec.status,
        'logfile': rec.logfile if rec.logfile in logfileslist else None,
        'message': rec.message,
        'arguments': rec.arguments,
        'user__username': rec.user.username if rec.user else None
        }


  @classmethod
  def extraJSON(reportclass, request):
    try:
      lastCompletedTask = Task.objects.all().using(request.database).filter(status='Done').order_by('-id').only('id')[0]
      return '"lastcompleted":%d,\n' % lastCompletedTask.id
    except:
      return '"lastcompleted":0,\n'


@csrf_exempt
@basicauthentication(allow_logged_in=True)
def APITask(request, action):
  try:
    if action == 'status':
      response = {}
      args = request.GET.getlist('id')
      if args:
        tasks = Task.objects.all().using(request.database).filter(id__in=args)
      else:
        tasks = Task.objects.all().using(request.database).filter(finished__isnull=True).exclude(status='Canceled')
      for t in tasks:
        response[t.id] = {
          'name': t.name, 'submitted': str(t.submitted),
          'started': str(t.started), 'finished': str(t.finished),
          'arguments': t.arguments, 'status': t.status,
          'message': t.message, 'user': t.user.username if t.user else None,
          'logfile': t.logfile
          }
    else:
      task = wrapTask(request, action)
      if task:
        response = {'taskid': task.id, 'message': 'Successfully launched task'}
      else:
        response = {'message': "No task was launched"}
  except Exception as e:
    response = {'message': 'Exception launching task: %s' % e}
  return HttpResponse(json.dumps(response), content_type="application/json")


@staff_member_required
@never_cache
@csrf_protect
def LaunchTask(request, action):
  try:
    if action == 'exportworkbook':
      return exportWorkbook(request)
    elif action == 'importworkbook':
      return StreamingHttpResponse(
        content_type='text/plain; charset=%s' % settings.DEFAULT_CHARSET,
        streaming_content=importWorkbook(request)
        )
    else:
      wrapTask(request, action)
      return HttpResponseRedirect('%s/execute/' % request.prefix)
  except Exception as e:
    messages.add_message(
      request, messages.ERROR,
      force_text(_('Failure launching action: %(msg)s') % {'msg': e})
      )
    return HttpResponseRedirect('%s/execute/' % request.prefix)


def wrapTask(request, action):
  # Allow only post
  if request.method != 'POST':
    raise Exception('Only post requests allowed')
  # Parse the posted parameters as arguments for an asynchronous task to add to the queue.    TODO MAKE MODULAR WITH SEPERATE TASK CLASS
  worker_database = request.database

  now = datetime.now()
  task = None
  args = request.POST or request.GET

  # A
  if action in ('frepple_run', 'runplan'):
    if not request.user.has_perm('auth.generate_plan'):
      raise Exception('Missing execution privileges')
    constraint = 0
    for value in args.getlist('constraint'):
      try:
        constraint += int(value)
      except:
        pass
    task = Task(name='runplan', submitted=now, status='Waiting', user=request.user)
    task.arguments = "--constraint=%s --plantype=%s" % (constraint, args.get('plantype', 1))
    env = []
    for value in args.getlist('env'):
      env.append(value)
    if env:
      task.arguments = "%s --env=%s" % (task.arguments, ','.join(env))
    request.session['env'] = env
    task.save(using=request.database)
    # Update the session object
    request.session['plantype'] = args.get('plantype')
    request.session['constraint'] = constraint
  # C
  elif action in ('frepple_flush', 'empty'):
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='empty', submitted=now, status='Waiting', user=request.user)
    models = ','.join(args.getlist('models'))
    if models:
      task.arguments = "--models=%s" % (models)
    task.save(using=request.database)
  # D
  elif action == 'loaddata':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='loaddata', submitted=now, status='Waiting', user=request.user, arguments=args['fixture'])
    task.save(using=request.database)
    # Also run the workflow upon loading of manufacturing_demo or distribution_demo
    if (args['regenerateplan'] == 'true'):
      active_modules = 'supply'
      task = Task(name='runplan', submitted=now, status='Waiting', user=request.user)
      task.arguments = "--constraint=15 --plantype=1 --env=%s --background" % (active_modules,)
      task.save(using=request.database)
  # E
  elif action in ('frepple_copy', 'scenario_copy'):
    worker_database = DEFAULT_DB_ALIAS
    if 'copy' in args:
      if not request.user.has_perm('auth.copy_scenario'):
        raise Exception('Missing execution privileges')
      source = args.get('source', DEFAULT_DB_ALIAS)
      worker_database = source
      destination = args.getlist('destination')
      force = args.get('force', False)
      for sc in Scenario.objects.all():
        arguments = "%s %s" % (source, sc.name)
        if force:
          arguments += ' --force'
        if args.get(sc.name, 'off') == 'on' or sc.name in destination:
          task = Task(name='scenario_copy', submitted=now, status='Waiting', user=request.user, arguments=arguments)
          task.save(using=source)
    elif 'release' in args:
      # Note: release is immediate and synchronous.
      if not request.user.has_perm('auth.release_scenario'):
        raise Exception('Missing execution privileges')
      for sc in Scenario.objects.all().using(DEFAULT_DB_ALIAS):
        if args.get(sc.name, 'off') == 'on' and sc.status != 'Free':
          sc.status = 'Free'
          sc.lastrefresh = now
          sc.save(using=DEFAULT_DB_ALIAS)
          if request.database == sc.name:
            # Erasing the database that is currently selected.
            request.prefix = ''
    elif 'update' in args:
      # Note: update is immediate and synchronous.
      if not request.user.has_perm('auth.release_scenario'):
        raise Exception('Missing execution privileges')
      for sc in Scenario.objects.all().using(DEFAULT_DB_ALIAS):
        if args.get(sc.name, 'off') == 'on':
          sc.description = args.get('description', None)
          sc.save(using=DEFAULT_DB_ALIAS)
    else:
      raise Exception('Invalid scenario task')
  # G
  elif action in ('frepple_createbuckets', 'createbuckets'):
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='createbuckets', submitted=now, status='Waiting', user=request.user)
    arguments = []
    start = args.get('start', None)
    if start:
      arguments.append("--start=%s" % start)
    end = args.get('end', None)
    if end:
      arguments.append("--end=%s" % end)
    weekstart = args.get('weekstart', None)
    if weekstart:
      arguments.append("--weekstart=%s" % weekstart)
    format_day = args.get('format-day', None)
    if format_day:
      arguments.append('--format-day="%s"' % format_day)
    format_week = args.get('format-week', None)
    if format_week:
      arguments.append('--format-week="%s"' % format_week)
    format_month = args.get('format-month', None)
    if format_month:
      arguments.append('--format-month="%s"' % format_month)
    format_quarter = args.get('format-quarter', None)
    if format_quarter:
      arguments.append('--format-quarter="%s"' % format_quarter)
    format_year = args.get('format-year', None)
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
          c = getattr(import_module('%s.management.commands.%s' % (appname, commandname)), 'Command')
          if c.index >= 0:
            if getattr(c, 'getHTML', None) and c.getHTML(request):
              # Command class has getHTML method
              command = c
              break
            else:
              for p in c.__bases__:
                # Parent command class has getHTML method
                if getattr(p, 'getHTML', None) and p.getHTML(request):
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
      if arg != 'csrfmiddlewaretoken':
        arguments.append('--%s=%s' % (arg, ','.join(val)))
    task = Task(name=action, submitted=now, status='Waiting', user=request.user)
    if arguments:
      task.arguments = " ".join(arguments)
    task.save(using=request.database)

  # Launch a worker process, making sure it inherits the right
  # environment variables from this parent
  os.environ['FREPPLE_CONFIGDIR'] = settings.FREPPLE_CONFIGDIR
  if task and not checkActive(worker_database):
    if os.path.isfile(os.path.join(settings.FREPPLE_APP, "frepplectl.py")):
      if "python" in sys.executable:
        # Development layout
        Popen([
          sys.executable,  # Python executable
          os.path.join(settings.FREPPLE_APP, "frepplectl.py"),
          "runworker",
          "--database=%s" % worker_database
          ])
      else:
        # Deployment on Apache web server
        Popen([
          "python",
          os.path.join(settings.FREPPLE_APP, "frepplectl.py"),
          "runworker",
          "--database=%s" % worker_database
          ], creationflags=0x08000000)
    elif sys.executable.find('freppleserver.exe') >= 0:
      # Py2exe executable
      Popen([
        sys.executable.replace('freppleserver.exe', 'frepplectl.exe'),  # frepplectl executable
        "runworker",
        "--database=%s" % worker_database
        ], creationflags=0x08000000)  # Do not create a console window
    else:
      # Linux standard installation
      Popen([
        "frepplectl",
        "runworker",
        "--database=%s" % worker_database
        ])
  return task


@staff_member_required
@never_cache
@csrf_protect
def CancelTask(request, taskid):
  # Allow only post
  if request.method != 'POST' or not request.is_ajax():
    raise Http404('Only ajax post requests allowed')
  try:
    task = Task.objects.all().using(request.database).get(pk=taskid)
    if task.name in ('frepple_run', 'runplan') and task.status.endswith("%"):
      fname = os.path.join(settings.FREPPLE_LOGDIR, task.logfile)
      try:
        # The second line in the log file has the id of the frePPLe process
        with open(fname, 'r') as f:
          t = 0
          for line in f:
            if t >= 1:
              t = line.split()
              break
            else:
              t += 1
          if t[0] == 'FrePPLe' and t[1] == 'with' and t[2] == 'processid':
            # Kill the process with signal 9
            os.kill(int(t[3]), 9)
            task.message = 'Killed process'
      except Exception as e:
        return HttpResponseServerError('Error canceling task')
    elif task.status != 'Waiting':
      raise Exception('Task is not in waiting status')
    task.status = 'Canceled'
    task.save(using=request.database)
    return HttpResponse(content="OK")
  except Exception as e:
    logger.error("Error saving report settings: %s" % e)
    return HttpResponseServerError('Error canceling task')


@staff_member_required
@never_cache
def DownloadLogFile(request, taskid):
  # if request.database == DEFAULT_DB_ALIAS:
  #   filename = 'frepple.log'
  # else:
  #   filename = 'frepple_%s.log' % request.database
  filename = Task.objects.using(request.database).get(id=taskid).logfile
  if not filename.lower().endswith('.log'):
    return HttpResponseNotFound(force_text(_('Error downloading file')))

  response = static.serve(
    request, filename,
    document_root=settings.FREPPLE_LOGDIR
    )
  response['Content-Disposition'] = 'inline; filename="%s"' % filename
  response['Content-Type'] = 'application/octet-stream'
  return response


@staff_member_required
@never_cache
def logfile(request, taskid):
  '''
  This view shows the frePPLe log file of the last planning run in this database.
  '''

  try:
    filename = Task.objects.using(request.database).get(id=taskid).logfile
    if not filename.lower().endswith('.log'):
      return HttpResponseNotFound(force_text(_('Error downloading file')))

    f = open(os.path.join(settings.FREPPLE_LOGDIR, filename), 'rb')
  except:
    logdata = "File not found"
  else:
    try:
      f.seek(-1, os.SEEK_END)
      if f.tell() >= 50000:
        # Too big to display completely
        f.seek(-50000, os.SEEK_END)
        d = f.read(50000)
        d = d[d.index(b'\n'):]  # Strip the first, incomplete line
        logdata = force_text(_("Displaying only the last 50K from the log file")) + '...\n\n...' + d.decode("utf8", "ignore")
      else:
        # Displayed completely
        f.seek(0, os.SEEK_SET)
        logdata = f.read(50000)
    finally:
      f.close()

  return render(request, 'execute/logfrepple.html', {
    'title': ' '.join([force_text(capfirst(_('log file'))), taskid]),
    'logdata': logdata,
    'taskid': taskid
    } )


class FileManager:
  '''
  Class to upload and download files from a folder.
  The folder code argument indicates which folder to use:
    - 0: file upload folder
    - 1: export subdirectory of the file upload folder
  '''

  @staticmethod
  def getFolderInfo(request, foldercode):
    if foldercode == '0':
      # File upload folder
      return (
        settings.DATABASES[request.database]['FILEUPLOADFOLDER'],
        ('.xlsx', '.csv', '.csv.gz')
        )
    elif foldercode == '1':
      # Export folder
      return (
        os.path.join(settings.DATABASES[request.database]['FILEUPLOADFOLDER'], 'export'),
        None  # No upload here
        )
    else:
      raise Http404('Invalid folder code')


  @staticmethod
  @csrf_exempt
  @basicauthentication(allow_logged_in=True)
  @staff_member_required
  @never_cache
  def uploadFiletoFolder(request, foldercode):
    if request.method != 'POST':
      return HttpResponseNotAllowed(['post'], content='Only POST request method is allowed')

    if len(list(request.FILES.items())) == 0:
      return HttpResponseNotFound('Missing file selection in request')
    errorcount = 0
    response = HttpResponse()
    folder, extensions = FileManager.getFolderInfo(request, foldercode)
    for filename, content in request.FILES.items():
      try:
        # Validate file name
        clean_filename = re.split(r'/|:|\\', filename)[-1]
        if not extensions or not clean_filename.lower().endswith(extensions):
          response.write('%s: %s\n' % (clean_filename, _("Filename extension must be among %(ext)s") % {"ext": ", ".join(extensions)}))
          errorcount += 1
          continue

        # Write to a file
        with open(os.path.join(folder, clean_filename), 'wb') as thetarget:
          for chunk in content.chunks():
            thetarget.write(chunk)

        response.write(force_text('%s: %s\n' % (clean_filename, _('OK'))))
      except Exception as e:
        logger.error("Failed file upload: %s" % e)
        response.write('%s: %s\n' % (clean_filename, _("Upload failed") ))
        errorcount += 1
    response.write(force_text('%s' % capfirst(_('finished'))))
    if errorcount:
      response.status_code = 400
      response.reason_phrase = '%s files failed to upload correctly' % errorcount
    return response


  @staticmethod
  @csrf_exempt
  @basicauthentication(allow_logged_in=True)
  @staff_member_required
  @never_cache
  def deleteFilefromFolder(request, foldercode, files):
    if request.method != 'DELETE':
      return HttpResponseNotAllowed(['delete'], content='Only DELETE request method is allowed')
    folder, extensions = FileManager.getFolderInfo(request, foldercode)

    if extensions is None:
      extensions = ('.csv', '.csv.gz', '.log')

    fileerrors = force_text(_('Error deleting file'))
    errorcount = 0
    filelist = list()
    if files == 'AllFiles':
      for filename in os.listdir(folder):
        clean_filename = re.split(r'/|:|\\', filename)[-1]
        if clean_filename.lower().endswith(extensions) and not clean_filename.lower().endswith('.log'):
          filelist.append(clean_filename)
    else:
      clean_filename = re.split(r'/|:|\\', files)[-1]
      filelist.append(clean_filename)

    for clean_filename in filelist:
      try:
        os.remove(os.path.join(folder, clean_filename))
      except Exception as e:
        logger.error("Failed file deletion: %s" % e)
        errorcount += 1
        fileerrors = fileerrors + ' / ' + clean_filename

    if errorcount > 0:
      return HttpResponseServerError(fileerrors)
    else:
      return HttpResponse(content="OK")

  @staticmethod
  @csrf_exempt
  @basicauthentication(allow_logged_in=True)
  @staff_member_required
  @never_cache
  def downloadFilefromFolder(request, foldercode, filename):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['get'], content='Only GET request method is allowed')
    folder = FileManager.getFolderInfo(request, foldercode)[0]

    try:
      clean_filename = filename.split('/')[0]
      response = static.serve(
        request, clean_filename, document_root=folder
        )
      response['Content-Disposition'] = 'inline; filename="%s"' % filename
      response['Content-Type'] = 'application/octet-stream'
      return response
    except Exception as e:
      logger.error("Failed file download: %s" % e)
      return HttpResponseNotFound(force_text(_('Error downloading file')))
