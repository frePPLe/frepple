#
# Copyright (C) 2023 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template import Template, RequestContext

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import VERSION


class Command(BaseCommand):
    help = """
  This command copies the contents of a measure into another.
  The original data in the destination measure if any is lost.
  """

    requires_system_checks = []

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
            help="Database where to run the command",
        )
        parser.add_argument(
            "--description", help="Description of the destination measure"
        )
        parser.add_argument("--label", help="Label of the destination measure")
        parser.add_argument(
            "--startdate", help="Date when the copy should start. Format is YYYY-MM-DD"
        )
        parser.add_argument(
            "--enddate", help="Date when the copy should end. Format is YYYY-MM-DD"
        )
        parser.add_argument(
            "--type", help="Type of the destination measure. Default: aggregate"
        )
        parser.add_argument("source", help="source measure")
        parser.add_argument("destination", help="destination measure")

    def handle(self, **options):
        from freppledb.forecast.models import Measure

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

        startdate = None
        if options["startdate"]:
            try:
                startdate = datetime.strptime(options["startdate"], "%Y-%m-%d").date()
            except Exception:
                raise CommandError(
                    "Invalid startdate option: %s" % options["startdate"]
                )

        enddate = None
        if options["enddate"]:
            try:
                enddate = datetime.strptime(options["enddate"], "%Y-%m-%d").date()
            except Exception:
                raise CommandError("Invalid enddate option: %s" % options["enddate"])

        database = options["database"]
        source = options["source"]
        destination = options["destination"]

        if not destination:
            raise CommandError("No destination measure defined")

        # check source exists
        try:
            sourceMeasure = Measure.objects.using(database).get(pk=source)
        except Exception:
            raise CommandError("No source measure defined with name '%s'" % source)

        if not destination.isalnum():
            raise CommandError(
                'Destination measure must be alphanumeric, "%s" is not.' % destination
            )

        destinationExists = (
            Measure.objects.using(database).filter(name=destination).count() > 0
        )

        if not destinationExists:
            measure = Measure.objects.using(database).create(name=destination)
            measure.formatter = sourceMeasure.formatter
            measure.initially_hidden = True
            measure.mode_past = "view"
            measure.mode_future = "view"
        else:
            measure = Measure.objects.using(database).get(name=destination)

        # measure are created with "aggregate" type if not specified
        measure.type = (
            options["type"]
            or (measure.type if measure.type != "default" else None)
            or "aggregate"
        )

        # label is set to name if not defined
        measure.label = options["label"] or measure.label or destination

        description = options["description"]
        if description:
            measure.description = description

        measure.save(using=database)

        now = datetime.now()

        # Initialize the task
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
                or task.name != "measure_copy"
            ):
                raise CommandError("Invalid task identifier")
            task.status = "0%"
            task.started = now
        else:
            task = Task(
                name="measure_copy", submitted=now, started=now, status="0%", user=user
            )
        task.processid = os.getpid()
        task.save(using=database)

        try:
            task.arguments = "%s %s" % (source, destination)
            task.save(using=database)
            if source == destination:
                raise CommandError("Can't copy a measure on itself")

            with connections[database].cursor() as cursor:
                # Make the copy
                # We want to capture the days specified in start and end dates
                # So we compare the startdate with forecastplan enddates and vice versa
                cursor.execute(
                    """
                    update forecastplan set %s = %s
                    where %s is distinct from %s
                    %s
                    %s
                    """
                    % (
                        destination,
                        source,
                        destination,
                        source,
                        ("and enddate >= '%s'" % (startdate,)) if startdate else "",
                        ("and startdate <= '%s'" % (enddate,)) if enddate else "",
                    )
                )
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
    title = _("measure management")
    index = 3000
    help_url = "command-reference.html#measure-copy"

    @staticmethod
    def getHTML(request):
        from freppledb.forecast.models import Measure

        measures = Measure.objects.using(request.database)
        if measures.count() > 1:
            javascript = """
                $("#msr-entityul li a").click(function(){
                  $("#msr-entity").html($(this).text());
                  $("#sourcemeasure").val($(this).text());
                  $("#destinationmeasure").val($(this).text());
                });
                """
            context = RequestContext(
                request, {"javascript": javascript, "measures": measures}
            )

            template = Template(
                """
    {% load i18n %}
    {% if perms.auth.run_db %}
    <form class="form form-inline" role="form" method="post"
        onsubmit="return $('#sourcemeasure').val() != ''"
        action="{{request.prefix}}/execute/launch/measure_copy/">{% csrf_token %}
        <table id="measures">
        <tr>
            <td style="padding:15px; vertical-align:top">
                <button  class="btn btn-primary" id="msr-load" type="submit" value="{% trans "launch"|capfirst %}">
                  {% trans "launch"|capfirst %}
                </button>
            </td>
            <td style="padding:5px">
              {% trans "Copy source measure" %}
                <div class="btn-group">
                  <button class="dropdown-toggle d-inline form-control show" id="msr-entity" type="button" data-bs-toggle="dropdown">-</button>
                  <ul class="dropdown-menu" aria-labelledby="entity" id="msr-entityul">
                    {% for i in measures %}<li><a class="dropdown-item">{{ i.name }}</a></li>{% endfor %}
                  </ul>
                </div>
              {% trans "to destination measure" %}
              <input class="d-inline form-control" style="width:20em" type="text" size="20" name="destination" id="destinationmeasure" value="">
            </td>
        </tr>
        </table>
        <input type="hidden" name="source" id="sourcemeasure" value="">
    </form>
    <script>{{ javascript|safe }}</script>
    {% else %}
    {% trans "Sorry, You don't have any execute permissions..." %}
    {% endif %}
      """
            )
            return template.render(context)
            # A list of translation strings from the above
            translated = (_("Copy source measure"), _("to destination measure"))
        else:
            return None
