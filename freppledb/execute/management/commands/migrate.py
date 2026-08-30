#
# Copyright (C) 2021 by frePPLe bv
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

import sys

from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as StdCommand
from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS

from freppledb.common.models import Scenario


class Command(StdCommand):
    def create_parser(self, prog_name, subcommand, **kwargs):
        kwargs["conflict_handler"] = "resolve"
        return super().create_parser(prog_name, subcommand, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(database=None)

    def get_check_kwargs(self, options):
        opts = dict(options)
        if not opts.get("database"):
            opts["database"] = DEFAULT_DB_ALIAS
        return super().get_check_kwargs(opts)

    def handle(self, *args, **options):
        def run_migrate():
            try:
                super(Command, self).handle(*args, **options)
            except CommandError as e:
                msg = str(e)
                if any(
                    t in msg
                    for t in (
                        "does not have migrations.",
                        "No installed app with label",
                    )
                ):
                    # Safe to ignore these zero-operation migrations
                    return
                raise

        if options["database"]:
            # Database was specified
            run_migrate()
            return

        Scenario.syncWithSettings()
        try:
            with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
                cursor.execute(
                    """
                    select name
                    from common_scenario
                    where status='In use' or name = %s
                    """,
                    (DEFAULT_DB_ALIAS,),
                )
                for i in cursor.fetchall():
                    try:
                        print("Start migrating database %s" % i[0].upper())
                        options["database"] = i[0]
                        run_migrate()
                        print("Successfully migrated database %s" % i[0].upper())
                    except Exception as e:
                        print("ERROR migrating database %s: %s" % (i[0].upper(), e))
        except Exception:
            options["database"] = DEFAULT_DB_ALIAS
            run_migrate()
