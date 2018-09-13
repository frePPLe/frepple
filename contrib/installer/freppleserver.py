#
# Copyright (C) 2014 by frePPLe bvba
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
import argparse
import cx_Logging
from cherrypy.wsgiserver import CherryPyWSGIServer
from datetime import datetime
import os
import socket
from subprocess import call, DEVNULL
import sys
from threading import Thread
import win32api
import win32con
import win32gui_struct
try:
  import winxpgui as win32gui
except ImportError:
  import win32gui
from win32process import DETACHED_PROCESS, CREATE_NO_WINDOW


def log(msg):
  print (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)


# Running WSGI in a thread
class RunWSGIServer(Thread):

  def __init__(self, address, port):
    self.address = address
    self.port = port
    super(RunWSGIServer, self).__init__()

  def run(self):
    try:
      self.server = CherryPyWSGIServer(
        (address, port),
        StaticFilesHandler(WSGIHandler())
        )
      self.server.start()
    except Exception as e:
      log("Server error: %s" % e)


def on_quit(sysTrayIcon):
  wsgi.server.stop()
  log("Stopping web server")


def ShowLogDirectory(sysTrayIcon):
  import subprocess
  subprocess.Popen('explorer "%s"' % settings.FREPPLE_LOGDIR)


def ShowConfigDirectory(sysTrayIcon):
  import subprocess
  subprocess.Popen('explorer "%s"' % settings.FREPPLE_CONFIGDIR)


def OpenBrowser(sysTrayIcon):
  import webbrowser
  webbrowser.open_new_tab("http://%s:%s" % (address == '0.0.0.0' and '127.0.0.1' or address, port))


def OpenCommandWindow(sysTrayIcon):
  import subprocess
  subprocess.Popen('cmd', cwd=settings.FREPPLE_HOME)


