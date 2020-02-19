#
# Copyright (C) 2018 by frePPLe bvba
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
from dateutil.parser import parse
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands import loaddata
from django.db import connections, transaction
from django.template import Template, RequestContext
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import User, Parameter
from freppledb.common.middleware import _thread_locals
from freppledb.execute.models import Task


class Command(loaddata.Command):
    @staticmethod
    def getHTML(request):
        #  here is the code for the accordion menu

        # Loop over all fixtures of all apps and directories
        fixtures = set()
        folders = list(settings.FIXTURE_DIRS)
        for app in apps.get_app_configs():
            if not app.name.startswith("django"):
                folders.append(
                    os.path.join(os.path.dirname(app.path), app.label, "fixtures")
                )
        for f in folders:
            try:
                for root, dirs, files in os.walk(f):
                    for i in files:
                        if i.endswith(".json"):
                            fixtures.add(i.split(".")[0])
            except Exception:
                pass  # Silently ignore failures
        fixtures = sorted(fixtures)

        javascript = """
          $("#entityul li a").click(function(){
            $("#entity").html($(this).text() + ' <span class="caret"></span>');
            $("#loaddatafile").val($(this).text());
          });
          function checkbox_changed(checkbox) {
            $("#regeneratevar").val(checkbox.checked);
          };
          """

        context = RequestContext(
            request, {"fixtures": fixtures, "javascript": javascript}
        )

        template = Template(
            """
      {% load i18n %}
      {% if perms.auth.run_db %}
      <form class="form" role="form" method="post"
        onsubmit="return $('#loaddatafile').val() != ''"
        action="{{request.prefix}}/execute/launch/loaddata/">{% csrf_token %}
      <table>
        <tr>
          <td style="padding:15px; vertical-align:top">
            <button  class="btn btn-primary" id="load" type="submit" value="{% trans "launch"|capfirst %}">
              {% trans "launch"|capfirst %}
            </button>
          </td>
          <td style="padding:15px">
            <div class="dropdown dropdown-submit-input">
              <p>{% trans "Load one of the available datasets." %}</p>
              <button class="btn btn-default dropdown-toggle form-control" id="entity" type="button" data-toggle="dropdown">-&nbsp;&nbsp;<span class="caret"></span>
              </button>
              <ul class="dropdown-menu col-xs-12" aria-labelledby="entity" id="entityul">
                {% for i in fixtures %}<li><a>{{i}}</a></li>{% endfor %}
              </ul>
            </div>
          </td>
          <td style="padding:15px">
            <div>
              <ul class="checkbox">
                <li><input type="checkbox" id="loaddatacb1" onclick="checkbox_changed(this)" checked />
                <label for="loaddatacb1">{% trans "Execute plan after loading is done" %}</label></li>
              </ul>
            </div>
          </td>
        </tr>
      </table>
      <input type="hidden" name="fixture" id="loaddatafile" value="">
      <input type="hidden" name="regenerateplan" id="regeneratevar" value="true">
      </form>
      <script>{{ javascript|safe }}</script>
      {% else %}
        {% trans "Sorry, You don't have any execute permissions..." %}
      {% endif %}
    """
        )
        return template.render(context)
        # A list of translation strings from the above
        translated = (
            _("launch"),
            _("Load one of the available datasets."),
            _("Sorry, You don't have any execute permissions..."),
            _("Execute plan after loading is done"),
        )

    title = _("Load a dataset")
    index = 1800
    help_url = "user-guide/command-reference.html#loaddata"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--task",
            dest="task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument("--user", dest="user", help="User running the command")

    def handle(self, *fixture_labels, **options):

        # get the database object
        database = options["database"]
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)

        now = datetime.now()
        task = None
        try:
            setattr(_thread_locals, "database", database)
            # Initialize the task
            if options["task"]:
                try:
                    task = Task.objects.all().using(database).get(pk=options["task"])
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name != "loaddata"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
                task.processid = os.getpid()
                task.save(
                    using=database, update_fields=["started", "status", "processid"]
                )
            else:
                if options["user"]:
                    try:
                        user = (
                            User.objects.all()
                            .using(database)
                            .get(username=options["user"])
                        )
                    except Exception:
                        raise CommandError("User '%s' not found" % options["user"])
                else:
                    user = None
                task = Task(
                    name="loaddata",
                    submitted=now,
                    started=now,
                    status="0%",
                    user=user,
                    arguments=" ".join(fixture_labels),
                )
                task.processid = os.getpid()
                task.save(using=database)

            # Excecute the standard django command
            super().handle(*fixture_labels, **options)

            # if the fixture doesn't contain the 'demo' word, let's not apply loaddata post-treatments
            for f in fixture_labels:
                if "demo" not in f.lower():
                    return

            with transaction.atomic(using=database, savepoint=False):
                if self.verbosity > 2:
                    print("updating fixture to current date")

                cursor = connections[database].cursor()
                currentDate = parse(
                    Parameter.objects.using(database).get(name="currentdate").value
                )

                now = datetime.now()
                offset = (now - currentDate).days

                # update currentdate to now
                cursor.execute(
                    """
                    update common_parameter set value = 'now' where name = 'currentdate'
                    """
                )

                # update demand due dates
                cursor.execute(
                    """
                    update demand set due = due + %s * interval '1 day'
                    """,
                    (offset,),
                )

                # update PO/DO/MO due dates
                cursor.execute(
                    """
                      update operationplan
                      set startdate = startdate + %s * interval '1 day',
                          enddate = enddate + %s * interval '1 day'
                    """,
                    2 * (offset,),
                )

                # Task update
                task.status = "Done"
                task.finished = datetime.now()
                task.processid = None
                task.save(using=database, update_fields=["status", "finished"])

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
                task.processid = None
                task.save(
                    using=database, update_fields=["status", "finished", "message"]
                )
            raise CommandError("%s" % e)

        finally:
            setattr(_thread_locals, "database", None)
