#
# Copyright (C) 2007 by Johan De Taeye
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

# frePPLe specific variables  # TODO remove these
import os, os.path, sys
try:
  FREPPLE_HOME = os.environ['FREPPLE_HOME']
except:
  print 'Error: Environment variable FREPPLE_HOME is not defined'
  sys.exit(1)
if 'FREPPLE_APP' in os.environ:
  FREPPLE_APP = os.environ['FREPPLE_APP']
else:
  FREPPLE_APP = os.path.abspath(os.path.join(FREPPLE_HOME,'..','contrib','django'))
FREPPLE_VERSION = '0.8.2.beta'

# Determing whether Django runs as a standalone application or is deployed on a web server
STANDALONE = False
try:
  for i in sys.argv:
    STANDALONE = STANDALONE or i.find('runserver')>=0
except:
  pass

# Django settings for freppledb project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# FrePPLe is tested with the following database backends:
# 'oracle', 'postgresql_psycopg2', 'mysql' and 'sqlite3'.
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
    'USER': '',
    'PASSWORD': '',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  'scenario2': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'scenario2',
    'USER': '',
    'PASSWORD': '',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  'scenario3': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'scenario3',
    'USER': '',
    'PASSWORD': '',
    'HOST': '',     # Set to empty string for localhost. Not used with sqlite3.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default. Not used with sqlite3.
    },
  }

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Europe/Brussels'

# Internationalization is switched on by default.
# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
ugettext = lambda s: s
USE_I18N = True
LANGUAGE_CODE = 'en-us'
LANGUAGES = (
  ('nl', ugettext('Dutch')),
  ('en', ugettext('English')),
  ('it', ugettext('Italian')),
  ('zh-tw', ugettext('Traditional Chinese')),
)
if (STANDALONE):
  LOCALE_PATHS = [ os.path.join(FREPPLE_HOME, 'conf', 'locale'), os.path.join(FREPPLE_APP,'locale'), ]


SITE_ID = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%@mzit!i8b*$zc&6oe$t-q^3wev96=kqj7mq(z&-$)#o^k##+_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'freppledb.common.middleware.LocaleMiddleware',
    'freppledb.common.middleware.DatabaseSelectionMiddleware',
    'django.middleware.common.CommonMiddleware',
)

ROOT_URLCONF = 'freppledb.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    os.path.join(FREPPLE_APP,'freppledb','templates').replace('\\','/'),
    os.path.join(FREPPLE_HOME,'templates').replace('\\','/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'django.contrib.admin',
    'freppledb.input',
    'freppledb.output',
    'freppledb.execute',
    'freppledb.common',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.auth',
    # The debug context keeps track of all sql statements
    # that are executed. Handy for debugging, but a memory killer when
    # huge numbers of queries are executed...
    #'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
)

# Sessions
SESSION_COOKIE_NAME = 'sessionid'         # Cookie name. This can be whatever you want.
SESSION_COOKIE_AGE = 60 * 60 * 24 *  2    # Age of cookie, in seconds: 2 days
SESSION_COOKIE_DOMAIN = None              # A string, or None for standard domain cookie.
SESSION_SAVE_EVERY_REQUEST = False        # Whether to save the session data on every request.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True    # Whether sessions expire when a user closes his browser.

# Mail settings
#DEFAULT_FROM_EMAIL #if not pass from_email to send_mail func.
#EMAIL_HOST #required
#EMAIL_PORT #required
#EMAIL_HOST_USER #if required authentication to host
#EMAIL_HOST_PASSWORD #if required auth.

# To use a customized authentication backend.
AUTHENTICATION_BACKENDS = (
    "freppledb.common.auth.EmailBackend",
)

# To add the user preferences to the standard admin
AUTH_PROFILE_MODULE = 'common.Preferences'

# IP address of the machine you are browsing from. When logging in from this
# machine additional debugging statements can be shown.
INTERNAL_IPS = ( '127.0.0.1', )

# Default charset to use for all ``HttpResponse`` objects, if a MIME type isn't
# manually specified.
# For frePPLe this is important when downloading csv-files. FrePPLe encodes the
# output in this encoding.
DEFAULT_CHARSET = 'utf-8'

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

# Allow overriding the settings
# This is useful for the py2exe distribution: this settings file will be
# compiled and included in a compressed zip-file, and we need to give users a
# way to pass parameters and settings to Django.
if os.path.normcase(os.path.abspath(os.path.dirname(__file__))) != os.path.normcase(FREPPLE_APP) and not 'localsettings' in vars():
  localsettings = True
  try: execfile(os.path.join(FREPPLE_APP,'settings.py'))
  except IOError:
    # The file doesn't exist. No problem - all settings are at defaults.
    pass
  except SyntaxError, e:
    print "Error parsing file %s:\n   %s" % (e.filename, e)
    print "Error at character %d in line %d:\n  %s" % (e.offset, e.lineno, e.text)
  except Exception, e:
    print "Error parsing file %s:\n  %s" % (os.path.join(FREPPLE_APP,'settings.py'),e)

# Extra database parameters
for param in DATABASES.values():
  if param['ENGINE'] == 'django.db.backends.sqlite3':
    # Path to the sqlite3 test database file
    param['TEST_NAME'] = os.path.join(FREPPLE_HOME,'test_%s.sqlite' % param['NAME'])
    # Path to sqlite3 database file
    param['NAME'] = os.path.join(FREPPLE_HOME,'%s.sqlite' % param['NAME'])
    # Extra default settings for SQLITE
    if len(param['OPTIONS']) == 0:
      param['OPTIONS'] = {"timeout": 10, "check_same_thread": False}
  elif param['ENGINE'] == 'django.db.backends.mysql':
    # Extra default settings for MYSQL
    # InnoDB has the proper support for transactions that is required for
    # frePPLe in a production environment.
    if len(param['OPTIONS']) == 0:
      param['OPTIONS'] = {"init_command": "SET storage_engine=INNODB"}
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
