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

# Create the database if it doesn't exist yet
noDatabaseSchema = False
if settings.DATABASES[DEFAULT_DB_ALIAS]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
  # PostgreSQL:
  # Try connecting and check for a table called 'parameter'.
  from django.db import connection
  try: cursor = connection.cursor()
  except Exception as e:
    print("Aborting: Can't connect to the database")
    print("   %s" % e)
    input("Hit any key to continue...")
    sys.exit(1)
  try: cursor.execute("SELECT 1 FROM common_parameter")
  except: noDatabaseSchema = True
else:
  print('Aborting: Unknown database engine %s' % settings.DATABASES[DEFAULT_DB_ALIAS]['ENGINE'])
  input("Hit any key to continue...")
  sys.exit(1)

if noDatabaseSchema and len(sys.argv)>1 and sys.argv[1]!='migrate':
  print("\nDatabase schema has not been initialized yet.")
  confirm = input("Do you want to do that now? (yes/no): ")
  while confirm not in ('yes', 'no'):
    confirm = input('Please enter either "yes" or "no": ')
  if confirm == 'yes':
    # Create the database
    print("\nCreating database scheme")
    call_command('migrate', verbosity=1)

# Execute the command
execute_from_command_line(sys.argv)
