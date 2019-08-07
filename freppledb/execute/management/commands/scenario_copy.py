#
# Copyright (C) 2010-2019 by frePPLe bvba
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
from django.utils.translation import gettext_lazy as _
from django.template import Template, RequestContext

from freppledb.execute.models import Task
from freppledb.common.models import User, Scenario
from freppledb import VERSION


class Command(BaseCommand):
    help = """
  This command copies the contents of a database into another.
  The original data in the destination database are lost.

  The pg_dump and psql commands need to be in the path, otherwise
  this command will fail.
  """

    requires_system_checks = False

    def get_version(self):
        return VERSION

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command"),
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Overwrite scenarios already in use",
        )
        parser.add_argument(
            "--description", help="Description of the destination scenario"
        )
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
        parser.add_argument("source", help="source database to copy")
        parser.add_argument("destination", help="destination database to copy")

    def handle(self, **options):
        # Make sure the debug flag is not set!
        # When it is set, the django database wrapper collects a list of all sql
        # statements executed and their timings. This consumes plenty of memory
        # and cpu time.
        tmp_debug = settings.DEBUG
        settings.DEBUG = False

        # Pick up options
        force = options["force"]
        test = "FREPPLE_TEST" in os.environ
        if options["user"]:
            try:
                user = User.objects.all().get(username=options["user"])
            except:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        # Synchronize the scenario table with the settings
        Scenario.syncWithSettings()

        # Initialize the task
        source = options["source"]
        try:
            sourcescenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(pk=source)
        except:
            raise CommandError("No source database defined with name '%s'" % source)
        now = datetime.now()
        task = None
        if "task" in options and options["task"]:
            try:
                task = Task.objects.all().using(source).get(pk=options["task"])
            except:
                raise CommandError("Task identifier not found")
            if (
                task.started
                or task.finished
                or task.status != "Waiting"
                or task.name not in ("frepple_copy", "scenario_copy")
            ):
                raise CommandError("Invalid task identifier")
            task.status = "0%"
            task.started = now
        else:
            task = Task(
                name="scenario_copy", submitted=now, started=now, status="0%", user=user
            )
        task.processid = os.getpid()
        task.save(using=source)

        # Validate the arguments
        destination = options["destination"]
        destinationscenario = None
        try:
            task.arguments = "%s %s" % (source, destination)
            if options["description"]:
                task.arguments += '--description="%s"' % options["description"].replace(
                    '"', '\\"'
                )
            if force:
                task.arguments += " --force"
            task.save(using=source)
            try:
                destinationscenario = Scenario.objects.using(DEFAULT_DB_ALIAS).get(
                    pk=destination
                )
            except:
                raise CommandError(
                    "No destination database defined with name '%s'" % destination
                )
            if source == destination:
                raise CommandError("Can't copy a schema on itself")
            if sourcescenario.status != "In use":
                raise CommandError("Source scenario is not in use")
            if destinationscenario.status != "Free" and not force:
                raise CommandError("Destination scenario is not free")

            # Logging message - always logging in the default database
            destinationscenario.status = "Busy"
            destinationscenario.save(using=DEFAULT_DB_ALIAS)

            # Copying the data
            # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
            if settings.DATABASES[source]["PASSWORD"]:
                os.environ["PGPASSWORD"] = settings.DATABASES[source]["PASSWORD"]
            if os.name == "nt":
                # On windows restoring with pg_restore over a pipe is broken :-(
                cmd = "pg_dump -c -Fp %s%s%s%s | psql %s%s%s%s"
            else:
                cmd = "pg_dump -Fc %s%s%s%s | pg_restore -n public -Fc -c --if-exists %s%s%s -d %s"
            commandline = cmd % (
                settings.DATABASES[source]["USER"]
                and ("-U %s " % settings.DATABASES[source]["USER"])
                or "",
                settings.DATABASES[source]["HOST"]
                and ("-h %s " % settings.DATABASES[source]["HOST"])
                or "",
                settings.DATABASES[source]["PORT"]
                and ("-p %s " % settings.DATABASES[source]["PORT"])
                or "",
                test
                and settings.DATABASES[source]["TEST"]["NAME"]
                or settings.DATABASES[source]["NAME"],
                settings.DATABASES[destination]["USER"]
                and ("-U %s " % settings.DATABASES[destination]["USER"])
                or "",
                settings.DATABASES[destination]["HOST"]
                and ("-h %s " % settings.DATABASES[destination]["HOST"])
                or "",
                settings.DATABASES[destination]["PORT"]
                and ("-p %s " % settings.DATABASES[destination]["PORT"])
                or "",
                test
                and settings.DATABASES[destination]["TEST"]["NAME"]
                or settings.DATABASES[destination]["NAME"],
            )
            with subprocess.Popen(
                commandline,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            ) as p:
                try:
                    task.processid = p.pid
                    task.save(using=source)
                    p.wait()
                except:
                    p.kill()
                    p.wait()
                    # Consider the destination database free again
                    destinationscenario.status = "Free"
                    destinationscenario.lastrefresh = datetime.today()
                    destinationscenario.save(using=DEFAULT_DB_ALIAS)
                    raise Exception("Database copy failed")

            # Update the scenario table
            destinationscenario.status = "In use"
            destinationscenario.lastrefresh = datetime.today()
            if options["description"]:
                destinationscenario.description = options["description"]
            destinationscenario.save(using=DEFAULT_DB_ALIAS)

            # Give access to the destination scenario to:
            #  a) the user doing the copy
            #  b) all superusers from the source schema
            User.objects.using(destination).filter(is_superuser=True).update(
                is_active=True
            )
            User.objects.using(destination).filter(is_superuser=False).update(
                is_active=False
            )
            if user:
                User.objects.using(destination).filter(username=user.username).update(
                    is_active=True
                )

            # Logging message
            task.processid = None
            task.status = "Done"
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
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            if destinationscenario and destinationscenario.status == "Busy":
                destinationscenario.status = "Free"
                destinationscenario.save(using=DEFAULT_DB_ALIAS)
            raise e

        finally:
            if task:
                task.processid = None
                task.save(using=source)
            settings.DEBUG = tmp_debug

    # accordion template
    title = _("scenario management")
    index = 1500
    help_url = "user-guide/command-reference.html#scenario-copy"

    @staticmethod
    def getHTML(request):

        # Synchronize the scenario table with the settings
        Scenario.syncWithSettings()

        scenarios = Scenario.objects.using(DEFAULT_DB_ALIAS)
        if scenarios.count() > 1:
            javascript = """
        $(".scenariorelease").on("click", function(event) {
          event.preventDefault();
          var target = "/" + $(this).attr("data-target");
          if (target == "/default")
            target = "";
          $.ajax({
           url: target + "/execute/launch/scenario_copy/",
           type: 'POST',
           data: {release: 1},
           success: function() { if (target == prefix) window.location.href = "/"; }
           });
        });
        $(".scenariocopy").on("click", function(event) {
          event.preventDefault();
          var source = "/" + $(this).attr("data-source");
          if (source == "/default")
            source = "";
          $.ajax({
           url: source + "/execute/launch/scenario_copy/",
           type: 'POST',
           data: {
             copy: 1,
             source: $(this).attr("data-source"),
             destination: $(this).attr("data-target")
             }
           });
        });
        $(".scenariolabel").on("change", function(event) {
          event.preventDefault();
          var target = "/" + $(this).attr("data-target");
          if (target == "/default")
            target = "";
          $.ajax({
           url: target + "/execute/launch/scenario_copy/",
           type: 'POST',
           data: {
             update: 1,
             description: $(this).val()
             },
           success: function() { window.location.href = window.location.href; }
           });
        });
        """
            context = RequestContext(
                request, {"javascript": javascript, "scenarios": scenarios}
            )

            template = Template(
                """
        {% load i18n %}
        <table id="scenarios">
          <tr>
            {% comment %}Translators: Translation included with Django {% endcomment %}
            <th style="padding:5px 10px 5px 10px; text-align: center">{% trans 'scenario'|capfirst %}</th>
            <th style="padding:5px 10px 5px 10px; text-align: center">{% trans 'action'|capfirst %}</th>
            <th style="padding:5px 10px 5px 10px; text-align: center">
              <span data-toggle="tooltip" data-placement="top" data-html="true"
                data-original-title="<b>In use</b>: Contains data<br><b>Free</b>: Available to copy data into<br><b>Busy</b>: Data copy in progress">
              {% trans 'status'|capfirst %}
              <span class="fa fa-question-circle"></span>
              </span>
            </th>
            <th style="padding:5px 10px 5px 10px; text-align: center">
              <span data-toggle="tooltip" data-placement="top" data-original-title="Label shown in the scenario dropdown list">
              {% trans 'label'|capfirst %}
              <span class="fa fa-question-circle"></span>
              </span></th>
            <th style="padding:5px 10px 5px 10px; text-align: center">
              <span data-toggle="tooltip" data-placement="top" data-original-title="Date of the last action">
              {% trans 'last modified'|capfirst %}
              <span class="fa fa-question-circle"></span>
              </span>
            </th>
          </tr>
          {% for j in scenarios %}
          <tr>
            <td style="padding:5px">
              <strong>{{j.name|capfirst}}</strong>
            </td>
            <td style="padding:5px 10px 5px 10px">
               {% if j.name != 'default' and j.status == 'Free' and perms.auth.copy_scenario %}
               <div class="btn-group btn-block">
               <button class="btn btn-block btn-primary dropdown-toggle" type="button" data-toggle="dropdown">
                 {% trans 'copy'|capfirst %}&nbsp;<span class="caret"></span>
               </button>
               <ul class="dropdown-menu" rol="menu">
                 {% for k in scenarios %}{% if k.status == 'In use' %}
                 <li><a class="scenariocopy" href="#" data-source="{{ k.name }}" data-target="{{ j.name }}">
                   Copy from {{ k.name|capfirst }}
                 </a></li>
                 {% endif %}{% endfor %}
               </ul>
               </div>
               {% elif j.name != 'default' and j.status == 'In use' and perms.auth.release_scenario %}
               <div class="btn-group btn-block">
               <button class="btn btn-block btn-primary dropdown-toggle" type="button" data-toggle="dropdown">
                 {% trans 'release'|capfirst %}&nbsp;<span class="caret"></span>
               </button>
               <ul class="dropdown-menu" rol="menu">
                 <li><a class="scenariorelease" href="#" data-target="{{ j.name }}">
                 {% trans "You will lose ALL data in this scenario!" %}
                 </a></li>
               </ul>
               </div>
               {% endif %}
            </td>
            {% with mystatus=j.status|lower %}
            <td style="padding:5px 10px 5px 10px; text-align: center">{% trans mystatus|capfirst %}</td>
            {% endwith %}
            <td style="padding:5px 10px 5px 10px">
              <input class="scenariolabel" type="text" size="20" data-target="{{ j.name }}"
              value="{% if j.description %}{{j.description|escape}}{% else %}{{ j.name }}{% endif %}">
            </td>
            <td style="padding:5px 10px 5px 10px; text-align: center">{{j.lastrefresh|date:"DATETIME_FORMAT"}}</td>
          </tr>
          {% endfor %}
        </table>
        <script>{{ javascript|safe }}</script>
      """
            )
            return template.render(context)
            # A list of translation strings from the above
            translated = (
                _("copy"),
                _("release"),
                _("release selected scenarios"),
                _("into selected scenarios"),
                _("update"),
                _("Update description of selected scenarios"),
                _("You will lose ALL data in this scenario!"),
            )
        else:
            return None
