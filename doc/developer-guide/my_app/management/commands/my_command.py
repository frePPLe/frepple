"""
This file demonstrates a custom command.
"""
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.template import Template, RequestContext
from django.utils.translation import gettext_lazy as _

from freppledb import VERSION
from freppledb.execute.models import Task


class Command(BaseCommand):
    # Help text shown when you run "frepplectl help my_command"
    help = "This command does ..."

    def add_arguments(self, parser):
        parser.add_argument(
            "--my_arg",
            dest="my_arg",
            type=int,
            default=0,
            help="an optional argument for the command",
        )
        parser.add_argument(
            "--database",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to load data from and export results into",
        )
        parser.add_argument(
            "--task",
            dest="task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )

    requires_model_validation = False

    def get_version(self):
        return VERSION

    # The busisness logic of the command goes in this method
    def handle(self, *args, **options):
        if "database" in options:
            database = options["database"] or DEFAULT_DB_ALIAS
        else:
            database = DEFAULT_DB_ALIAS
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)
        task = None
        now = datetime.now()
        try:
            # Initialize the task
            if "task" in options and options["task"]:
                try:
                    task = Task.objects.all().using(database).get(pk=options["task"])
                except Exception:
                    raise CommandError("Task identifier not found")
                if (
                    task.started
                    or task.finished
                    or task.status != "Waiting"
                    or task.name != "my_command"
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(name="my_command", submitted=now, started=now, status="0%")
            task.save(using=database)

            # Here goes the real business logic
            print("This command was called with argument %s" % options["my_arg"])

            # The task has finished successfully
            task.message = "My task message"
            task.processid = None
            task.status = "Done"
            task.finished = datetime.now()
            task.save(using=database)

        except Exception as e:
            # The task failed
            if task:
                task = Task.objects.all().using(database).get(pk=task.id)
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
                task.processid = None
                task.save(using=database)
            raise e

    # Label to display on the execution screen
    title = _("My own command")

    # Sequence of the command on the execution screen
    index = 1

    # This method generates the text to display on the execution screen
    @staticmethod
    def getHTML(request):
        context = RequestContext(request)
        template = Template(
            """
            {% load i18n %}
            <form class="form" role="form" method="post"
               action="{{request.prefix}}/execute/launch/my_command/">{% csrf_token %}
            <table>
            <tr>
              <td style="padding:15px; vertical-align:top">
              <button  class="btn btn-primary" id="load" type="submit">{% trans "launch"|capfirst %}</button>
              </td>
              <td style="padding:15px">
              A description of my command
              </td>
            </tr>
            </table>
            </form>
            """
        )
        return template.render(context)
