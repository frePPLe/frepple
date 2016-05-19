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
import sys
import os
import socket
from datetime import datetime

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
          "start"
          ])
    
    # Import modules
    from django.conf import settings
    import cherrypy
    from cherrypy.wsgiserver import CherryPyWSGIServer
    import django
    from django.core.handlers.wsgi import WSGIHandler
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from stat import S_ISDIR, ST_MODE
  
    # Override the debugging settings
    settings.DEBUG = False
    settings.TEMPLATE_DEBUG = False
  
    # Pick up port and adress
    try: address = socket.gethostbyname(socket.gethostname())
    except: address = '127.0.0.1'
    port = settings.PORT
  
    cherrypy.config.update({
        'global':{
            'log.screen': False,
            'tools.log_tracebacks.on': True,
            'engine.autoreload.on': False,
            'engine.SIGHUP': None,
            'engine.SIGTERM': None
            }
        })
    self.server = CherryPyWSGIServer((address, port),
      StaticFilesHandler(WSGIHandler())
      )
  
    # Redirect all output and log a start event
    try:
      log = os.path.join(settings.FREPPLE_LOGDIR,'service.log')
      sys.stdout = open(log, 'a', 0)
      msg = "frePPLe web server listening on http://%s:%d and logging to %s" % (address, port, log)
      servicemanager.LogInfoMsg(msg)
      print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    except:
      # Too bad if we can't write log info
      servicemanager.LogInfoMsg("frePPLe web server listening on http://%s:%d without log file" % (address, port))
    
    # Infinite loop serving requests
    # The loop gets interrupted when the service gets ordered to shut down.
    try:
      self.server.start()
    except Exception as e:
      # Log an error event
      msg = "frePPLe web server failed to start:\n%s" % e
      servicemanager.LogErrorMsg(msg)
      print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)

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
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Shutting down the database")
        call([
          os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
          "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
          "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
          "-w", # Wait till it's down
          "stop"
          ],
          stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL
          )
      
    self.stopEvent.set()
    

  # Called when the service is being stopped by the service manager GUI
  def Stop(self):
    # Stop the CherryPy server
    self.server.stop()
          
    # Wait till stopped
    self.stopEvent.wait()
