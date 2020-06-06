#
# Copyright (C) 2007-2013 by frePPLe bv
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

from multiprocessing import freeze_support
import os
import os.path
from subprocess import call, DEVNULL
import sys
from win32process import CREATE_NO_WINDOW


def main():
    # Environment settings (which are used in the Django settings file and need
    # to be updated BEFORE importing the settings)
    os.environ.setdefault("FREPPLE_HOME", sys.path[0])
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")
    os.environ.setdefault("FREPPLE_APP", os.path.join(sys.path[0], "custom"))
    os.environ.setdefault(
        "PYTHONPATH",
        os.path.join(sys.path[0], "lib", "library.zip")
        + os.pathsep
        + os.path.join(sys.path[0], "lib"),
    )

    # Add the custom directory to the Python path.
    sys.path += [os.environ["FREPPLE_APP"]]

    # Initialize django
    import django

    django.setup()

    # Import django
    from django.core.management import execute_from_command_line
    from django.conf import settings

    if os.path.exists(
        os.path.join(settings.FREPPLE_HOME, "..", "pgsql", "bin", "pg_ctl.exe")
    ):
        # Using the included postgres database
        # Check if the database is running. If not, start it.
        os.environ["PATH"] = (
            os.path.join(settings.FREPPLE_HOME, "..", "pgsql", "bin")
            + os.pathsep
            + os.environ["PATH"]
        )
        status = call(
            [
                os.path.join(settings.FREPPLE_HOME, "..", "pgsql", "bin", "pg_ctl.exe"),
                "--pgdata",
                os.path.join(settings.FREPPLE_LOGDIR, "database"),
                "--silent",
                "status",
            ],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        if status:
            print("Starting the PostgreSQL database now", settings.FREPPLE_LOGDIR)
            call(
                [
                    os.path.join(
                        settings.FREPPLE_HOME, "..", "pgsql", "bin", "pg_ctl.exe"
                    ),
                    "--pgdata",
                    os.path.join(settings.FREPPLE_LOGDIR, "database"),
                    "--log",
                    os.path.join(settings.FREPPLE_LOGDIR, "database", "server.log"),
                    "-w",  # Wait till it's up
                    "start",
                ],
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL,
                creationflags=CREATE_NO_WINDOW,
            )

    # Synchronize the scenario table with the settings
    from freppledb.common.models import Scenario

    Scenario.syncWithSettings()

    # Execute the command
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    # Support multiprocessing module
    freeze_support()

    # Call the main function
    main()
