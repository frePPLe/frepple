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

from freppledb.settings import *
from freppledb.manage import *

# Define the command line options
parser = OptionParser(version=settings.FREPPLE_VERSION)
parser.add_option("-m", "--model", dest="model",
                  help="frepple home directory", type="string")
parser.add_option("-p", "--port", dest="port", default=8000,
                  help="port number of the server", type="int")
parser.add_option("-a", "--address", dest="address",
                  help="IP address for the server to listen", type="string",
                  default=socket.getaddrinfo(socket.gethostname(), None)[0][4][0])

# Parse the command line
(options, args) = parser.parse_args()

# Validate the model directory
if options.model == None:
  if 'FREPPLE_HOME' in os.environ:
    options.model = default=os.environ['FREPPLE_HOME']
  else:
    print 'Missing frepple model directory'
    sys.exit(1)
if not S_ISDIR(os.stat(options.model)[ST_MODE]):
  print "Directory %s doesn't exist" % options.model
  sys.exit(1)

# Validate the address and port number
try:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind( (options.address, options.port) )
  s.close()
except socket.error, e:
  print 'Invalid address and port: %s' % e
  sys.exit(1)

# Update the root directory of the application
settings.FREPPLE_APP = os.path.split(sys.path[0])[0]

# Update the template dirs
settings.TEMPLATE_DIRS = (
    # Always use forward slashes, even on Windows.
    os.path.join(settings.FREPPLE_APP,'templates2').replace('\\','/'),
    os.path.join(settings.FREPPLE_APP,'templates1').replace('\\','/'),
    settings.FREPPLE_HOME.replace('\\','/'),
)

# Run the server
print 'Frepple %s \n' % settings.FREPPLE_VERSION
execute_manager(settings, ['','runserver',
  '--adminmedia=%s' % os.path.join(settings.FREPPLE_APP,'media'),
  '--noreload',
  '%s:%d' % (options.address, options.port)
  ])
