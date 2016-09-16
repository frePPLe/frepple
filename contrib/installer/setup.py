#!/usr/bin/env python3
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

import cx_Freeze
import os
import os.path
import sys

sys.path.append(os.path.join(os.path.split(__file__)[0],'..','django'))

# Add default command lines
if len(sys.argv) == 1:
  sys.argv.append("py2exe")

# Define what is to be included and excluded
packages = [# Required for django standalone deployment
            'logging', 'email', 'cherrypy.wsgiserver', 'sqlite3',
            # Added for PostgreSQL
            'psycopg2',
            # Added to be able to connect to SQL Server
            'adodbapi',
            # Required for reading and writing spreadsheets
            'openpyxl',
            # Required for REST API
            'rest_framework_bulk', 'rest_framework_filters', 'markdown',
            # Added to package a more complete python library with frePPLe
            'urllib', 'multiprocessing', 'asyncio', 'pip', 'html.parser', 'csv',
            'poplib', 'imaplib', 'telnetlib',
            # Added for unicode and internationalization
            'encodings',
            # Added for cx_freeze binaries
            'cx_Logging', 'jwt'
           ]
excludes = ['django', 'freppledb', 'pydoc', 'cx_Oracle', 'MySQLdb', 'rest_framework', 'tkinter']

from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
  scheme['data'] = scheme['purelib']

# Add all modules that need to be added in uncompiled format
import django
import freppledb
import django_admin_bootstrapped
import bootstrap3
import rest_framework
from distutils.sysconfig import get_python_lib
data_files = [
  ('freppleservice.py', 'freppleservice.py'),
  (os.path.join(get_python_lib(), 'win32', 'lib', 'pywintypes.py'), 'pywintypes.py'),
  (os.path.join(get_python_lib(), 'pythoncom.py'), 'pythoncom.py')
  ]
for mod in [django, freppledb, django_admin_bootstrapped, bootstrap3, rest_framework]:
   srcdir = mod.__path__[0]
   targetdir = os.path.join('custom', mod.__name__)
   root_path_length = len(srcdir) + 1
   for dirpath, dirnames, filenames in os.walk(os.path.join(srcdir)):
     # Ignore dirnames that start with '.'
     for i, dirname in enumerate(dirnames):
       if dirname.startswith('.') or dirname == '__pycache__':
         del dirnames[i]
     # Append data files for this subdirectory
     for f in filenames:
       if not f.endswith(".pyc") and not f.endswith(".pyo"):
         data_files.append((
           os.path.join(dirpath, f),
           os.path.join(targetdir, dirpath[root_path_length:], f),
           ))

# Run the cx_Freeze program
cx_Freeze.setup(
  version = freppledb.VERSION.replace(".beta", ".0"),
  description = "frePPLe web application",
  name = "frePPLe",
  author = "frepple.com",
  url = "https://frepple.com",
  options = {
    "install_exe": {
      "install_dir": 'dist'
      },
    "build_exe": {
      "silent": True,
      "optimize": 2,
      "packages": packages,
      "excludes": excludes,
      "include_files": data_files,
      "include_msvcr": True,
      },
    },
  executables = [
    # A console application
    cx_Freeze.Executable(
       'frepplectl.py',
       base='Console',
       icon=os.path.join("..","..","src","frepple.ico")
       ),
    # A Windows service
    cx_Freeze.Executable(
      'freppleservice.py',
      base='Win32Service',
      icon=os.path.join("..","..","src","frepple.ico")
      ),
    # A system tray application
    cx_Freeze.Executable(
      'freppleserver.py',
      base='Win32GUI',
      icon=os.path.join("..","..","src","frepple.ico")
      )
    ]
  )
