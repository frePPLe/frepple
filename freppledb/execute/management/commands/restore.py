#
# Copyright (C) 2007-2013 by frePPLe bv
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
import os.path
import pathlib
import subprocess
import sys

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import __version__


class Command(BaseCommand):
    help = """
    This command restores a database dump of the frePPLe database.
    """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to restore into",
        )
        parser.add_argument("dump", help="Database dump file to restore.", nargs="?")

    def handle(self, **options):
        # Pick up the options
        database = options["database"]
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)

        dump = options["dump"]
        if not dump:
            if sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty():
                # Running interactive shell
                dumps = [
                    f.name
                    for f in pathlib.Path(settings.FREPPLE_LOGDIR).rglob("*.dump")
                ]
                if not dumps:
                    raise CommandError("No database dumps available")
                print(f"\nAvailable dumps:")
                for i, o in enumerate(dumps, start=1):
                    print(f"   {i}. {o}")
                while True:
                    try:
                        choice = int(
                            input(f"Select a dump to restore (1–{len(dumps)}): ")
                        )
                        if 1 <= choice <= len(dumps):
                            dump = dumps[choice - 1]
                            break
                        else:
                            print("Invalid choice. Try again.")
                    except ValueError:
                        print("Invalid choice. Try again.")
            else:
                raise CommandError("No database dump argument provided")

        # Validate options
        dumpfile = os.path.abspath(os.path.join(settings.FREPPLE_LOGDIR, dump))
        if not os.path.isfile(dumpfile):
            raise CommandError("Dump file not found")
        env = os.environ.copy()
        if settings.DATABASES[database]["PASSWORD"]:
            env["PGPASSWORD"] = settings.DATABASES[database]["PASSWORD"]
        commonargs = []
        if settings.DATABASES[database]["USER"]:
            commonargs.append(f"--username={settings.DATABASES[database]["USER"]}")
        if settings.DATABASES[database]["HOST"]:
            commonargs.append(f"--host={settings.DATABASES[database]["HOST"]}")
        if settings.DATABASES[database]["PORT"]:
            commonargs.append(f"--port={settings.DATABASES[database]["PORT"]}")

        # Drop existing database
        subprocess.run(
            ["dropdb", "--if-exists", "--force"]
            + commonargs
            + [settings.DATABASES[database]["NAME"]],
            env=env,
            check=True,
        )

        # Recreate a new database
        subprocess.run(
            ["createdb"] + commonargs + [settings.DATABASES[database]["NAME"]],
            env=env,
            check=True,
        )

        # Restore the dump
        subprocess.run(
            [
                "pg_restore",
                "--clean",
                "--if-exists",
                "-v",
                "--no-owner",
                f"--role={settings.DATABASES[database]["USER"]}",
            ]
            + commonargs
            + [f"--dbname={settings.DATABASES[database]["NAME"]}", dumpfile],
            env=env,
        )
