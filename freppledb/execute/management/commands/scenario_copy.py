#
# Copyright (C) 2010-2013 by frePPLe bvba
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
import subprocess
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _
from django.template import Template, RequestContext

from freppledb.execute.models import Task
from freppledb.common.models import User, Scenario
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command copies the contents of a database into another.
  The original data in the destination database are lost.

  The pg_dump and psql commands need to be in the path, otherwise
  this command will fail.
  '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user',
      help='User running the command'
      ),
    parser.add_argument(
      '--force', action="store_true", default=False,
      help='Overwrite scenarios already in use'
      )
    parser.add_argument(
      '--description',
      help='Description of the destination scenario'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      'source', help='source database to copy'
      )
    parser.add_argument(
      'destination', help='destination database to copy'
      )


  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up options
    force = options['force']
    test = 'FREPPLE_TEST' in os.environ
    if options['user']:
      try:
        user = User.objects.all().get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      user = None

    # Synchronize the scenario table with the settings
    Scenario.syncWithSettings()

    # Initialize the task
    source = options['source']
    try:
      sourcescenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(pk=source)
    except:
      raise CommandError("No source database defined with name '%s'" % source)
    now = datetime.now()
    task = None
    if 'task' in options and options['task']:
      try:
        task = Task.objects.all().using(source).get(pk=options['task'])
      except:
        raise CommandError("Task identifier not found")
      if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_copy', 'scenario_copy'):
        raise CommandError("Invalid task identifier")
      task.status = '0%'
      task.started = now
    else:
      task = Task(name='scenario_copy', submitted=now, started=now, status='0%', user=user)
    task.save(using=source)

    # Validate the arguments
    destination = options['destination']
    destinationscenario = None
    try:
      task.arguments = "%s %s" % (source, destination)
      if options['description']:
        task.arguments += '--description="%s"' % options['description'].replace('"', '\\"')
      if force:
        task.arguments += " --force"
      task.save(using=source)
      try:
        destinationscenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(pk=destination)
      except:
        raise CommandError("No destination database defined with name '%s'" % destination)
      if source == destination:
        raise CommandError("Can't copy a schema on itself")
      if settings.DATABASES[source]['ENGINE'] != settings.DATABASES[destination]['ENGINE']:
        raise CommandError("Source and destination scenarios have a different engine")
      if sourcescenario.status != 'In use':
        raise CommandError("Source scenario is not in use")
      if destinationscenario.status != 'Free' and not force:
        raise CommandError("Destination scenario is not free")

      # Logging message - always logging in the default database
      destinationscenario.status = 'Busy'
      destinationscenario.save(using=DEFAULT_DB_ALIAS)

      # Copying the data
      # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
      if settings.DATABASES[source]['PASSWORD']:
        os.environ['PGPASSWORD'] = settings.DATABASES[source]['PASSWORD']
      commandline = "pg_dump -c -Fp %s%s%s%s | psql %s%s%s%s" % (
        settings.DATABASES[source]['USER'] and ("-U %s " % settings.DATABASES[source]['USER']) or '',
        settings.DATABASES[source]['HOST'] and ("-h %s " % settings.DATABASES[source]['HOST']) or '',
        settings.DATABASES[source]['PORT'] and ("-p %s " % settings.DATABASES[source]['PORT']) or '',
        test and settings.DATABASES[source]['TEST']['NAME'] or settings.DATABASES[source]['NAME'],
        settings.DATABASES[destination]['USER'] and ("-U %s " % settings.DATABASES[destination]['USER']) or '',
        settings.DATABASES[destination]['HOST'] and ("-h %s " % settings.DATABASES[destination]['HOST']) or '',
        settings.DATABASES[destination]['PORT'] and ("-p %s " % settings.DATABASES[destination]['PORT']) or '',
        test and settings.DATABASES[destination]['TEST']['NAME'] or settings.DATABASES[destination]['NAME'],
        )

      ret = subprocess.call(commandline, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

      if ret:
        raise Exception('Exit code of the database copy command is %d' % ret)

      # Update the scenario table
      destinationscenario.status = 'In use'
      destinationscenario.lastrefresh = datetime.today()
      if 'description' in options:
        destinationscenario.description = options['description']
      destinationscenario.save(using=DEFAULT_DB_ALIAS)

      # Give access to the destination scenario to:
      #  a) the user doing the copy
      #  b) all superusers from the source schema
      User.objects.using(destination).filter(is_superuser=True).update(is_active=True)
      User.objects.using(destination).filter(is_superuser=False).update(is_active=False)
      if user:
        User.objects.using(destination).filter(username=user.username).update(is_active=True)

      # Logging message
      task.status = 'Done'
      task.finished = datetime.now()

      # Update the task in the destination database
      task.message = "Scenario copied from %s" % source
      task.save(using=destination)
      task.message = "Scenario copied to %s" % destination

      # Delete any waiting tasks in the new copy.
      # This is needed for situations where the same source is copied to
      # multiple destinations at the same moment.
      Task.objects.all().using(destination).filter(id__gt=task.id).delete()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      if destinationscenario and destinationscenario.status == 'Busy':
        destinationscenario.status = 'Free'
        destinationscenario.save(using=DEFAULT_DB_ALIAS)
      raise e

    finally:
      if task:
        task.save(using=source)
      settings.DEBUG = tmp_debug

  # accordion template
  title = _('scenario management')
  index = 1500
  help_url = 'user-guide/command-reference.html#scenario-copy'

  @ staticmethod
  def getHTML(request):

    # Synchronize the scenario table with the settings
    Scenario.syncWithSettings()

    scenarios = Scenario.objects.all().using(DEFAULT_DB_ALIAS)
    if scenarios.count() > 1:
      javascript = '''
        $("#sourceul li a").click(function(){
          $("#source").html($(this).text() + ' <span class="caret"></span>');
          $("#sourcescenario").val($(this).text());
        });
        '''
      context = RequestContext(request, {'javascript': javascript, 'scenarios': scenarios})

      template = Template('''
        {% load i18n %}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/scenario_copy/">{% csrf_token %}
          <table id="scenarios">
            <tr>
              {% comment %}Translators: Translation included with Django {% endcomment %}
              <th style="padding: 0px 15px;">{% trans 'scenario'|capfirst %}</th>
              <th style="padding: 0px 15px;">{% trans 'status'|capfirst %}</th>
              <th>{% trans 'label'|capfirst %}</th>
              <th>{% trans 'last refresh'|capfirst %}</th>
            </tr>
            {% for j in scenarios %}{% ifnotequal j.name 'default' %}
            <tr>
              <td style="padding: 0px 15px;"><input type=checkbox name="{{j.name}}" id="sc{{j.name}}"/>
                <label for="sc{{j.name}}">&nbsp;<strong>{{j.name|capfirst}}</strong>
                </label>
              </td>
              <td  style="padding: 0px 15px;">{{j.status}}</td>
              <td>{% if j.description %}{{j.description}}{% endif %}</td>
              <td>{{j.lastrefresh|date:"DATETIME_FORMAT"}}</td>
            </tr>
            {% endifnotequal %}{% endfor %}
            {% if perms.auth.copy_scenario %}
            <tr>
              <td><button  class="btn btn-primary" name="copy" type="submit" value="{% trans "copy"|capfirst %}" style="width:100%">{% trans "copy"|capfirst %}</button>
              </td>
              <td  style="padding: 0px 15px;" colspan="3">
                {% trans "copy"|capfirst %}
                  <div class="dropdown dropdown-submit-input" style="display: inline-block;">
                    <button class="btn btn-default dropdown-toggle" id="source" value="" type="button" data-toggle="dropdown" style="min-width: 160px">-&nbsp;&nbsp;<span class="caret"></span></button>
                    <ul class="dropdown-menu" aria-labelledby="source" id="sourceul" style="top: auto">
                    {% for j in scenarios %}
                      {% ifequal j.status 'In use' %}
                        <li><a name="{{j.name}}">{{j.name}}</a></li>
                      {% endifequal %}
                    {% endfor %}
                    </ul>
                  </div>
                {% trans "into selected scenarios" %}

              </td>
            </tr>
            {% endif %}
            {% if perms.auth.release_scenario %}
            <tr>
              <td><button class="btn btn-primary" name="release" type="submit" value="{% trans "release"|capfirst %}" style="width:100%">{% trans "release"|capfirst %}</button></td>
              <td  style="padding: 0px 15px;" colspan="3">{% trans "release selected scenarios"|capfirst %}</td>
            </tr>
            <tr>
              <td><button class="btn btn-primary" name="update" type="submit" value="{% trans "update"|capfirst %}" style="width:100%">{% trans "update"|capfirst %}</button></td>
              <td  style="padding: 0px 15px;" colspan="3"><input class="form-control" name="description" type="text" size="40" placeholder="{% trans "Update description of selected scenarios" %}"/></td>
            </tr>
            {% endif %}
          </table>
          <input type="hidden" name="source" id="sourcescenario" value="">
        </form>
        <script>{{ javascript|safe }}</script>
      ''')
      return template.render(context)
      # A list of translation strings from the above
      translated = (
        _("copy"), _("release"), _("release selected scenarios"), _("into selected scenarios"),
        _("update"), _("Update description of selected scenarios")
        )
    else:
      return None
