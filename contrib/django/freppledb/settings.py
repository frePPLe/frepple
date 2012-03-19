#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
Main Django configuration file.
'''
import os, os.path, sys, locale

# frePPLe specific variables  # TODO remove these
try:
  FREPPLE_HOME = os.environ['FREPPLE_HOME']
except:
  print 'Error: Environment variable FREPPLE_HOME is not defined'
  sys.exit(1)
if 'FREPPLE_APP' in os.environ:
  FREPPLE_APP = os.environ['FREPPLE_APP']
else:
  FREPPLE_APP = os.path.abspath(os.path.join(FREPPLE_HOME,'..','contrib','django'))
# sys.path.append(os.path.abspath(os.path.join(FREPPLE_HOME,'..','contrib','openerp')))

# Django settings for freppledb project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

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

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
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
    #)),
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

WSGI_APPLICATION = 'freppledb.wsgi.application'
ROOT_URLCONF = 'freppledb.urls'
STATIC_ROOT = 'static'
STATIC_URL = '/static/'
USE_L10N=True        # Represent data in the local format
USE_I18N=True        # Use translated strings
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
    #'freppledb.openerp',
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

STATICFILES_DIRS = (
  ('doc',os.path.normpath(os.path.join(FREPPLE_HOME,'..','doc'))),
  )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'django.core.context_processors.static',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
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

# Sessions
SESSION_COOKIE_NAME = 'sessionid'         # Cookie name. This can be whatever you want.
SESSION_COOKIE_AGE = 60 * 60 * 24 *  2    # Age of cookie, in seconds: 2 days
SESSION_COOKIE_DOMAIN = None              # A string, or None for standard domain cookie.
SESSION_SAVE_EVERY_REQUEST = True         # Whether to save the session data on every request. 
                                          # Needs to be True to have the breadcrumbs working correctly!
SESSION_EXPIRE_AT_BROWSER_CLOSE = True    # Whether sessions expire when a user closes his browser.

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.SessionStorage'

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

# To add the user preferences to the standard admin
AUTH_PROFILE_MODULE = 'common.Preferences'

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

# A list of available user interface themes.
# The current selection is nothing but the pack of standard themes of JQuery UI.
# Check out http://jqueryui.com/themeroller/ to roll your own theme.
THEMES = [ (i,i) for i in (
  'base', 'black-tie', 'blitzer', 'cupertino', 'dark-hive', 'dot-luv', 'eggplant',
  'excite-bike', 'flick', 'hot-sneaks', 'humanity', 'le-frog', 'mint-choc',
  'overcast', 'pepper-grinder', 'redmond', 'smoothness', 'south-street', 'start',
  'sunny', 'swanky-purse', 'trontastic', 'ui-darkness', 'ui-lightness', 'vader'
  )] 

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

# Port number for the CherryPy web server
PORT = 8000

# Extra database parameters
for param in DATABASES.values():
  if param['ENGINE'] == 'django.db.backends.sqlite3':
    # Path to the sqlite3 test database file
    param['TEST_NAME'] = os.path.join(FREPPLE_APP,'test_%s.sqlite' % param['NAME'])
    # Path to sqlite3 database file
    param['NAME'] = os.path.join(FREPPLE_APP,'%s.sqlite' % param['NAME'])
    # Extra default settings for SQLITE
    if len(param['OPTIONS']) == 0:
      param['OPTIONS'] = {"timeout": 10, "check_same_thread": False}
  elif param['ENGINE'] == 'django.db.backends.mysql':
    # Extra default settings for MYSQL
    # InnoDB has the proper support for transactions that is required for
    # frePPLe in a production environment.
    if len(param['OPTIONS']) == 0:
      param['OPTIONS'] = {"init_command": "SET storage_engine=INNODB, SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"}
    param['TEST_NAME'] = 'test_%s' % param['NAME']
  elif param['ENGINE'] == 'django.db.backends.oracle':
    param['TEST_NAME'] = param['NAME']
    param['TEST_USER'] = 'test_%s' % param['USER']
    param['TEST_PASSWD'] = param['PASSWORD']
  elif param['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
    param['TEST_NAME'] = 'test_%s' % param['NAME']
  else:
    print 'Error: Unsupported database engine %s' % param['ENGINE']
    sys.exit(1)
