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

r'''
Main Django configuration file.

It is recommended not to edit this file!
Instead put all your settings in the file FREPPLE_CONFDIR/djangosettings.py.

'''
import locale
import os
import sys
import types
import freppledb

# FREPPLE_APP directory
if 'FREPPLE_APP' in os.environ:
  FREPPLE_APP = os.environ['FREPPLE_APP']
else:
  FREPPLE_APP = os.path.abspath(os.path.join(os.path.dirname(freppledb.__file__), '..'))

# FREPPLE_HOME directory
if 'FREPPLE_HOME' in os.environ:
  FREPPLE_HOME = os.environ['FREPPLE_HOME']
elif os.sep == '/' and os.path.isfile('/usr/share/frepple/frepple.xsd'):
  # Linux installation layout with prefix /usr
  FREPPLE_HOME = '/usr/share/frepple'
elif os.sep == '/' and os.path.isfile('/usr/local/share/frepple/frepple.xsd'):
  # Linux installation layout with prefix /usr/local
  FREPPLE_HOME = '/usr/local/share/frepple'
elif os.path.isfile(os.path.abspath(os.path.join(FREPPLE_APP, '..', 'frepple.xsd'))):
  # Py2exe layout
  FREPPLE_HOME = os.path.abspath(os.path.join(FREPPLE_APP, '..'))
elif os.path.isfile(os.path.abspath(os.path.join(FREPPLE_APP, '..', '..', 'bin', 'frepple.xsd'))):
  # Development layout
  FREPPLE_HOME = os.path.abspath(os.path.join(FREPPLE_APP, '..', '..', 'bin'))
else:
  print("Error: Can't locate frepple.xsd")
  sys.exit(1)
os.environ['FREPPLE_HOME'] = FREPPLE_HOME

# FREPPLE_LOGDIR directory
if 'FREPPLE_LOGDIR' in os.environ:
  FREPPLE_LOGDIR = os.environ['FREPPLE_LOGDIR']
elif os.sep == '/' and os.access('/var/log/frepple', os.W_OK):
  # Linux installation layout
  FREPPLE_LOGDIR = '/var/log/frepple'
else:
  FREPPLE_LOGDIR = FREPPLE_APP

# FREPPLE_CONFIGDIR directory
if 'FREPPLE_CONFIGDIR' in os.environ:
  FREPPLE_CONFIGDIR = os.environ['FREPPLE_CONFIGDIR']
elif os.sep == '/' and os.path.isfile('/etc/frepple/djangosettings.py'):
  # Linux installation layout
  FREPPLE_CONFIGDIR = '/etc/frepple'
else:
  FREPPLE_CONFIGDIR = FREPPLE_APP

try:
  DEBUG = 'runserver' in sys.argv
except:
  DEBUG = False

# A list of strings representing the host/domain names the application can serve.
# This is a security measure to prevent an attacker from poisoning caches and
# password reset emails with links to malicious hosts by submitting requests
# with a fake HTTP Host header, which is possible even under many seemingly-safe
# webserver configurations.
# Values in this list can be fully qualified names (e.g. 'www.example.com'),
# in which case they will be matched against the request's Host header exactly
# (case-insensitive, not including port).
# A value beginning with a period can be used as a subdomain wildcard: '.example.com'
# will match example.com, www.example.com, and any other subdomain of example.com.
# A value of '*' will match anything, effectively disabling this feature.
# This option is only active when DEBUG = false.
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Brussels'

# Supported language codes, sorted by language code.
# Language names and codes should match the ones in Django.
# You can see the list supported by Django at:
#    https://github.com/django/django/blob/master/django/conf/global_settings.py
ugettext = lambda s: s
LANGUAGES = (
  # Translators: Translation included with Django
  ('en', ugettext('English')),
  # Translators: Translation included with Django
  ('fr', ugettext('French')),
  # Translators: Translation included with Django
  ('it', ugettext('Italian')),
  # Translators: Translation included with Django
  ('jp', ugettext('Japanese')),
  # Translators: Translation included with Django
  ('nl', ugettext('Dutch')),
  # Translators: Translation included with Django
  ('pt', ugettext('Portuguese')),
  # Translators: Translation included with Django
  ('pt-br', ugettext('Brazilian Portuguese')),
  # Translators: Translation included with Django
  ('zh-cn', ugettext('Simplified Chinese')),
  # Translators: Translation included with Django
  ('zh-tw', ugettext('Traditional Chinese')),
)

