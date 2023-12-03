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

import os.path
import subprocess
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb.execute.models import Task
from freppledb.common.models import User
from freppledb import __version__


class Command(BaseCommand):
    help = """
    This command restores a database dump of the frePPLe database.

    The pg_restore command needs to be in the path, otherwise this command
    will fail.
    """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="User running the command")
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates a specific database to restore into",
        )
        parser.add_argument(
            "--task",
            type=int,
            help="Task identifier (generated automatically if not provided)",
        )
        parser.add_argument("dump", help="Database dump file to restore.")

    def handle(self, **options):
        # Pick up the options
        database = options["database"]
        if database not in settings.DATABASES:
            raise CommandError("No database settings known for '%s'" % database)
        if options["user"]:
            try:
                user = User.objects.all().using(database).get(username=options["user"])
            except Exception:
                raise CommandError("User '%s' not found" % options["user"])
        else:
            user = None

        now = datetime.now()
        task = None
        try:
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
                    or task.name not in ("frepple_restore", "restore")
                ):
                    raise CommandError("Invalid task identifier")
                task.status = "0%"
                task.started = now
            else:
                task = Task(
                    name="restore", submitted=now, started=now, status="0%", user=user
                )
            task.arguments = options["dump"]
            task.processid = os.getpid()
            task.save(using=database)

            # Validate options
            dumpfile = os.path.abspath(
                os.path.join(settings.FREPPLE_LOGDIR, options["dump"])
            )
            if not os.path.isfile(dumpfile):
                raise CommandError("Dump file not found")

            # Run the restore command
            # Commenting the next line is a little more secure, but requires you to create a .pgpass file.
            if settings.DATABASES[database]["PASSWORD"]:
                os.environ["PGPASSWORD"] = settings.DATABASES[database]["PASSWORD"]
            cmd = ["pg_restore", "-n", "public", "-Fc", "-c", "--if-exists"]
            if settings.DATABASES[database]["USER"]:
                cmd.append("--username=%s" % settings.DATABASES[database]["USER"])
            if settings.DATABASES[database]["HOST"]:
                cmd.append("--host=%s" % settings.DATABASES[database]["HOST"])
            if settings.DATABASES[database]["PORT"]:
                cmd.append("--port=%s " % settings.DATABASES[database]["PORT"])
            cmd.append("-d")
            cmd.append(settings.DATABASES[database]["NAME"])
            cmd.append("<%s" % dumpfile)
            # Shell needs to be True in order to interpret the < character
            with subprocess.Popen(cmd, shell=True) as p:
                try:
                    task.processid = p.pid
                    task.save(using=database)
                    p.wait()
                except Exception:
                    p.kill()
                    p.wait()
                    raise Exception("Database restoration failed")

            # Task update
            # We need to recreate a new task record, since the previous one is lost during the restoration.
            task = Task(
                name="restore",
                submitted=task.submitted,
                started=task.started,
                arguments=task.arguments,
                status="Done",
                finished=datetime.now(),
                user=task.user,
            )

        except Exception as e:
            if task:
                task.status = "Failed"
                task.message = "%s" % e
                task.finished = datetime.now()
            raise e

        finally:
            # Commit it all, even in case of exceptions
            if task:
                task.processid = None
                task.save(using=database)
