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

import os
import os.path
import sys
from datetime import datetime
from subprocess import Popen

from django.conf import settings
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.db.models import get_apps
from django.utils.translation import ugettext_lazy as _
from django.db import DEFAULT_DB_ALIAS
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponse, StreamingHttpResponse
from django.contrib import messages
from django.utils.encoding import force_text

from freppledb.execute.models import Task
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

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), editable=False, align='center'),
    GridFieldDateTime('submitted', title=_('submitted'), editable=False, align='center'),
    GridFieldDateTime('started', title=_('started'), editable=False, align='center'),
    GridFieldDateTime('finished', title=_('finished'), editable=False, align='center'),
    GridFieldText('status', title=_('status'), editable=False, align='center', extra="formatter:status"),
    GridFieldText('message', title=_('message'), editable=False, width=500),
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

    # Loop over all fixtures of all apps and directories
    fixtures = set()
    folders = list(settings.FIXTURE_DIRS)
    for app in get_apps():
      if app.__name__.startswith('django'):
        continue
      folders.append(os.path.join(os.path.dirname(app.__file__), 'fixtures'))
    for f in folders:
      try:
        for root, dirs, files in os.walk(f):
          for i in files:
            if i.endswith('.json'):
              fixtures.add(i.split('.')[0])
      except:
        pass  # Silently ignore failures
    fixtures = sorted(fixtures)

    # Send to template
    odoo = 'freppledb.odoo' in settings.INSTALLED_APPS
    return {'capacityconstrained': constraint & 4,
            'materialconstrained': constraint & 2,
            'leadtimeconstrained': constraint & 1,
            'fenceconstrained': constraint & 8,
            'scenarios': Scenario.objects.all(),
            'fixtures': fixtures,
            'openbravo': 'freppledb.openbravo' in settings.INSTALLED_APPS,
            'odoo': odoo,
            'odoo_read': odoo and request.session.get('odoo_read', False),
            'odoo_write': odoo and request.session.get('odoo_write', False)
            }


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

  # Check user permissions
  if not request.user.has_perm('execute'):
    raise Exception('Missing execution privileges')

  # Parse the posted parameters as arguments for an asynchronous task to add to the queue.    TODO MAKE MODULAR WITH SEPERATE TASK CLASS
  worker_database = request.database

  now = datetime.now()
  task = None
  # A
  if action == 'frepple_run':
    if not request.user.has_perm('execute.generate_plan'):
      raise Exception('Missing execution privileges')
    constraint = 0
    for value in request.POST.getlist('constraint'):
      try:
        constraint += int(value)
      except:
        pass
    task = Task(name='generate plan', submitted=now, status='Waiting', user=request.user)
    task.arguments = "--constraint=%s --plantype=%s" % (constraint, request.POST.get('plantype'))
    env = []
    if request.POST.get('odoo_read', None) == '1':
      env.append("odoo_read")
      request.session['odoo_read'] = True
    else:
      request.session['odoo_read'] = False
    if request.POST.get('odoo_write', None) == '1':
      env.append("odoo_write")
      request.session['odoo_write'] = True
    else:
      request.session['odoo_write'] = False
    if env:
      task.arguments = "%s --env=%s" % (task.arguments, ','.join(env))
    task.save(using=request.database)
    # Update the session object
    request.session['plantype'] = request.POST.get('plantype')
    request.session['constraint'] = constraint
  # B
  elif action == 'frepple_createmodel':
    task = Task(name='generate model', submitted=now, status='Waiting', user=request.user)
    task.arguments = "--cluster=%s --demand=%s --forecast_per_item=%s --level=%s --resource=%s " \
      "--resource_size=%s --components=%s --components_per=%s --deliver_lt=%s --procure_lt=%s" % (
        request.POST['clusters'], request.POST['demands'], request.POST['fcst'], request.POST['levels'],
        request.POST['rsrc_number'], request.POST['rsrc_size'], request.POST['components'],
        request.POST['components_per'], request.POST['deliver_lt'], request.POST['procure_lt']
        )
    task.save(using=request.database)
  # C
  elif action == 'frepple_flush':
    task = Task(name='empty database', submitted=now, status='Waiting', user=request.user)
    if not request.POST.get('all'):
      task.arguments = "--models=%s" % ','.join(request.POST.getlist('entities'))
    task.save(using=request.database)
  # D
  elif action == 'loaddata':
    task = Task(name='load dataset', submitted=now, status='Waiting', user=request.user, arguments=request.POST['datafile'])
    task.save(using=request.database)
  # E
  elif action == 'frepple_copy':
    worker_database = DEFAULT_DB_ALIAS
    if 'copy' in request.POST:
      if not request.user.has_perm('execute.copy_scenario'):
        raise Exception('Missing execution privileges')
      source = request.POST.get('source', DEFAULT_DB_ALIAS)
      for sc in Scenario.objects.all():
        if request.POST.get(sc.name, 'off') == 'on' and sc.status == 'Free':
          task = Task(name='copy scenario', submitted=now, status='Waiting', user=request.user, arguments="%s %s" % (source, sc.name))
          task.save()
    elif 'release' in request.POST:
      # Note: release is immediate and synchronous.
      if not request.user.has_perm('execute.release_scenario'):
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
      for sc in Scenario.objects.all():
        if request.POST.get(sc.name, 'off') == 'on':
          sc.description = request.POST.get('description', None)
          sc.save()
    else:
      raise Exception('Invalid scenario task')
  # F
  elif action == 'frepple_backup':
    task = Task(name='backup database', submitted=now, status='Waiting', user=request.user)
    task.save(using=request.database)
  # G
  elif action == 'frepple_createbuckets':
    task = Task(name='generate buckets', submitted=now, status='Waiting', user=request.user)
    task.arguments = "--start=%s --end=%s --weekstart=%s" % (
      request.POST['start'], request.POST['end'], request.POST['weekstart']
      )
    task.save(using=request.database)
  # H
  elif action == 'openbravo_import' and 'freppledb.openbravo' in settings.INSTALLED_APPS:
    task = Task(name='Openbravo import', submitted=now, status='Waiting', user=request.user)
    task.arguments = "--delta=%s" % request.POST['delta']
    task.save(using=request.database)
  # I
  elif action == 'openbravo_export' and 'freppledb.openbravo' in settings.INSTALLED_APPS:
    task = Task(name='Openbravo export', submitted=now, status='Waiting', user=request.user)
    task.save(using=request.database)
  else:
    # Task not recognized
    raise Exception('Invalid launching task')

  # Launch a worker process
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
  if request.method != 'POST'or not request.is_ajax():
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
        with open(fname, 'rb') as f:
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
        logdata = force_text(_("Displaying only the last 50K from the log file")) + '...\n\n...' + force_text(d)
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
