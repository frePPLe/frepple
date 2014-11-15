#
# Copyright (C) 2010-2013 by Johan De Taeye, frePPLe bvba
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

import win32serviceutil
import win32service
import servicemanager

# TODO event log not nice: eventmessagefile (stored in registry) is not valid (refers to file inside zip file)

class frePPLeService(win32serviceutil.ServiceFramework):

    _svc_name_ = "frepple-service"
    _svc_display_name_ = "frePPLe web server"
    _svc_description_ = "Runs a web server for frePPLe"

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # Stop CherryPy server
        self.server.stop()
        # Log stop event
        msg = "frePPLe web server stopped"
        servicemanager.LogInfoMsg(msg)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)

    def SvcDoRun(self):
        # Environment settings (which are used in the Django settings file and need
        # to be updated BEFORE importing the settings)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
        os.environ['FREPPLE_APP'] = os.path.join(os.path.split(sys.path[0])[0],'custom')
        os.environ['FREPPLE_HOME'] = os.path.abspath(os.path.dirname(sys.argv[0]))

        # Add the custom directory to the Python path.
        sys.path = [ os.environ['FREPPLE_APP'], sys.path[0] ]

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

        # Log usage
        from freppledb.execute.management.commands.frepple_runserver import CheckUpdates
        CheckUpdates().start()

        # Infinite loop serving requests
        try:
          self.server.start()
        except Exception as e:
          # Log an error event
          msg = "frePPLe web server failed to start:\n%s" % e
          servicemanager.LogErrorMsg(msg)
          print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)


if __name__=='__main__':
    # Do with the service whatever option is passed in the command line
    win32serviceutil.HandleCommandLine(frePPLeService)