# Running a program in the system tray
# The following code is inspired on:
#    http://www.brunningonline.net/simon/blog/archives/SysTrayIcon.py.html
class SysTrayIcon:
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]

    FIRST_ID = 1023

    def __init__(self, icon, hover_text, menu_options, on_quit=None,
                 default_menu_index=None, window_class_name=None):
      self.icon = icon
      self.hover_text = hover_text
      self.on_quit = on_quit

      menu_options = menu_options + (('Quit', None, self.QUIT),)
      self._next_action_id = self.FIRST_ID
      self.menu_actions_by_id = set()
      self.menu_options = self._add_ids_to_menu_options(list(menu_options))
      self.menu_actions_by_id = dict(self.menu_actions_by_id)
      del self._next_action_id
      self.default_menu_index = default_menu_index
      self.window_class_name = window_class_name

      message_map = {
        win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
        win32con.WM_DESTROY: self.destroy,
        win32con.WM_COMMAND: self.command,
        win32con.WM_USER + 20: self.notify,
        }

      # Register the Window class.
      window_class = win32gui.WNDCLASS()
      hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
      window_class.lpszClassName = self.window_class_name
      window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
      window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
      window_class.hbrBackground = win32con.COLOR_WINDOW
      window_class.lpfnWndProc = message_map   # could also specify a wndproc.
      classAtom = win32gui.RegisterClass(window_class)

      # Create the Window.
      style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
      self.hwnd = win32gui.CreateWindow(
        classAtom, self.window_class_name, style, 0, 0,
        win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0,
        hinst, None
        )
      win32gui.UpdateWindow(self.hwnd)
      self.notify_id = None
      self.refresh_icon()

      # Message loop
      win32gui.PumpMessages()

    def _add_ids_to_menu_options(self, menu_options):
      result = []
      for menu_option in menu_options:
        option_text, option_icon, option_action = menu_option
        if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
          self.menu_actions_by_id.add((self._next_action_id, option_action))
          result.append(menu_option + (self._next_action_id,))
        elif non_string_iterable(option_action):
          result.append((
            option_text, option_icon,
            self._add_ids_to_menu_options(option_action),
            self._next_action_id
            ))
        else:
          print('Unknown item', option_text, option_icon, option_action)
        self._next_action_id += 1
      return result

    def refresh_icon(self):
      # Try and find a custom icon
      hinst = win32gui.GetModuleHandle(None)
      if isinstance(self.icon, str) and os.path.isfile(self.icon):
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        hicon = win32gui.LoadImage(hinst, self.icon, win32con.IMAGE_ICON, 0, 0, icon_flags)
      else:
        hicon = win32gui.LoadIcon(hinst, int(self.icon))

      if self.notify_id:
        message = win32gui.NIM_MODIFY
      else:
        message = win32gui.NIM_ADD
      self.notify_id = (
        self.hwnd, 0,
        win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
        win32con.WM_USER + 20, hicon, self.hover_text
        )
      win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
      self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
      if self.on_quit:
        self.on_quit(self)
      nid = (self.hwnd, 0)
      win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
      win32gui.PostQuitMessage(0)     # Terminate the app.

      # Using the included postgres database?
      if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
        # Check if the database is running. If so, stop it.
        os.environ['PATH'] = os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin') + os.pathsep + os.environ['PATH']
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
          call([
            os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
            "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
            "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
            "-w",   # Wait till it's down
            "stop"
            ],
            stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
            creationflags=CREATE_NO_WINDOW
            )

    def notify(self, hwnd, msg, wparam, lparam):
      if lparam == win32con.WM_LBUTTONDBLCLK:
        self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
      elif lparam == win32con.WM_RBUTTONUP:
        self.show_menu()
      elif lparam == win32con.WM_LBUTTONUP:
        pass
      return True

    def show_menu(self):
      menu = win32gui.CreatePopupMenu()
      self.create_menu(menu, self.menu_options)
      #win32gui.SetMenuDefaultItem(menu, 1000, 0)
      pos = win32gui.GetCursorPos()
      # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
      win32gui.SetForegroundWindow(self.hwnd)
      win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
      win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def create_menu(self, menu, menu_options):
      for option_text, option_icon, option_action, option_id in menu_options[::-1]:
        if option_icon:
          option_icon = self.prep_menu_icon(option_icon)
        if option_id in self.menu_actions_by_id:
          item, extras = win32gui_struct.PackMENUITEMINFO(
            text=option_text, hbmpItem=option_icon, wID=option_id
            )
          win32gui.InsertMenuItem(menu, 0, 1, item)
        else:
          submenu = win32gui.CreatePopupMenu()
          self.create_menu(submenu, option_action)
          item, extras = win32gui_struct.PackMENUITEMINFO(
            text=option_text, hbmpItem=option_icon, hSubMenu=submenu
            )
          win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        # Fill the background.
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        # unclear if brush needs to be feed.  Best clue I can find is:
        # "GetSysColorBrush returns a cached brush instead of allocating a new
        # one." - implies no DeleteObject
        # draw the icon
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(self, hwnd, msg, wparam, lparam):
        self.execute_menu_option(win32gui.LOWORD(wparam))

    def execute_menu_option(self, ident):
      menu_action = self.menu_actions_by_id[ident]
      if menu_action == self.QUIT:
        win32gui.DestroyWindow(self.hwnd)
      else:
        menu_action(self)


def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return not isinstance(obj, str)


# Environment settings (which are used in the Django settings file and need
# to be updated BEFORE importing the settings)
os.environ['DJANGO_SETTINGS_MODULE'] = 'freppledb.settings'
os.environ['FREPPLE_APP'] = os.path.join(sys.path[0], 'custom')
os.environ['FREPPLE_HOME'] = os.path.abspath(os.path.dirname(sys.argv[0]))
os.environ['PYTHONPATH'] = \
  os.path.join(sys.path[0], 'lib', 'library.zip') \
  + os.pathsep + \
  os.path.join(sys.path[0], 'lib') 

