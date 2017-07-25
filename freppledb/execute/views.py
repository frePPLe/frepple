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
from time import localtime, strftime

from django.apps import apps
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

from freppledb.common.commands import PlanTaskRegistry
from freppledb.execute.models import Task
from freppledb.common.auth import basicauthentication
from freppledb.common.models import Scenario
from freppledb.common.report import exportWorkbook, importWorkbook
from freppledb.common.report import GridReport, GridFieldDateTime, GridFieldText, GridFieldInteger
from freppledb.execute.management.commands.frepple_runworker import checkActive

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
    GridFieldText('message', title=_('message'), editable=False, width=500, formatter='longstring'),
    GridFieldText('arguments', title=_('arguments'), editable=False),
    #. Translators: Translation included with Django
    GridFieldText('user', title=_('user'), field_name='user__username', editable=False, align='center'),
    )

  @classmethod
  def extra_context(reportclass, request, *args, **kwargs):
    try:
      constraint = int(request.session['constraint'])
    except:
      constraint = 15

    # Synchronize the scenario table with the settings
    Scenario.syncWithSettings()

    # Collect optional tasks
    PlanTaskRegistry.autodiscover()
    planning_options = PlanTaskRegistry.getLabels()

    # Loop over all fixtures of all apps and directories
    fixtures = set()
    folders = list(settings.FIXTURE_DIRS)
    for app in apps.get_app_configs():
      if not app.name.startswith('django'):
        folders.append(os.path.join(os.path.dirname(app.path), app.label, 'fixtures'))
    for f in folders:
      try:
        for root, dirs, files in os.walk(f):
          for i in files:
            if i.endswith('.json'):
              fixtures.add(i.split('.')[0])
      except:
        pass  # Silently ignore failures
    fixtures = sorted(fixtures)

    # Function to convert from bytes to human readabl format
    def sizeof_fmt(num):
      for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
          return "%3.1f%sB" % (num, unit)
        num /= 1024.0
      return "%.1f%sB" % (num, 'Yi')

    # List available data files
    filesexported = []
    if 'FILEUPLOADFOLDER' in settings.DATABASES[request.database]:
      exportfolder = os.path.join(settings.DATABASES[request.database]['FILEUPLOADFOLDER'], 'export')
      if os.path.isdir(exportfolder):
        for file in os.listdir(exportfolder):
          if file.endswith(('.csv', '.csv.gz', '.log')):
            filesexported.append([
              file,
              strftime("%Y-%m-%d %H:%M:%S",localtime(os.stat(os.path.join(exportfolder, file)).st_mtime)),
              sizeof_fmt(os.stat(os.path.join(exportfolder, file)).st_size)
              ])

    filestoupload = []
    if 'FILEUPLOADFOLDER' in settings.DATABASES[request.database]:
      uploadfolder = settings.DATABASES[request.database]['FILEUPLOADFOLDER']
      if os.path.isdir(uploadfolder):
        for file in os.listdir(uploadfolder):
          if file.endswith(('.csv', '.csv.gz', '.log')):
            filestoupload.append([
              file,
              strftime("%Y-%m-%d %H:%M:%S",localtime(os.stat(os.path.join(uploadfolder, file)).st_mtime)),
              sizeof_fmt(os.stat(os.path.join(uploadfolder, file)).st_size)
              ])

    # Send to template
    return {
      'capacityconstrained': constraint & 4,
      'materialconstrained': constraint & 2,
      'leadtimeconstrained': constraint & 1,
      'fenceconstrained': constraint & 8,
      'scenarios': Scenario.objects.all(),
      'fixtures': fixtures,
      'odoo': 'freppledb.odoo' in settings.INSTALLED_APPS,
      'planning_options': planning_options,
      'current_options': request.session.get('env', [ i[0] for i in planning_options ]),
      'filestoupload': filestoupload,
      'filesexported': filesexported,
      'datafolderconfigured': 'FILEUPLOADFOLDER' in settings.DATABASES[request.database]
      }


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
          'message': t.message, 'user': t.user.username if t.user else None
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
  # A
  if action == 'frepple_run':
    if not request.user.has_perm('auth.generate_plan'):
      raise Exception('Missing execution privileges')
    constraint = 0
    for value in request.POST.getlist('constraint'):
      try:
        constraint += int(value)
      except:
        pass
    task = Task(name='generate plan', submitted=now, status='Waiting', user=request.user)
    task.arguments = "--constraint=%s --plantype=%s" % (constraint, request.POST.get('plantype', 1))
    env = []
    for value in request.POST.getlist('env'):
      env.append(value)
    if env:
      task.arguments = "%s --env=%s" % (task.arguments, ','.join(env))
    request.session['env'] = env
    task.save(using=request.database)
    # Update the session object
    request.session['plantype'] = request.POST.get('plantype')
    request.session['constraint'] = constraint
  # C
  elif action == 'frepple_flush':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='empty database', submitted=now, status='Waiting', user=request.user)
    models = ','.join(request.POST.getlist('models'))
    if models:
      task.arguments = "--models=%s" % models
    task.save(using=request.database)
  # D
  elif action == 'loaddata':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='load dataset', submitted=now, status='Waiting', user=request.user, arguments=request.POST['fixture'])
    task.save(using=request.database)
  # E
  elif action == 'frepple_copy':
    worker_database = DEFAULT_DB_ALIAS
    if 'copy' in request.POST:
      if not request.user.has_perm('auth.copy_scenario'):
        raise Exception('Missing execution privileges')
      source = request.POST.get('source', DEFAULT_DB_ALIAS)
      destination = request.POST.getlist('destination')
      force = request.POST.get('force', False)
      for sc in Scenario.objects.all():
        arguments = "%s %s" % (source, sc.name)
        if force:
          arguments += ' --force'
        if request.POST.get(sc.name, 'off') == 'on' or sc.name in destination:
          task = Task(name='copy scenario', submitted=now, status='Waiting', user=request.user, arguments=arguments)
          task.save()
    elif 'release' in request.POST:
      # Note: release is immediate and synchronous.
      if not request.user.has_perm('auth.release_scenario'):
        raise Exception('Missing execution privileges')
      for sc in Scenario.objects.all():
        if request.POST.get(sc.name, 'off') == 'on' and sc.status != 'Free':
          sc.status = 'Free'
          sc.lastrefresh = now
          sc.save()
          if request.database == sc.name:
            # Erasing the database that is currently selected.
            request.prefix = ''
    elif 'update' in request.POST:
      # Note: update is immediate and synchronous.
      if not request.user.has_perm('auth.release_scenario'):
        raise Exception('Missing execution privileges')
      for sc in Scenario.objects.all():
        if request.POST.get(sc.name, 'off') == 'on':
          sc.description = request.POST.get('description', None)
          sc.save()
    else:
      raise Exception('Invalid scenario task')
  # F
  elif action == 'frepple_backup':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='backup database', submitted=now, status='Waiting', user=request.user)
    task.save(using=request.database)
  # G
  elif action == 'frepple_createbuckets':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='generate buckets', submitted=now, status='Waiting', user=request.user)
    arguments = []
    start = request.POST.get('start', None)
    if start:
      arguments.append("--start=%s" % start)
    end = request.POST.get('end', None)
    if end:
      arguments.append("--end=%s" % end)
    weekstart = request.POST.get('weekstart', None)
    if weekstart:
      arguments.append("--weekstart=%s" % weekstart)
    if arguments:
      task.arguments = " ".join(arguments)
    task.save(using=request.database)
  # J
  elif action == 'odoo_import' and 'freppledb.odoo' in settings.INSTALLED_APPS:
    task = Task(name='Odoo import', submitted=now, status='Waiting', user=request.user)
    task.save(using=request.database)
  # M
  elif action == 'frepple_importfromfolder':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='import from folder', submitted=now, status='Waiting', user=request.user)
    task.save(using=request.database)
  # N
  elif action == 'frepple_exporttofolder':
    if not request.user.has_perm('auth.run_db'):
      raise Exception('Missing execution privileges')
    task = Task(name='export to folder', submitted=now, status='Waiting', user=request.user)
    task.save(using=request.database)
  else:
    # Task not recognized
    raise Exception("Invalid task name '%s'" % action)

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
          "frepple_runworker",
          "--database=%s" % worker_database
          ])
      else:
        # Deployment on Apache web server
        Popen([
          "python",
          os.path.join(settings.FREPPLE_APP, "frepplectl.py"),
          "frepple_runworker",
          "--database=%s" % worker_database
          ], creationflags=0x08000000)
    elif sys.executable.find('freppleserver.exe') >= 0:
      # Py2exe executable
      Popen([
        sys.executable.replace('freppleserver.exe', 'frepplectl.exe'),  # frepplectl executable
        "frepple_runworker",
        "--database=%s" % worker_database
        ], creationflags=0x08000000)  # Do not create a console window
    else:
      # Linux standard installation
      Popen([
        "frepplectl",
        "frepple_runworker",
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
    if task.name == 'generate plan' and task.status.endswith("%"):
      if request.database == DEFAULT_DB_ALIAS:
        fname = os.path.join(settings.FREPPLE_LOGDIR, 'frepple.log')
      else:
        fname = os.path.join(settings.FREPPLE_LOGDIR, 'frepple_%s.log' % request.database)
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
def DownloadLogFile(request):
  if request.database == DEFAULT_DB_ALIAS:
    filename = 'frepple.log'
  else:
    filename = 'frepple_%s.log' % request.database
  response = static.serve(
    request, filename,
    document_root=settings.FREPPLE_LOGDIR
    )
  response['Content-Disposition'] = 'inline; filename="%s"' % filename
  response['Content-Type'] = 'application/octet-stream'
  return response


@staff_member_required
@never_cache
def logfile(request):
  '''
  This view shows the frePPLe log file of the last planning run in this database.
  '''
  try:
    if request.database == DEFAULT_DB_ALIAS:
      f = open(os.path.join(settings.FREPPLE_LOGDIR, 'frepple.log'), 'rb')
    else:
      f = open(os.path.join(settings.FREPPLE_LOGDIR, 'frepple_%s.log' % request.database), 'rb')
  except:
    logdata = "File not found"
  else:
    try:
      f.seek(-1, os.SEEK_END)
      if f.tell() >= 50000:
        # Too big to display completely
        f.seek(-50000, os.SEEK_END)
        d = f.read(50000)
        d = d[d.index(b'\n'):] # Strip the first, incomplete line
        logdata = force_text(_("Displaying only the last 50K from the log file")) + '...\n\n...' + d.decode("utf8","ignore")
      else:
        # Displayed completely
        f.seek(0, os.SEEK_SET)
        logdata = f.read(50000)
    finally:
      f.close()

  return render(request, 'execute/logfrepple.html', {
    'title': _('Log file'),
    'logdata': logdata,
    } )


class FileManager:
  '''
  Class to upload and download files from a folder.
  The folder code argument indicates which folder to use:
    - 0: file upload folder
    - 1: export subdirectory of the file upload folder
  '''

  @staticmethod
  def getFolder(request, foldercode):
    if foldercode == '0':
      return settings.DATABASES[request.database]['FILEUPLOADFOLDER']
    elif foldercode == '1':
      return os.path.join(settings.DATABASES[request.database]['FILEUPLOADFOLDER'], 'export')
    else:
      return HttpResponseNotAllowed(['post'], content='Only POST request method is allowed')


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
    folder = FileManager.getFolder(request, foldercode)
    for filename, content in request.FILES.items():
      try:
        # Validate file name
        clean_filename = re.split(r'/|:|\\', filename)[-1]
        if not clean_filename.endswith(('.csv', '.csv.gz')):
          response.write('%s: %s ' % (clean_filename, _("Extension must be .csv or .csv.gz") ) + '\n')
          errorcount += 1
          continue

        # Write to a file
        with open(os.path.join(folder, clean_filename), 'wb') as thetarget:
          for chunk in content.chunks():
            thetarget.write(chunk)

        response.write(force_text('%s: %s\n' % (clean_filename, _('OK'))))
      except Exception:
        response.write('%s: %s\n' % (clean_filename, _("Upload failed") ))
        errorcount += 1
    response.write(force_text('%s' % _('Finished')))
    if errorcount:
      response.status_code = 400
      response.reason_phrase = '%s files failed to upload correctly' % errorcount
    return response


  @staticmethod
  @csrf_exempt
  @basicauthentication(allow_logged_in=True)
  @staff_member_required
  @never_cache
  def deleteFilefromFolder(request, foldercode, filename):
    if request.method != 'DELETE':
      return HttpResponseNotAllowed(['delete'], content='Only DELETE request method is allowed')
    folder = FileManager.getFolder(request, foldercode)

    try:
      clean_filename = re.split(r'/|:|\\', filename)[-1]
      os.remove(os.path.join(folder, clean_filename))
      return HttpResponse(content="OK")
    except Exception:
      return HttpResponseServerError(force_text(_('Error deleting file')))


  @staticmethod
  @csrf_exempt
  @basicauthentication(allow_logged_in=True)
  @staff_member_required
  @never_cache
  def downloadFilefromFolder(request, foldercode, filename):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['get'], content='Only GET request method is allowed')
    folder = FileManager.getFolder(request, foldercode)

    try:
      clean_filename = filename.split('/')[0]
      response = static.serve(
        request, clean_filename, document_root=folder
        )
      response['Content-Disposition'] = 'inline; filename="%s"' % filename
      response['Content-Type'] = 'application/octet-stream'
      return response
    except Exception:
      return HttpResponseNotFound(force_text(_('Error downloading file')))
