#
# Copyright (C) 2007-2013 by frePPLe bvba
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
import sys, os, os.path
from stat import S_ISDIR, ST_MODE
from subprocess import call, DEVNULL
from win32process import DETACHED_PROCESS, CREATE_NO_WINDOW

# Environment settings (which are used in the Django settings file and need
# to be updated BEFORE importing the settings)
os.environ.setdefault('FREPPLE_HOME', sys.path[0])
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "freppledb.settings")
os.environ.setdefault('FREPPLE_APP', os.path.join(sys.path[0],'custom'))
os.environ.setdefault('PYTHONPATH',
  os.path.join(sys.path[0], 'lib', 'library.zip')
  + os.pathsep +
  os.path.join(sys.path[0], 'lib') 
  )

# Add the custom directory to the Python path.
sys.path += [ os.environ['FREPPLE_APP'], ]

# Initialize django
import django
django.setup()

# Import django
from django.core.management import execute_from_command_line
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
  # Using the included postgres database
  # Check if the database is running. If not, start it.
  os.environ['PATH'] = os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin') + os.pathsep + os.environ['PATH']
  status = call([
    os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
    "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
    "--silent",
    "status"
    ],
    stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
    creationflags=CREATE_NO_WINDOW
    )
  if status:
    print("Starting the PostgreSQL database now", settings.FREPPLE_LOGDIR)
    call([
      os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
      "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
      "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
      "-w", # Wait till it's up
      "start"
      ],
      stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
      creationflags=CREATE_NO_WINDOW
      )


# Synchronize the scenario table with the settings
from freppledb.common.models import Scenario
Scenario.syncWithSettings()

# Execute the command
execute_from_command_line(sys.argv)
