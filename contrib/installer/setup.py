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

from distutils.core import setup
import django
import os
import os.path
import py2exe
import sys

sys.path.append(os.path.join(os.path.split(__file__)[0],'..','django'))
import freppledb

# Add default command lines
if len(sys.argv) == 1:
  sys.argv.append("py2exe")

# Figure out where the django and frepple directories are
djangodirectory = django.__path__[0]
freppledirectory = freppledb.__path__[0]

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
            'rest_framework',
            # Added to package a more complete python library with frePPLe
            'urllib', 'multiprocessing', 'asyncio', 'pip',
            # Added for unicode and internationalization
            'encodings',
           ]
includes = ['html.parser', 'csv', 'poplib', 'imaplib', 'telnetlib', '_sitebuiltins']
excludes = ['django', 'freppledb', 'pydoc', 'cx_Oracle', 'MySQLdb']
ignores = [# Not using docutils
           'docutils', 'docutils.core', 'docutils.nodes', 'docutils.parsers.rst.roles',
           # Not using psycopg (using psycopg2 instead)
           'psycopg',
           # Not using pysqlite2
           'pysqlite2',
           # Not using mod_python
           'mod_python', 'mod_python.util',
           # Not using memcache
           'cmemcache', 'memcache',
           # Not using markdown tags of django
           'markdown', 'textile',
           # Not using WSCGI
           'flup', 'flup.server.fcgi', 'flup.server.fcgi_fork',
           # Not using ImageFields
           'PIL', 'ImageFile',
           # Not needing special datetime handling
           'mx', 'mx.TextTools',
           # Not using yaml serialization
           'yaml',
           # Not storing templates in python eggs
           'pkg_resources', 'resource',
           # Not using the python interactive interpreter
           'IPython',
           # Not sure where django references these...
           'crypt',
           # Not using SSL
           'OpenSSL',
           # Not needed to include frePPLe's own python interface
           'frepple',
           ]

# Add django and frepple.
# Both are added in uncompiled format
from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values(): scheme['data'] = scheme['purelib']
data_files = []
import site
data_files.append( ['custom', [site.__file__,]] )
for srcdir, targetdir in [
   (djangodirectory, os.path.join('custom','django')),
   (freppledirectory, os.path.join('custom','freppledb')),
   ]:
   root_path_length = len(srcdir) + 1
   for dirpath, dirnames, filenames in os.walk(os.path.join(srcdir)):
     # Ignore dirnames that start with '.'
     for i, dirname in enumerate(dirnames):
       if dirname.startswith('.') or dirname == '__pycache__':
         del dirnames[i]
     # Append data files for this subdirectory
     data_files.append([
       os.path.join(targetdir, dirpath[root_path_length:]),
       [os.path.join(dirpath, f) for f in filenames if not f.endswith(".pyc") and not f.endswith(".pyo")]
       ])

# Run the py2exe program
setup(
    # Options
    options = {"py2exe": {
          # create a compressed zip archive
          "compressed": 1,
          # optimize the bytecode
          "optimize": 2,
          # Next option is commented out: Gives a cleaner install, but doesn't work for sqlite
          # bundle python modules in the zip file as well.  TODO test if it works for postgresql
          #"bundle_files": 2,
          # content of the packaged python
          "packages": packages,
          "excludes": excludes,
          "includes": includes,
          "ignores": ignores,
          }},
    data_files = data_files,
    # Attributes
    version = freppledb.VERSION,
    description = "frePPLe web application",
    name = "frePPLe",
    author = "frepple.com",
    url = "http://frepple.com",
    # Target to build a Windows service
    service = [{
       "modules":["freppleservice"],
       "icon_resources": [(1, os.path.join("..","..","src","frepple.ico"))],
       "cmdline_style": 'pywin32',
       }],
    # Target to build the system tray application
    windows = [{
       "script": "freppleserver.py",
       "icon_resources": [(1, os.path.join("..","..","src","frepple.ico"))],
       }],
    # Target to build a console application
    console = [{
       "script": "frepplectl.py",
       "icon_resources": [(1, os.path.join("..","..","src","frepple.ico"))],
       }],
    # Name of the zip file with the bytecode of the Python library.
    # This zip file with the name mentioned below is automatically included
    # in the Python search path (while the default output file "library.zip"
    # isn't)
    zipfile = "python%d%d.zip" % (sys.version_info[0], sys.version_info[1])
    )
