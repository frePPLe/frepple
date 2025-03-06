#
# Copyright (C) 2016 by frePPLe bv
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

from datetime import datetime

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _
from django.template import Template, RequestContext
from django.template.loader import render_to_string

from freppledb import __version__
from freppledb.execute.models import Task


class Command(BaseCommand):
    help = "Loads data from an Odoo instance into the frePPLe database"

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates the frePPLe database to load",
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument(
            "--environment", default="odoo_read_1", help="data source environment"
        )

    def handle(self, **options):
        self.verbosity = int(options["verbosity"])
        task = options.get("task", None)
        database = options["database"]
        environment = options["environment"]
        if (
            not environment.startswith("odoo_read_")
            or not len(environment) == 11
            or not environment[10].isdigit()
        ):
            raise CommandError(
                "Invalid environment: %s. It must be odoo_read_X with X being a number between 1 to 5"
                % environment
            )
        if database not in settings.DATABASES.keys():
            raise CommandError("No database settings known for '%s'" % self.database)
        kwargs = {
            "env": "%s,nowebservice" % environment,
            "database": database,
            "task": task,
            "constraint": 0,
            "plantype": 2,
        }
        if not options["task"]:
            task = Task(
                name="odoo_import",
                submitted=datetime.now(),
                status="Waiting",
                user=options["user"],
            )
            task.save(using=database)
            kwargs["task"] = task.id
        elif options["user"]:
            kwargs["user"] = options["user"]
        management.call_command("runplan", **kwargs)

    # accordion template
    title = _("Import data from %(erp)s") % {"erp": "odoo"}
    index = 1050
    help_url = "command-reference.html#odoo_import"

    @staticmethod
    def getHTML(request):
        return render_to_string(
            "commands/odoo_import.html",
            request=request,
        )
