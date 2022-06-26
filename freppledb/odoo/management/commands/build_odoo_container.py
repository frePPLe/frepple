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
            "--nopullbase",
            action="store_false",
            dest="pullbase",
            default=True,
            help="Disable refreshing the odoo base image",
        )
        parser.add_argument(
            "--nodatabaserebuild",
            action="store_false",
            dest="databaserebuild",
            default=True,
            help="Disable refreshing the odoo database",
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

        # Used as docker image name, docker container name, odoo database name
        name = "odoo_frepple_%s" % odooversion

        if options["pullbase"]:
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

        if options["databaserebuild"]:
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
                    "--init=base,purchase,mrp,sale,stock,frepple",
                    "--database=%s" % name,
                    "--stop-after-init",
                ]
            )

        print("CREATING DOCKER CONTAINER")
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "-p",
                "8069:8069",
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
            ]
        )
