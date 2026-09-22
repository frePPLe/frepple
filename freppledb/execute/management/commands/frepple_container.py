#
# Copyright (C) 2026 by frePPLe bv
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
import shutil
import subprocess
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

import freppledb
from freppledb import __version__


class Command(BaseCommand):
    help = """
    Development utility command to run a docker container with the current source code.
    """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-build",
            action="store_true",
            dest="no_build",
            default=False,
            help="Skip compiling and building the docker image, and only (re)start the container",
        )
        parser.add_argument(
            "--destroy",
            action="store_true",
            dest="destroy",
            default=False,
            help="Use this option to clean up all docker objects",
        )
        parser.add_argument(
            "--nolog",
            action="store_true",
            dest="nolog",
            default=False,
            help="Don't tail the container log at the end of this command",
        )
        parser.add_argument(
            "--container-port",
            type=int,
            default=9999,
            help="Port to publish the frepple web server on. Defaults to 9999",
        )
        parser.add_argument(
            "--memory",
            default="20g",
            help="Memory limit for the container. Defaults to 20g",
        )
        parser.add_argument(
            "--docker-arg",
            action="append",
            help="Extra arguments to pass to the 'docker run' command. Can be used multiple times.",
        )

    def handle(self, **options):
        # Name used for both the docker container and the derived docker image
        container_name = "frepple_community"
        # Image produced by the cmake "docker" target
        base_image = "frepple-community:%s" % __version__

        # Root of the git checkout, ie the parent folder of the freppledb package
        root = os.path.abspath(os.path.join(os.path.dirname(freppledb.__file__), ".."))

        # This command only makes sense in a development checkout, never in a production deployment
        if not os.path.isdir(os.path.join(root, ".git")):
            raise CommandError("This command is only available in a git checkout")

        # Building the docker image
        if not options["no_build"]:
            build_dir = os.path.join(root, "build")
            if not os.path.isfile(os.path.join(build_dir, "CMakeCache.txt")):
                raise CommandError(
                    "No configured cmake build directory found at '%s'" % build_dir
                )
            if options["verbosity"]:
                print("COMPILING AND BUILDING THE DOCKER IMAGE")
            result = subprocess.run(
                ["cmake", "--build", build_dir, "--target", "docker"]
            )
            if result.returncode:
                raise CommandError("Building the docker image failed")

        # Populate a folder with files to pass to the container
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "dockerfile"), "w") as dockerfile:
                print("FROM %s" % base_image, file=dockerfile)

                localsettings = os.path.join(root, "localsettings.py")
                if os.path.isfile(localsettings):
                    # Localsettings
                    print(
                        "COPY localsettings.py /etc/frepple/localsettings.py",
                        file=dockerfile,
                    )
                    shutil.copy(localsettings, os.path.join(tmpdir, "localsettings.py"))

                # Custom apps
                apps = {
                    app.split(".")[1]
                    for app in settings.INSTALLED_APPS
                    if app.startswith("freppleapps.")
                }
                for app in sorted(apps):
                    appdir = os.path.join(root, "freppleapps", app)
                    if os.path.isdir(appdir):
                        print(
                            "COPY freppleapps/%s /usr/share/frepple/venv/lib/python3.12/site-packages/freppleapps/%s"
                            % (app, app),
                            file=dockerfile,
                        )
                        shutil.copytree(
                            appdir,
                            os.path.join(tmpdir, "freppleapps", app),
                        )

                # License file
                license = os.path.join(root, "bin", "license.xml")
                if os.path.isfile(license):
                    print("COPY license.xml /etc/frepple/license.xml", file=dockerfile)
                    shutil.copy(license, os.path.join(tmpdir, "license.xml"))

                # Environment variables for PostgreSQL
                print(
                    f'ENV POSTGRES_HOST="{"host.docker.internal" if settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"] == "localhost" else settings.DATABASES[DEFAULT_DB_ALIAS]["HOST"]}"',
                    file=dockerfile,
                )
                print(
                    f'ENV POSTGRES_PORT="{settings.DATABASES[DEFAULT_DB_ALIAS]["PORT"] or 5432}"',
                    file=dockerfile,
                )
                print(
                    f'ENV POSTGRES_USER="{settings.DATABASES[DEFAULT_DB_ALIAS]["USER"]}"',
                    file=dockerfile,
                )
                print(
                    f'ENV POSTGRES_PASSWORD="{settings.DATABASES[DEFAULT_DB_ALIAS]["PASSWORD"]}"',
                    file=dockerfile,
                )
                print(
                    f'ENV POSTGRES_DBNAME="{settings.DATABASES[DEFAULT_DB_ALIAS]["NAME"]}"',
                    file=dockerfile,
                )
            result = subprocess.run(
                [
                    "docker",
                    "build",
                    "--progress=plain",
                    "-t",
                    container_name,
                    tmpdir,
                ]
            )
            if result.returncode:
                raise CommandError("Building the docker image failed")

        subprocess.run(["docker", "rm", "--force", container_name])

        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--add-host",
                "host.docker.internal:host-gateway",
                "-p",
                "%s:80" % options["container_port"],
                "--memory",
                options["memory"],
                "--name",
                container_name,
                *(options["docker_arg"] or []),
                container_name,
            ]
        )
        if result.returncode:
            raise CommandError("Starting the docker container failed")

        if not options["nolog"]:
            print("Hit CTRL-C to stop displaying the container log")
            subprocess.run(["docker", "logs", "--follow", container_name])
