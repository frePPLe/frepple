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
from optparse import make_option
from cherrypy.wsgiserver import CherryPyWSGIServer

import django
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler

class Command(BaseCommand):

  help = '''
    Runs a multithreaded web server for serving django.

    Because of the multithreading it is is more performant than the default
    development web server bundled with django.
    However, it should still only be used for configurations with a single user,
    and is not an alternative to using mod_python on Apache.
  '''

  option_list = BaseCommand.option_list + (
    make_option("--port", dest="port", default=8000,
                  help="Port number of the server.", type="int"),
    make_option("--address", dest="address",
                  help="IP address for the server to listen.", type="string",
                  default=socket.getaddrinfo(socket.gethostname(), None)[0][4][0]),
    )

  requires_model_validation = False

  def get_version(self):
    return settings.FREPPLE_VERSION

  def handle(self, **options):

    # Validate the address and port number
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind( (options['address'], options['port']) )
      s.close()
    except socket.error, e:
      raise Exception('Invalid address and/or port: %s' % e)

    # Print a header message
    print 'Running Frepple %s with database %s\n' % (settings.FREPPLE_VERSION,settings.DATABASE_NAME)
    print 'To access the server, point your browser to http://%s:%s/' % (options['address'], options['port'])
    print 'Three users are created by default: "admin", "frepple" and "guest" (the password is equal to the user name)\n'
    print 'Quit the server with CTRL-C.\n'

    # Detect the media directory
    media = os.path.join(django.__path__[0],'contrib','admin','media')
    if not os.path.exists(media)or not S_ISDIR(os.stat(media)[ST_MODE]):
      # Media path used by the py2exe executable
      media = os.path.join(settings.FREPPLE_APP,'media')
      if not os.path.exists(media)or not S_ISDIR(os.stat(media)[ST_MODE]):
        raise Exception("No valid media directory found")

    # Run the WSGI server
    server = CherryPyWSGIServer(
      (options['address'], options['port']),
      AdminMediaHandler(WSGIHandler(), media)
      )
    # Want SSL support? Just set these attributes apparantly, but I haven't tested or verified this
    #  server.ssl_certificate = <filename>
    #  server.ssl_private_key = <filename>
    try:
      server.start()
    except KeyboardInterrupt:
      server.stop()
