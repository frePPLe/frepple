#!/usr/bin/env python

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
# email : jdetaeye@users.sourceforge.net

import sys, os, os.path, socket
from stat import S_ISDIR, ST_MODE
from optparse import OptionParser, OptionValueError
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler
from django.core import management
from cherrypy.wsgiserver import CherryPyWSGIServer

# Environment settings (which are used in the Django settings file and need
# to be updated BEFORE importing the settings)
os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
os.environ['FREPPLE_APP'] = os.path.split(sys.path[0])[0]

# Sys.path contains the zip file with all packages. We need to put the
# freppledb subdirectory from the zip-file separately on the path because
# our django applications never refer to the project name.
sys.path = [ os.path.join(sys.path[0],'freppledb'), sys.path[0] ]

# Import django settings
from django.conf import settings

# Define the command line options
parser = OptionParser(
  version='frepple %s' % settings.FREPPLE_VERSION,
  usage= '''usage: %prog [options] [action]

Actions:
  runserver      Run the web server.
                 This is the default action.
  shell          Run an interactive Python interpreter.
  dbshell        Run an interactive SQL session on the database.
  syncdb         Create the database tables.
  test           Run the test suite.
''',
  )
parser.add_option("-m", "--model", dest="model",
                  help="Frepple home directory.", type="string")
parser.add_option("-p", "--port", dest="port", default=8000,
                  help="Port number of the server.", type="int")
parser.add_option("-a", "--address", dest="address",
                  help="IP address for the server to listen.", type="string",
                  default=socket.getaddrinfo(socket.gethostname(), None)[0][4][0])
parser.add_option("-s", "--silent", dest="silent", action="store_true",
                  help="Avoid interactive prompts.")

# Parse the command line
(options, args) = parser.parse_args()

# Validate the model directory
if options.model == None:
  if 'FREPPLE_HOME' in os.environ:
    options.model = default=os.environ['FREPPLE_HOME']
  else:
    print 'Missing frepple model directory'
    sys.exit(1)
if not os.path.exists(options.model)or not S_ISDIR(os.stat(options.model)[ST_MODE]):
  print "Directory %s doesn't exist" % options.model
  sys.exit(1)

# Validate the address and port number
try:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind( (options.address, options.port) )
  s.close()
except socket.error, e:
  print 'Invalid address and/or port: %s' % e
  sys.exit(1)

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
elif settings.DATABASE_ENGINE not in ['postgresql_psycopg2', 'mysql']:
    print 'Aborting: Unknown database engine %s' % settings.DATABASE_ENGINE
    if not options.silent: raw_input("Hit any key to continue...")
    sys.exit(1)
else:
  # PostgreSQL or MySQL database:
  # Try connecting and check for a table called 'plan'.
  from django.db import connection, transaction
  try: cursor = connection.cursor()
  except Exception, e:
    print "Aborting: Can't connect to the database"
    print "   %s" % e
    if not options.silent: raw_input("Hit any key to continue...")
    sys.exit(1)
  try: cursor.execute("SELECT name FROM plan")
  except: noDatabaseSchema = True
  transaction.commit_unless_managed()

if noDatabaseSchema:
  print "\nDatabase schema %s doesn't exist." % settings.DATABASE_NAME
  if not options.silent:
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
  management.call_command('syncdb', verbosity=1)

# Do the action
try:
  action = args[0]
  if action == 'shell':
    # Runs a Python interactive interpreter.
    management.call_command('shell', verbosity=1)
    sys.exit(0)
  elif action == 'dbshell':
    # Runs a Python interactive interpreter.
    management.call_command('dbshell', verbosity=1)
    sys.exit(0)
  elif action == 'syncdb':
    # Initializes a database
    management.call_command('syncdb', verbosity=1)
    sys.exit(0)
  elif action == 'test':
    # Run the test suite
    management.call_command('test', verbosity=1)
    sys.exit(0)
  elif action != 'runserver':
    # Unsupported action
    print "Aborting: Invalid action '%s'" % action
    parser.print_help()
    sys.exit(1)
except IndexError:
  # When no arguments are given: run the server
  pass

# Running the cherrypy wsgi server is the default action

# Print a header message
print 'Running Frepple %s with database %s\n' % (settings.FREPPLE_VERSION,settings.DATABASE_NAME)
print 'To access the server, point your browser to http://%s:%s/' % (options.address, options.port)
print 'Three users are created by default: "admin", "frepple" and "guest" (the password is equal to the user name)\n'
print 'Quit the server with CTRL-C.\n'

# Run the WSGI server
server = CherryPyWSGIServer(
  (options.address, options.port),
  AdminMediaHandler(WSGIHandler(), os.path.join(settings.FREPPLE_APP,'media'))
  )
# Want SSL support? Just set these attributes apparantly, but I haven't tested or verified this
#  server.ssl_certificate = <filename>
#  server.ssl_private_key = <filename>
try:
  server.start()
except KeyboardInterrupt:
  server.stop()
