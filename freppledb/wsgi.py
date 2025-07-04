#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""
Configuration for frePPLe django WSGI web application.
This is used by the different WSGI deployment options:
  - mod_wsgi on apache web server.
    See https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
  - django development server 'frepplectl.py runserver'
"""

import os
import sys

# Assure frePPLe is found in the Python path.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

if "FREPPLE_TEST" not in os.environ:
    from freppledb.execute.management.commands.scheduletasks import scheduler

    scheduler.start()
