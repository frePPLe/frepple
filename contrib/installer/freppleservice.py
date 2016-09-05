#
# Copyright (C) 2010-2013 by frePPLe bvba
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

from datetime import datetime
import os
import sys
import threading


NAME = 'frePPLe_%s'
DISPLAY_NAME = 'frePPLe supply chain planning service - %s'
MODULE_NAME = 'freppleservice'
CLASS_NAME = 'ServiceHandler'
DESCRIPTION = 'frePPLe is an open source supply chain planning application. Visit https://frepple.com for more details.'
AUTO_START = True
SESSION_CHANGES = False


class ServiceHandler(object):

  def __init__(self):
    # Event flag to communicate between the Run and Stop methods
    self.stopEvent = threading.Event()
    self.server = None


  # Called when the service is starting
  def Initialize(self, configFileName):
    # Environment settings (which are used in the Django settings file and need
    # to be updated BEFORE importing the settings)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
    os.environ['FREPPLE_APP'] = os.path.join(sys.path[0], 'custom')
    os.environ['FREPPLE_HOME'] = os.path.abspath(os.path.dirname(sys.argv[0]))

    # Add the custom directory to the Python path.
    sys.path += [ os.environ['FREPPLE_APP'] ]


  # Called when the service is starting immediately after Initialize()
  # use this to perform the work of the service; don't forget to set or check
  # for the stop event or the service GUI will not respond to requests to
  # stop the service
  def Run(self):
    # Import modules
    import cherrypy
    from cherrypy.wsgiserver import CherryPyWSGIServer
    from stat import S_ISDIR, ST_MODE
    from subprocess import call, DEVNULL
    from win32process import DETACHED_PROCESS, CREATE_NO_WINDOW

    # Initialize django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', "freppledb.settings")
    os.environ.setdefault('FREPPLE_APP', os.path.join(sys.path[0],'custom'))
    import django
    django.setup()
    from django.core import management
    from django.conf import settings
    from django.core.handlers.wsgi import WSGIHandler
    from django.contrib.staticfiles.handlers import StaticFilesHandler

    # Override the debugging settings
    settings.DEBUG = False
    settings.TEMPLATE_DEBUG = False

    # Sys.path contains the zip file with all packages. We need to put the
    # application directory into the path as well.
    sys.path += [ os.environ['FREPPLE_APP'] ]

    # Append all output to a unbuffered log stream
    with open(os.path.join(settings.FREPPLE_LOGDIR,'service.log'), 'a') as logfile:
      sys.stderr = sys.stdout = logfile
      try:
        # Using the included postgres database
        # Check if the database is running. If not, start it.
        if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
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
            print("%s\tStarting the PostgreSQL database" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)
            call([
              os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
              "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
              "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
              "start"
              ],
              stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
              creationflags=DETACHED_PROCESS
              )

        # Prepare web server
        cherrypy.config.update({
          'global':{
            'log.screen': False,
            'tools.log_tracebacks.on': True,
            'engine.autoreload.on': False,
            'engine.SIGHUP': None,
            'engine.SIGTERM': None
            }
          })
        self.server = CherryPyWSGIServer(('127.0.0.1', settings.PORT),
          StaticFilesHandler(WSGIHandler())
          )

        # Synchronize the scenario table with the settings
        from freppledb.common.models import Scenario
        Scenario.syncWithSettings()

        # Infinite loop serving requests
        # The loop gets interrupted when the service gets ordered to shut down.
        print("%s\tfrePPLe web server listening on http://localhost:%d" % (
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"), settings.PORT
          ), flush=True)
        self.server.start()
        print("%s\tStopping service" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)

        # Using the included postgres database?
        if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
          # Check if the database is running. If so, stop it.
          os.environ['PATH'] = os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin') + os.pathsep + os.environ['PATH']
          from subprocess import call, DEVNULL
          status = call([
            os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
            "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
            "--silent",
            "status"
            ],
            stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
            creationflags=CREATE_NO_WINDOW
            )
          if not status:
            print("%s\tShutting down the database", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)
            call([
              os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
              "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
              "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
              "-w", # Wait till it's down
              "stop"
              ],
              stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
              creationflags=CREATE_NO_WINDOW
              )

        # Notify the manager
        self.stopEvent.set()

      except Exception as e:
        print("%s\tfrePPLe web server failure: %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e), flush=True)


  # Called when the service is being stopped by the service manager GUI
  def Stop(self):
    if not self.server:
      return

    # Stop the CherryPy server
    self.server.stop()

    # Wait till stopped
    self.stopEvent.wait()