# The default redirects URLs not ending with a slash.
# This causes trouble in combination with the DatabaseSelectionMiddleware.
# We prefer not to redirect and report this as an incorrect URL.
APPEND_SLASH = False

WSGI_APPLICATION = 'freppledb.wsgi.application'
ROOT_URLCONF = 'freppledb.urls'
if os.sep == '/' and os.path.isdir('/usr/share/frepple/frepple.xsd'):
  # Standard Linux installation
  STATIC_ROOT = '/usr/share/frepple/static'
else:
  # All other layout types
  STATIC_ROOT = os.path.normpath(os.path.join(FREPPLE_APP, 'static'))
STATIC_URL = '/static/'
USE_L10N = True        # Represent data in the local format
USE_I18N = True        # Use translated strings

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.core.context_processors.static',
)

# Sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_NAME = 'sessionid'         # Cookie name. This can be whatever you want.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 2     # Age of cookie, in seconds: 2 days
SESSION_COOKIE_DOMAIN = None              # A string, or None for standard domain cookie.
SESSION_SAVE_EVERY_REQUEST = True         # Whether to save the session data on every request.
                                          # Needs to be True to have the breadcrumbs working correctly!
SESSION_EXPIRE_AT_BROWSER_CLOSE = True    # Whether sessions expire when a user closes his browser.

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.SessionStorage'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Mail settings
#DEFAULT_FROM_EMAIL #if not pass from_email to send_mail func.
#EMAIL_HOST #required
#EMAIL_PORT #required
#EMAIL_HOST_USER #if required authentication to host
#EMAIL_HOST_PASSWORD #if required auth.

# To use a customized authentication backend.
AUTHENTICATION_BACKENDS = (
    # Uncomment for external authentication.
    # The middleware RemoteUserMiddleware also needs to be activated.
    #"django.contrib.auth.backends.RemoteUserBackend",
    "freppledb.common.auth.EmailBackend",
)

# Custom user model
AUTH_USER_MODEL = 'common.User'

# IP address of the machine you are browsing from. When logging in from this
# machine additional debugging statements can be shown.
INTERNAL_IPS = ('127.0.0.1',)

# Default charset to use for all ``HttpResponse`` objects, if a MIME type isn't
# manually specified.
DEFAULT_CHARSET = 'utf-8'

# Default characterset for writing and reading CSV files.
# We are assuming here that the default encoding of clients is the same as the server.
# If the server is on Linux and the clients are using Windows, this guess will not be good.
# For Windows clients you should set this to the encoding that is better suited for Excel or
# other office tools.
#    Windows - western europe -> 'cp1252'
CSV_CHARSET = locale.getdefaultlocale()[1]

# A list of available user interface themes.
# If multiple themes are configured in this list, the user's can change their
# preferences among the ones listed here.
# If the list contains only a single value, the preferences screen will not
# display users an option to choose the theme.
THEMES = [
  'earth', 'grass', 'lemon', 'snow', 'strawberry', 'water'
  ]

# A default user-group to which new users are automatically added
DEFAULT_USER_GROUP = None

# The default user interface theme
DEFAULT_THEME = 'grass'

# The default number of records to pull from the server as a page
DEFAULT_PAGESIZE = 100

# Port number for the CherryPy web server
PORT = 8000

# Override any of the above settings from a separate file
if os.access(os.path.join(FREPPLE_CONFIGDIR, 'djangosettings.py'), os.R_OK):
  with open(os.path.join(FREPPLE_CONFIGDIR, 'djangosettings.py')) as mysettingfile:
    exec(mysettingfile.read(), globals())
  if DEBUG:
    # Add a dummy module to sys.modules to make the development server
    # autoreload when the configuration file changes.
    module = types.ModuleType('djangosettings')
    module.__file__ = os.path.join(FREPPLE_CONFIGDIR, 'djangosettings.py')
    sys.modules['djangosettings'] = module

# Some Django settings we don't like to be overriden
TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS
