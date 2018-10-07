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
from datetime import datetime
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.template import Template, RequestContext

from freppledb.common.commands import PlanTaskRegistry
from freppledb.common.models import User
from freppledb.execute.models import Task
from freppledb import VERSION


class Command(BaseCommand):

  help = "Runs frePPLe to generate a plan"

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user', dest='user',
      help='User running the command'
      )
    parser.add_argument(
      '--constraint', dest='constraint', type=int, default=15,
      choices=range(0, 16),
      help='Constraints to be considered: 1=lead time, 2=material, 4=capacity, 8=release fence'
      )
    parser.add_argument(
      '--plantype', dest='plantype', type=int, choices=[1, 2],
      default=1, help='Plan type: 1=constrained, 2=unconstrained'
      )
    parser.add_argument(
      '--database', dest='database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      )
    parser.add_argument(
      '--task', dest='task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      '--env', dest='env',
      help='A comma separated list of extra settings passed as environment variables to the engine'
      )
    parser.add_argument(
      '--background', dest='background', action='store_true', default=False,
      help='Run the planning engine in the background (default = False)'
      )


  def handle(self, **options):
    # Pick up the options
    now = datetime.now()

    if 'database' in options:
      database = options['database'] or DEFAULT_DB_ALIAS
    else:
      database = DEFAULT_DB_ALIAS
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    if 'user' in options and options['user']:
      try:
        user = User.objects.all().using(database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      user = None

    timestamp = now.strftime("%Y%m%d%H%M%S")
    if database == DEFAULT_DB_ALIAS:
      logfile = 'frepple-%s.log' % timestamp
    else:
      logfile = 'frepple_%s-%s.log' % (database, timestamp)

    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try:
          task = Task.objects.all().using(database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('runplan', 'frepple_run'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
        task.logfile = logfile
      else:
        task = Task(name='runplan', submitted=now, started=now, status='0%', user=user, logfile=logfile)

      # Validate options
      if 'constraint' in options:
        constraint = int(options['constraint'])
        if constraint < 0 or constraint > 15:
          raise ValueError("Invalid constraint: %s" % options['constraint'])
      else:
        constraint = 15
      if 'plantype' in options:
        plantype = int(options['plantype'])
      else:
        plantype = 1

      # Reset environment variables
      # TODO avoid having to delete the environment variables. Use options directly?
      PlanTaskRegistry.autodiscover()
      for i in PlanTaskRegistry.reg:
        if 'env' in options:
          # Options specified
          if i.label and i.label[0] in os.environ:
            del os.environ[i.label[0]]
        elif i.label:
          # No options specified - default to activate them all
          os.environ[i.label[0]] = '1'

      # Set environment variables
      if options['env']:
        task.arguments = "--constraint=%d --plantype=%d --env=%s" % (constraint, plantype, options['env'])
        for i in options['env'].split(','):
          j = i.split('=')
          if len(j) == 1:
            os.environ[j[0]] = '1'
          else:
            os.environ[j[0]] = j[1]
      else:
        task.arguments = "--constraint=%d --plantype=%d" % (constraint, plantype)
      if options['background']:
        task.arguments += " --background"

      # Log task
      task.save(using=database)

      # Locate commands.py
      import freppledb.common.commands
      cmd = freppledb.common.commands.__file__

      def setlimits():
        import resource
        if settings.MAXMEMORYSIZE:
          resource.setrlimit(
            resource.RLIMIT_AS,
            (settings.MAXMEMORYSIZE * 1024 * 1024, (settings.MAXMEMORYSIZE + 10) * 1024 * 1024)
            )
        if settings.MAXCPUTIME:
          resource.setrlimit(
            resource.RLIMIT_CPU,
            (settings.MAXCPUTIME, settings.MAXCPUTIME + 5)
            )
        # Limiting the file size is a bit tricky as this limit not only applies to the log
        # file, but also to temp files during the export
        # if settings.MAXTOTALLOGFILESIZE:
        #  resource.setrlimit(
        #    resource.RLIMIT_FSIZE,
        #   (settings.MAXTOTALLOGFILESIZE * 1024 * 1024, (settings.MAXTOTALLOGFILESIZE + 1) * 1024 * 1024)
        #   )

      # Prepare environment
      os.environ['FREPPLE_PLANTYPE'] = str(plantype)
      os.environ['FREPPLE_CONSTRAINT'] = str(constraint)
      os.environ['FREPPLE_TASKID'] = str(task.id)
      os.environ['FREPPLE_DATABASE'] = database
      os.environ['FREPPLE_LOGFILE'] = logfile
      os.environ['PATH'] = settings.FREPPLE_HOME + os.pathsep + os.environ['PATH'] + os.pathsep + settings.FREPPLE_APP
      if os.path.isfile(os.path.join(settings.FREPPLE_HOME, 'libfrepple.so')):
        os.environ['LD_LIBRARY_PATH'] = settings.FREPPLE_HOME
      if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
      os.environ['PYTHONPATH'] = os.path.normpath(settings.FREPPLE_APP)
      libdir = os.path.join(os.path.normpath(settings.FREPPLE_HOME), 'lib')
      if os.path.isdir(libdir):
        # Folders used by the Windows version
        os.environ['PYTHONPATH'] += os.pathsep + libdir
        if os.path.isfile(os.path.join(libdir, 'library.zip')):
          os.environ['PYTHONPATH'] += os.pathsep + os.path.join(libdir, 'library.zip')

      if options['background']:
        # Execute as background process on Windows
        if os.name == 'nt':
          subprocess.Popen(['frepple', cmd], creationflags=0x08000000)
        else:
          # Execute as background process on Linux
          subprocess.Popen(['frepple', cmd], preexec_fn=setlimits)
      else:
        if os.name == 'nt':
          # Execute in foreground on Windows
          ret = subprocess.call(['frepple', cmd])
        else:
          # Execute in foreground on Linux
          ret = subprocess.call(['frepple', cmd], preexec_fn=setlimits)
        if ret != 0 and ret != 2:
          # Return code 0 is a successful run
          # Return code is 2 is a run cancelled by a user. That's shown in the status field.
          raise Exception('Failed with exit code %d' % ret)

        # Task update
        task.status = 'Done'
        task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      if task:
        task.save(using=database)


  # accordion template
  title = _('Create a plan')
  index = 0

  help_url = 'user-guide/command-reference.html#runplan'

  @ staticmethod
  def getHTML(request):

    if request.user.has_perm('auth.generate_plan'):
      # Collect optional tasks
      PlanTaskRegistry.autodiscover()
      planning_options = PlanTaskRegistry.getLabels()
      current_options = request.session.get('env', [ i[0] for i in planning_options ])

      try:
        constraint = int(request.session['constraint'])
      except:
        constraint = 15

      context = RequestContext(request, {
        'planning_options': planning_options,
        'current_options': current_options,
        'capacityconstrained': constraint & 4,
        'materialconstrained': constraint & 2,
        'leadtimeconstrained': constraint & 1,
        'fenceconstrained': constraint & 8
        })

      template = Template('''
        {%% load i18n %%}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/runplan/">{%% csrf_token %%}
          <table>
          <tr>
            <td style="vertical-align:top; padding: 15px">
                <button type="submit" class="btn btn-primary">{%% trans "launch"|capfirst %%}</button>
            </td>
            <td  style="padding: 15px;">%s<br><br>
          {%% if planning_options %%}
          <p {%% if planning_options|length <= 1 %%}style="display: none"{%% endif %%}><b>{%% filter capfirst %%}%s{%% endfilter %%}</b><br>
          {%% for b in planning_options %%}
          <label for="option_{{b.0}}"><input type="checkbox" name="env" {%% if b.0 in current_options %%}checked {%% endif %%}value="{{b.0}}" id="option_{{b.0}}"/>&nbsp;&nbsp;{{b.1}}</label><br>
          {%% endfor %%}
          </p>
          {%% endif %%}
          <p><b>%s</b><br>
          <input type="radio" id="plantype1" name="plantype" {%% ifnotequal request.session.plantype '2' %%}checked {%% endifnotequal %%}value="1"/>
          <label for="plantype1">%s
          <span class="fa fa-question-circle" style="display:inline-block;"></span></label><br>
          <input type="radio" id="plantype2" name="plantype" {%% ifequal  request.session.plantype '2' %%}checked {%% endifequal %%}value="2"/>
          <label for="plantype2">%s
              <span class="fa fa-question-circle" style="display:inline-block;"></span></label><br>
              </p>
              <p>
              <b>{%% filter capfirst %%}%s{%% endfilter %%}</b><br>
              <label for="cb4"><input type="checkbox" name="constraint" {%% if capacityconstrained %%}checked {%% endif %%}value="4" id="cb4"/>&nbsp;&nbsp;%s</label><br>
              <label for="cb2"><input type="checkbox" name="constraint" {%% if materialconstrained %%}checked {%% endif %%}value="2" id="cb2"/>&nbsp;&nbsp;%s</label><br>
              <label for="cb1"><input type="checkbox" name="constraint" {%% if leadtimeconstrained %%}checked {%% endif %%}value="1" id="cb1"/>&nbsp;&nbsp;%s</label><br>
              <label for="cb8"><input type="checkbox" name="constraint" {%% if fenceconstrained %%}checked {%% endif %%}value="8" id="cb8"/>&nbsp;&nbsp;%s</label><br>
              </p>
            </td>
          </tr>
          </table>
        </form>
      ''' % (
        force_text(_('Load frePPLe from the database and live data sources...<br>'
          'and create a plan in frePPLe...<br>'
          'and export results.')),
        force_text(_("optional planning steps")),
        force_text(_("Plan type")),
        force_text(_('<span data-toggle="tooltip" data-placement="top" data-html="true" data-original-title="Generate a supply plan that respects all constraints.<br>In case of shortages the demand is planned late or short.">Constrained plan</span>')),
        force_text(_('<span data-toggle="tooltip" data-placement="top" data-html="true" data-original-title="Generate a supply plan that shows material, capacity and operation problems that prevent the demand from being planned in time.<br>The demand is always met completely and on time.">Unconstrained plan</span>')),
        force_text(_("constraints")),
        force_text(_("Capacity: respect capacity limits")),
        force_text(_("Material: respect procurement limits")),
        force_text(_("Lead time: do not plan in the past")),
        force_text(_("Release fence: do not plan within the release time window")),
        ))
      return template.render(context)
    else:
      return None
