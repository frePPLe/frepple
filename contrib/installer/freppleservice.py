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

import cx_Logging
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
    from django.conf import settings
    import cherrypy
    from cherrypy.wsgiserver import CherryPyWSGIServer
    import django
    from django.core.handlers.wsgi import WSGIHandler
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from stat import S_ISDIR, ST_MODE

    # Initialize logging
    cx_Logging.StartLogging(
      os.path.join(settings.FREPPLE_LOGDIR,'service.log'),
      level = cx_Logging.DEBUG,
      maxFiles = 1,
      prefix = "%t"
      )

    try:
      # Using the included postgres database
      # Check if the database is running. If not, start it.
      if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
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
          cx_Logging.Info("Starting the PostgreSQL database")
          call([
            os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
            "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
            "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
            "start"
            ])

      # Override the debugging settings
      settings.DEBUG = False
      settings.TEMPLATE_DEBUG = False

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
      self.server = CherryPyWSGIServer(('0.0.0.0', settings.PORT),
        StaticFilesHandler(WSGIHandler())
        )

      # Infinite loop serving requests
      # The loop gets interrupted when the service gets ordered to shut down.
      cx_Logging.Info("frePPLe web server listening on http://localhost:%d" % settings.PORT)
      self.server.start()

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
          stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL
          )
        if not status:
          cx_Logging.Info("Shutting down the database")
          call([
            os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
            "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
            "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
            "-w", # Wait till it's down
            "stop"
            ],
            stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL
            )

      # Notify the manager
      self.stopEvent.set()

    except Exception as e:
      cx_Logging.Error("frePPLe web server failure: %s" % e)


  # Called when the service is being stopped by the service manager GUI
  def Stop(self):
    if not self.server:
      return

    # Stop the CherryPy server
    self.server.stop()

    # Wait till stopped
    self.stopEvent.wait()