# Add the custom directory to the Python path.
sys.path += [ os.environ['FREPPLE_APP'] ]

# Initialize django
import django
django.setup()
from django.conf import settings

# Initialize logging
cx_Logging.StartLogging(
  os.path.join(settings.FREPPLE_LOGDIR, "systemtray.log"),
  level=cx_Logging.INFO,
  maxFiles=1,
  prefix="%t"
  )

# Parse command line
parser = argparse.ArgumentParser(
  description='Runs a web server for frePPLe.'
  )
parser.add_argument('--port', type=int, help="Port number of the server.")
parser.add_argument('--address', help="IP address to listen on.")
options = parser.parse_args()

# Using the included postgres database?
if os.path.exists(os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe')):
  # Check if the database is running. If not, start it.
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
    cx_Logging.Info("Starting the PostgreSQL database")
    call([
      os.path.join(settings.FREPPLE_HOME, '..', 'pgsql', 'bin', 'pg_ctl.exe'),
      "--pgdata", os.path.join(settings.FREPPLE_LOGDIR, 'database'),
      "--log", os.path.join(settings.FREPPLE_LOGDIR, 'database', 'server.log'),
      "-w",   # Wait till it's up
      "start"
      ],
      stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
      creationflags=CREATE_NO_WINDOW
      )

cx_Logging.Info("Starting the web server")

# Synchronize the scenario table with the settings
from freppledb.common.models import Scenario
Scenario.syncWithSettings()

# Import modules
from django.core.handlers.wsgi import WSGIHandler
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.db import DEFAULT_DB_ALIAS

# Determine the port number
port = options.port or settings.PORT

# Determine the IP-address to listen on:
# - either as command line argument
# - either 0.0.0.0 by default, which means all active IPv4 interfaces
address = options.address or '0.0.0.0'

# Redirect all output
logfile = os.path.join(settings.FREPPLE_LOGDIR, 'server.log')
try:
  sys.stdout = open(logfile, 'a', 0)
except:
  print("Can't open log file", logfile)

# Validate the address and port number
try:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind( (address, port) )
  s.close()
except socket.error as e:
  raise Exception("Invalid address '%s' and/or port '%s': %s" % (address, port, e))

# Print a header message
hostname = socket.getfqdn()
msg = ['Starting frePPLe web server on URLs:', ]
if address == '0.0.0.0':
  msg.append(' http://%s:%s/' % (hostname, port))
  for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
    msg.append(' http://%s:%s/' % (ip, port))
else:
  msg.append(' http://%s:%s/' % (address, port))
log(''.join(msg))
log("frePPLe using %s database '%s' as '%s' on '%s:%s'" % (
  settings.DATABASES[DEFAULT_DB_ALIAS].get('ENGINE', '').split('.')[-1],
  settings.DATABASES[DEFAULT_DB_ALIAS].get('NAME', ''),
  settings.DATABASES[DEFAULT_DB_ALIAS].get('USER', ''),
  settings.DATABASES[DEFAULT_DB_ALIAS].get('HOST', ''),
  settings.DATABASES[DEFAULT_DB_ALIAS].get('PORT', '')
  ))


# Run the WSGI server in a new thread
wsgi = RunWSGIServer(address, port)
wsgi.start()

# Run an icon in the system tray
SysTrayIcon(
  1,   # Icon. If integer it is loaded from the executable, otherwise loaded from file.
  'frePPLe server on port %s' % port,   # Text displayed when hovering over the icon
  (    # Menu_options
    ('Open browser', None, OpenBrowser),
    ('Show log directory', None, ShowLogDirectory),
    ('Show configuration directory', None, ShowConfigDirectory),
    ('Open command window', None, OpenCommandWindow),
  ),
  on_quit=on_quit,       # Method called when quitting the application
  default_menu_index=0,  # Double clicking on icon opens this menu option
  window_class_name="frePPLe server"
  )
