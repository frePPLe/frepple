#
# Copyright (C) 2022 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os.path
import psycopg2
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb import __version__


class Command(BaseCommand):

    help = "Utility command for development to spin up an odoo docker container"

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            dest="full",
            default=False,
            help="Complete rebuild of image and database",
        )

    def getOdooVersion(self, dockerfile):
        with open(dockerfile, mode="rt") as f:
            for l in f.read().splitlines():
                if l.startswith("FROM "):
                    return l.split(":", 1)[-1]
            raise CommandError("Can't find odoo version in dockerfile")

    def handle(self, **options):
        dockerfile = os.path.join(
            os.path.dirname(__file__), "..", "..", "odoo_addon", "dockerfile"
        )
        if not os.path.exists(dockerfile):
            raise CommandError("Can't find dockerfile")
        odooversion = self.getOdooVersion(dockerfile)

        # Used as a) docker image name, b) docker container name,
        # c) docker volume name and d) odoo database name.
        name = "odoo_frepple_%s" % odooversion

        if options["full"]:
            print("PULLING ODOO BASE IMAGE")
            subprocess.run(["docker", "pull", "odoo:%s" % odooversion])

        print("BUILDING DOCKER IMAGE")
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                dockerfile,
                "-t",
                name,
                ".",
            ],
            cwd=os.path.join(os.path.dirname(__file__), "..", "..", "odoo_addon"),
        )

        print("DELETE OLD CONTAINER")
        subprocess.run(["docker", "rm", "--force", name])
        if options["full"]:
            subprocess.run(["docker", "volume", "rm", "--force", name])

        if options["full"]:
            print("CREATE NEW DATABASE")
            os.environ["PGPASSWORD"] = settings.DATABASES[DEFAULT_DB_ALIAS]["PASSWORD"]
            extraargs = []
            if settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]:
                extraargs = extraargs + [
                    "-h",
                    settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"],
                ]
            if settings.DATABASES[DEFAULT_DB_ALIAS]["PORT"]:
                extraargs = extraargs + [
                    "-p",
                    settings.DATABASES[DEFAULT_DB_ALIAS]["PORT"],
                ]
            subprocess.run(
                [
                    "dropdb",
                    "-U",
                    settings.DATABASES[DEFAULT_DB_ALIAS]["USER"],
                    "--force",
                    "--if-exists",
                    name,
                ]
                + extraargs
            )
            subprocess.run(
                [
                    "createdb",
                    "-U",
                    settings.DATABASES[DEFAULT_DB_ALIAS]["USER"],
                    name,
                ]
                + extraargs
            )

            print("INITIALIZE ODOO DATABASE")
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-it",
                    "-v",
                    "%s:/var/lib/odoo" % name,
                    "-e",
                    "HOST=%s"
                    % (
                        "host.docker.internal"
                        if not settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]
                        else settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]
                    ),
                    "-e",
                    "USER=%s" % settings.DATABASES[DEFAULT_DB_ALIAS]["USER"],
                    "-e",
                    "PASSWORD=%s" % settings.DATABASES[DEFAULT_DB_ALIAS]["PASSWORD"],
                    "--name",
                    name,
                    "-t",
                    name,
                    "odoo",
                    "--init=base,product,purchase,sale,sale_management,resource,mrp,frepple,autologin",
                    "--load=web,autologin",
                    "--database=%s" % name,
                    "--stop-after-init",
                ]
            )

            print("CONFIGURE ODOO DATABASE")
            conn_params = {
                "database": name,
                "user": settings.DATABASES[DEFAULT_DB_ALIAS]["USER"],
                "password": settings.DATABASES[DEFAULT_DB_ALIAS]["PASSWORD"],
            }
            if settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]:
                conn_params["host"] = settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]
            if settings.DATABASES[DEFAULT_DB_ALIAS]["PORT"]:
                conn_params["port"] = settings.DATABASES[DEFAULT_DB_ALIAS]["PORT"]
            with psycopg2.connect(**conn_params) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        update res_company set
                          manufacturing_warehouse = (
                             select id
                             from stock_warehouse
                             where name = 'San Francisco'
                             ),
                          webtoken_key = '%s',
                          frepple_server = 'http://localhost:8000',
                          disclose_stack_trace = true
                        where name = 'My Company (San Francisco)'
                        """
                        % settings.SECRET_KEY
                    )
                    cursor.execute(
                        """
                        update res_company set
                          manufacturing_warehouse = (
                             select id
                             from stock_warehouse
                             where name = 'Chicago 1'
                             ),
                          webtoken_key = '%s',
                          frepple_server = 'http://localhost:8000',
                          disclose_stack_trace = true
                        where name = 'My Company (Chicago)'
                        """
                        % settings.SECRET_KEY
                    )

        print("CREATING DOCKER CONTAINER")
        container = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "-p",
                "8069:8069",
                "-p",
                "8071:8071",
                "-p",
                "8072:8072",
                "-v",
                "%s:/var/lib/odoo" % name,
                "-e",
                "HOST=%s"
                % (
                    "host.docker.internal"
                    if not settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]
                    else settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]
                ),
                "-e",
                "USER=%s" % settings.DATABASES[DEFAULT_DB_ALIAS]["USER"],
                "-e",
                "PASSWORD=%s" % settings.DATABASES[DEFAULT_DB_ALIAS]["PASSWORD"],
                "--name",
                name,
                "-t",
                name,
                "odoo",
                "--database=%s" % name,
            ],
            capture_output=True,
            text=True,
        ).stdout

        print("CONTAINER READY: %s " % container)
        print("Hit CTRL-C to stop displaying the container log")
        subprocess.run(["docker", "attach", container], shell=True)
