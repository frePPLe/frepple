#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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
'''
import os, sys, locale

try:
  DEBUG = 'runserver' in sys.argv
except:
  DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%@mzit!i8b*$zc&6oe$t-q^3wev96=kqj7mq(z&-$)#o^k##+_'

# FrePPLe is tested with the following database backends:
# 'oracle', 'postgresql_psycopg2', 'mysql' and 'sqlite3'.
# ================= START UPDATED BLOCK BY WINDOWS INSTALLER =================
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'frepple',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  'scenario1': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'scenario1',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  'scenario2': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'scenario2',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  'scenario3': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'scenario3',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  }

LANGUAGE_CODE = 'en'
# ================= END UPDATED BLOCK BY WINDOWS INSTALLER =================

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
ALLOWED_HOSTS = [ '*' ]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Brussels'

# Internationalization is switched on by default.
# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
ugettext = lambda s: s
LANGUAGES = (
  ('en', ugettext('English')),
  ('fr', ugettext('French')),
  ('it', ugettext('Italian')),
  ('nl', ugettext('Dutch')),
  ('zh-tw', ugettext('Traditional Chinese')),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%@mzit!i8b*$zc&6oe$t-q^3wev96=kqj7mq(z&-$)#o^k##+_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
   #('django.template.loaders.cached.Loader', (
     'django.template.loaders.filesystem.Loader',
     'django.template.loaders.app_directories.Loader',
   #))
   )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Uncomment for external authentication.
    # The authentication backend RemoteUserBackend also needs to be activated.
    #'django.contrib.auth.middleware.RemoteUserMiddleware',
    'freppledb.common.middleware.LocaleMiddleware',
    'freppledb.common.middleware.DatabaseSelectionMiddleware',
    'django.middleware.common.CommonMiddleware',
)

CURRENCY=("","$")    # Prefix and suffix for currency strings

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'freppledb.input',
    'freppledb.output',
    'freppledb.execute',
    'freppledb.common',
    #'openerp',
)

LOCALE_PATHS = (
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','django')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','auth')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','contenttypes')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','sessions')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','admin')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','messages')),
    os.path.normpath(os.path.join(FREPPLE_APP,'freppledb','locale')),
)

TEMPLATE_DIRS = (
    os.path.normpath(os.path.join(FREPPLE_APP,'freppledb','templates')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'templates')),
)

STATICFILES_DIRS = ()
if os.path.isdir(os.path.normpath(os.path.join(FREPPLE_HOME,'static'))):
  STATICFILES_DIRS += (os.path.normpath(os.path.join(FREPPLE_HOME,'static')),)
if os.path.isdir(os.path.normpath(os.path.join(FREPPLE_HOME,'..','doc','output'))):
  STATICFILES_DIRS += (('doc', os.path.normpath(os.path.join(FREPPLE_HOME,'..','doc','output')),),)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'CRITICAL',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        # A handler to log all SQL queries.
        # The setting "DEBUG" also needs to be set to True higher up in this file.
        #'django.db.backends': {
        #    'handlers': ['console'],
        #    'level': 'DEBUG',
        #    'propagate': False,
        #},
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'freppledb': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

# To use a customized authentication backend.
AUTHENTICATION_BACKENDS = (
    # Uncomment for external authentication.
    # The middleware RemoteUserMiddleware also needs to be activated.
    #"django.contrib.auth.backends.RemoteUserBackend",
    "freppledb.common.auth.EmailBackend",
)

# IP address of the machine you are browsing from. When logging in from this
# machine additional debugging statements can be shown.
INTERNAL_IPS = ( '127.0.0.1', )

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

# The default user interface theme
DEFAULT_THEME = 'sunny'

# The default number of records to pull from the server as a page
DEFAULT_PAGESIZE = 100

# The size of the "name" key field of the database models
NAMESIZE = 60

# The size of the "description" field of the database models
DESCRIPTIONSIZE = 200

# The size of the "category" and "subcategory" fields of the database models
CATEGORYSIZE = 20

# The number of digits for a number in the database models
MAX_DIGITS = 15

# The number of decimal places for a number in the database models
DECIMAL_PLACES = 4

# The maximum allowed length of a comment
COMMENT_MAX_LENGTH = 3000

# Port number for the CherryPy web server
PORT = 8000
