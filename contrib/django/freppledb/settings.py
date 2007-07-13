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
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net


# Frepple specific variables
import os, os.path, re, sys
FREPPLE_HOME = os.environ['FREPPLE_HOME']
FREPPLE_APP = os.path.normpath(os.path.join(FREPPLE_HOME,'..','contrib','django','freppledb'))
FREPPLE_VERSION = '0.3.0-beta'

# Determing whether Django runs as a standalone application or is deployed
# on a web server
STANDALONE = False
try:
  for i in sys.argv:
    STANDALONE = STANDALONE or (re.match(r'.*(runserver|runserver\.exe)$', i) != None)
except:
  pass

# Django settings for freppledb project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Django supports the following database engines: 'postgresql_psycopg2', 'postgresql',
# 'mysql', 'sqlite3' or 'ado_mssql'.
# Frepple is supports only 'postgresql_psycopg2', 'mysql' and 'sqlite3'
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'frepple'           # Database name
DATABASE_USER = 'frepple'             # Not used with sqlite3.
DATABASE_PASSWORD = 'frepple'         # Not used with sqlite3.
DATABASE_HOST = ''                    # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''                    # Set to empty string for default. Not used with sqlite3.

if DATABASE_ENGINE == 'sqlite3':
  # extra settings for SQLITE
  DATABASE_NAME = os.path.join(FREPPLE_HOME,'%s.sqlite' % DATABASE_NAME)  # Path to sqlite3 database file
  DATABASE_OPTIONS = {"timeout": 10, "check_same_thread": False}
elif DATABASE_ENGINE == 'mysql':
  # extra settings for MYSQL
  DATABASE_OPTIONS = {"init_command": "SET storage_engine=INNODB"}

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Europe/Brussels'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%@mzit!i8b*$zc&6oe$t-q^3wev96=kqj7mq(z&-$)#o^k##+_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'freppledb.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    os.path.join(FREPPLE_APP,'templates').replace('\\','/'),
    FREPPLE_HOME.replace('\\','/'),
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
    'freppledb.user',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.auth',
    # The debug context keeps track of all sql statements
    # that are executed. Handy for debugging, but a memory killer when
    # huge numbers of queries are executed...
    #'django.core.context_processors.debug',
    #'django.core.context_processors.i18n',
)

# Disable internationalization
USE_I18N = False

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

CACHE_BACKEND = 'locmem:///'

# Directory from which we allow server include
ALLOWED_INCLUDE_ROOTS = (FREPPLE_HOME)

# To use a customized authentication backend.
AUTHENTICATION_BACKENDS = (
    "freppledb.user.auth.EmailBackend",
)

# To add the user preferences to the standard admin
AUTH_PROFILE_MODULE = 'user.Preferences'

# IP address of the machine you are browsing from. When logging in from this
# machine additional debugging statements can be shown.
INTERNAL_IPS = ( '192.168.3.1' )

