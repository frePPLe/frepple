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

"""
Configuration for frePPLe django WSGI web application.
This is used by the different WSGI deployment options:
  - mod_wsgi on apache web server.
    See https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
  - django development server 'frepplectl.py runserver'
  - cherrypy server 'frepplectl.py runswebserver
"""

import os
import sys

# Assure frePPLe is found in the Python path.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "freppledb.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
