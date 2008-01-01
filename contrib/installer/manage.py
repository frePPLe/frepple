#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

import sys, os, os.path
from stat import S_ISDIR, ST_MODE

from django.core.management import execute_manager, call_command

# Environment settings (which are used in the Django settings file and need
# to be updated BEFORE importing the settings)
os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
os.environ['FREPPLE_APP'] = os.path.split(sys.path[0])[0]

# Sys.path contains the zip file with all packages. We need to put the
# freppledb subdirectory from the zip-file separately on the path because
# our django applications never refer to the project name.
sys.path = [ os.path.join(sys.path[0],'freppledb'), sys.path[0] ]

# Default command is to run the web server
if len(sys.argv) <= 1:
  sys.argv.append('frepple_runserver')

# Import django settings
from django.conf import settings

# Override the debugging settings
settings.DEBUG = False
settings.TEMPLATE_DEBUG = False

# Update the directories where fixtures are searched
settings.FIXTURE_DIRS = (
  os.path.join(settings.FREPPLE_APP,'fixtures','input').replace('\\','/'),
  os.path.join(settings.FREPPLE_APP,'fixtures','user').replace('\\','/'),
)

# Update the template dirs
settings.TEMPLATE_DIRS = (
    # Always use forward slashes, even on Windows.
    os.path.join(settings.FREPPLE_APP,'templates2').replace('\\','/'),
    os.path.join(settings.FREPPLE_APP,'templates1').replace('\\','/'),
    settings.FREPPLE_HOME.replace('\\','/'),
)

# Create the database if it doesn't exist yet
noDatabaseSchema = False
if settings.DATABASE_ENGINE == 'sqlite3':
  # Verify if the sqlite database file exists
  if not os.path.isfile(settings.DATABASE_NAME):
    noDatabaseSchema = True
elif settings.DATABASE_ENGINE not in ['postgresql_psycopg2', 'mysql', 'oracle']:
    print 'Aborting: Unknown database engine %s' % settings.DATABASE_ENGINE
    raw_input("Hit any key to continue...")
    sys.exit(1)
else:
  # PostgreSQL, Oracle or MySQL database:
  # Try connecting and check for a table called 'plan'.
  from django.db import connection, transaction
  try: cursor = connection.cursor()
  except Exception, e:
    print "Aborting: Can't connect to the database"
    print "   %s" % e
    raw_input("Hit any key to continue...")
    sys.exit(1)
  try: cursor.execute("SELECT name FROM plan")
  except: noDatabaseSchema = True
  transaction.commit_unless_managed()

if noDatabaseSchema:
  print "\nDatabase schema %s doesn't exist." % settings.DATABASE_NAME
  confirm = raw_input("Do you want to create it now? (yes/no): ")
  while confirm not in ('yes', 'no'):
    confirm = raw_input('Please enter either "yes" or "no": ')
  if confirm == 'no':
    # Honourable exit
    print "Exiting..."
    raw_input("Hit any key to continue...")
    sys.exit(0)
  # Create the database
  print "\nCreating database scheme"
  call_command('syncdb', verbosity=1)

# Execute the command
import freppledb.settings
execute_manager(freppledb.settings, sys.argv)
