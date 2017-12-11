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
import socket

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.contrib.staticfiles.handlers import StaticFilesHandler

from freppledb import VERSION


class Command(BaseCommand):

  help = '''
    Runs a multithreaded web server for frePPLe.
  '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      "--port", type=int, default=settings.PORT,
      help="Port number of the server."
      )
    parser.add_argument(
      "--address", help="IP address for the server to listen."
      ),
    parser.add_argument(
      "--threads", type=int, default=25,
      help="Number of server threads (default: 25)."
      )


  def handle(self, **options):
    from cherrypy.wsgiserver import CherryPyWSGIServer

    # Determine the port number
    port = options['port']

    # Determine the number of threads
    threads = options['threads']
    if threads < 1:
      raise Exception("Invalid number of threads: %s" % threads)

    # Determine the IP-address to listen on:
    # - either as command line argument
    # - either 0.0.0.0 by default, which means all active IPv4 interfaces
    address = options['address'] or '0.0.0.0'

    # Validate the address and port number
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind( (address, port) )
      s.close()
    except socket.error as e:
      raise Exception("Invalid address '%s' and/or port '%s': %s" % (address, port, e))

    # Print a header message
    hostname = socket.getfqdn()
    print('Starting frePPLe %s web server\n' % VERSION)
    print('To access the server, point your browser to either of the following URLS:')
    if address == '0.0.0.0':
      print('    http://%s:%s/' % (hostname, port))
      for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
        print('    http://%s:%s/' % (ip, port))
    else:
      print('    http://%s:%s/' % (address, port))
    print('Quit the server with CTRL-C.\n')

    # Run the WSGI server
    server = CherryPyWSGIServer(
      (address, port),
      StaticFilesHandler(WSGIHandler()),
      numthreads=threads
      )
    # Want SSL support? Just set these attributes apparently, but I haven't tested or verified this
    #  server.ssl_certificate = <filename>
    #  server.ssl_private_key = <filename>
    try:
      server.start()
    except KeyboardInterrupt:
      server.stop()
