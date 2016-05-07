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

# Environment settings (which are used in the Django settings file and need
# to be updated BEFORE importing the settings)
os.environ.setdefault('FREPPLE_HOME', os.path.split(sys.path[0])[0])
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "freppledb.settings")
os.environ.setdefault('FREPPLE_APP', os.path.join(os.path.split(sys.path[0])[0],'custom'))

# Sys.path contains the zip file with all packages. We need to put the
# application directory into the path as well.
sys.path += [ os.environ['FREPPLE_APP'] ]

# Initialize django
import django
django.setup()

# Import django
from django.core.management import execute_from_command_line, call_command
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
  # Using the included postgres database
  # Check if the database is running. If not, start it.
  from subprocess import call, DEVNULL
  status = call([
    os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
    "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
    "--silent",
    "status"
    ],
    stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL
    )
  if status:
    print("Starting the PostgreSQL database now", settings.FREPPLE_LOGDIR)
    call([
      os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
      "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
      "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
      "-w", # Wait till it's up
      "start"
      ])

# Execute the command
execute_from_command_line(sys.argv)
