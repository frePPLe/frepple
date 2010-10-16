#
# Copyright (C) 2007-2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

import sys, os, os.path, socket
from threading import Thread
from stat import S_ISDIR, ST_MODE
from optparse import make_option
from cherrypy.wsgiserver import CherryPyWSGIServer

import django
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler
from django.db.utils import DEFAULT_DB_ALIAS

class Command(BaseCommand):

  help = '''
    Runs a multithreaded web server for frePPLe.

    Because of the multithreading it is is more performant than the default
    development web server bundled with django.
    However, it should still only be used for configurations with a single user,
    and is not a full alternative to using Apache + mod_wsgi.
  '''

  option_list = BaseCommand.option_list + (
    make_option("--port", dest="port", type="int",
                  help="Port number of the server."),
    make_option("--address", dest="address", type="string",
                  help="IP address for the server to listen."),
    )

  requires_model_validation = False

  def get_version(self):
    return settings.FREPPLE_VERSION

  def handle(self, **options):
    # Determine the port number
    if 'port' in options: 
      port = int(options['port'] or settings.PORT)
    else: 
      port = settings.PORT

    # Determine the IP-address to listen on:
    # - either as command line argument
    # - automatically detected IP-address
    # - use 127.0.0.1 as a safe fallback
    address = None
    if 'address' in options: address = options['address']
    if address == None:
      try: address = socket.gethostbyname(socket.gethostname())
      except: address = '127.0.0.1'

    # Validate the address and port number
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind( (address, port) )
      s.close()
    except socket.error, e:
      raise Exception("Invalid address '%s' and/or port '%s': %s" % (address, port, e))

    # Print a header message
    print 'Running frePPLe %s with database %s\n' % (settings.FREPPLE_VERSION, settings.DATABASES[DEFAULT_DB_ALIAS]['NAME'])
    print 'To access the server, point your browser to http://%s:%s/' % (address, port)
    print 'Three users are created by default: "admin", "frepple" and "guest" (the password is equal to the user name)\n'
    print 'Quit the server with CTRL-C.\n'

    # Detect the media directory
    media = os.path.join(django.__path__[0],'contrib','admin','media')
    if not os.path.exists(media)or not S_ISDIR(os.stat(media)[ST_MODE]):
      # Media path used by the py2exe executable
      media = os.path.join(settings.FREPPLE_HOME,'media')
      if not os.path.exists(media)or not S_ISDIR(os.stat(media)[ST_MODE]):
        raise Exception("No valid media directory found")

    # Start a seperate thread that will check for updates
    # We don't wait for it to finish
    CheckUpdates().start()
    
    # Run the WSGI server
    server = CherryPyWSGIServer((address, port),
      AdminMediaHandler(WSGIHandler(), media)
      )
    # Want SSL support? Just set these attributes apparantly, but I haven't tested or verified this
    #  server.ssl_certificate = <filename>
    #  server.ssl_private_key = <filename>
    try:
      server.start()
    except KeyboardInterrupt:
      server.stop()


class CheckUpdates(Thread):
  def run(self):
    if settings.DEBUG == False:
      try:
        import urllib 
        import urllib2 
        import re 
        values = {
          'platform' : sys.platform,
          'executable' : sys.executable,
          'version' : settings.FREPPLE_VERSION,
          }
        request = urllib2.Request('http://www.frepple.com/usage.php?' + urllib.urlencode(values))
        response = urllib2.urlopen(request).read()
        match = re.search("<release>(.*)</release>", response)
        release = match.group(1)
        if release > settings.FREPPLE_VERSION:
          print "A new frePPLe release %s is available. Your current release is %s." % (release, settings.FREPPLE_VERSION)
      except:
        # Don't worry if something went wrong. 
        pass
      