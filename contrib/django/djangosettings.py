# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2015 by frePPLe bvba
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

# ================= START UPDATED BLOCK BY WINDOWS INSTALLER =================
# Make this unique, and don't share it with anybody.
SECRET_KEY = '%@mzit!i8b*$zc&6oev96=RANDOMSTRING'

# FrePPLe only supports the 'postgresql_psycopg2' database.
# Create additional entries in this dictionary to define scenario schemas.

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'frepple',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default.
    'TEST': {
      'NAME': 'test_frepple' # Database name used when running the test suite.
      }
    },
  'scenario1': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'scenario1',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default.
    'TEST': {
      'NAME': 'test_scenario1' # Database name used when running the test suite.
      }
    },
  'scenario2': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'scenario2',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default.
    'TEST': {
      'NAME': 'test_scenario2' # Database name used when running the test suite.
      }
    },
  'scenario3': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'scenario3',
    'USER': 'frepple',
    'PASSWORD': 'frepple',
    'HOST': '',     # Set to empty string for localhost.
    'OPTIONS': {},  # Backend specific configuration parameters.
    'PORT': '',     # Set to empty string for default.
    'TEST': {
      'NAME': 'test_scenario3' # Database name used when running the test suite.
      }
    },
  }

LANGUAGE_CODE = 'en'
# ================= END UPDATED BLOCK BY WINDOWS INSTALLER =================

# If passwords are set in this file they will be used instead of the ones set in the database parameters table
OODO_PASSWORDS = {
  'default': '',
  'scenario1': '',
  'scenario2': '',
  'scenario3': ''
  }

# If passwords are set in this file they will be used instead of the ones set in the database parameters table
OPENBRAVO_PASSWORDS = {
  'default': '',
  'scenario1': '',
  'scenario2': '',
  'scenario3': ''
  }

# Keep each database connection alive for 10 minutes.
CONN_MAX_AGE = 600

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

# A boolean that specifies if datetimes will be timezone-aware by default or not.
# If this is set to True, we will use timezone-aware datetimes internally.
# Otherwise, we use naive datetimes in local time.
USE_TZ = False     # TODO Test with this parameter set to True

# Supported language codes, sorted by language code.
# Language names and codes should match the ones in Django.
# You can see the list supported by Django at:
#    https://github.com/django/django/blob/master/django/conf/global_settings.py
ugettext = lambda s: s
LANGUAGES = (
  ('en', ugettext('English')),
  ('es', ugettext('Spanish')),
  ('fr', ugettext('French')),
  ('it', ugettext('Italian')),
  ('ja', ugettext('Japanese')),
  ('nl', ugettext('Dutch')),
  ('pt', ugettext('Portuguese')),
  ('pt-br', ugettext('Brazilian Portuguese')),
  ('zh-cn', ugettext('Simplified Chinese')),
  ('zh-tw', ugettext('Traditional Chinese')),
)

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
    'freppledb.common.middleware.MultiDBMiddleware',
    'freppledb.common.middleware.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

CURRENCY=("","$")    # Prefix and suffix for currency strings

# Installed applications.
# The order is important: urls, templates and menus of the earlier entries
# take precedence over and override later entries.
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'freppledb.boot',
    'freppledb.odoo',
    'freppledb.openbravo',
    'freppledb.input',
    'freppledb.output',
    'freppledb.execute',
    'freppledb.common',
    'rest_framework',
)

# Custom attribute fields in the database
# After each change of this setting, the following commands MUST be
# executed to create the fields in the database(s).
#   frepplectl makemigrations
#   frepplectl migrate     OR     frepplectl migrate --database DATABASE
#
# The commands will create migration files to keep track of the changes.
# You MUST use the above commands and the generated migration scripts. Manually
# changing the database schema will work in simple cases, but will get you
# in trouble in the long run!
# You'll need write permissions in the folder where these are stored.
#
# See https://docs.djangoproject.com/en/1.8/topics/migrations/ for the
# details on the migration files. For complex changes to the attributes
# an administrator may need to edit, delete or extend these files.
#
# Supported field types are 'string', 'boolean', 'number', 'integer',
# 'date', 'datetime', 'duration' and 'time'.
# Example:
#  ATTRIBUTES = [
#    ('freppledb.input.models.Item', [
#      ('attribute1', ugettext('attribute_1'), 'string'),
#      ('attribute2', ugettext('attribute_2'), 'boolean'),
#      ('attribute3', ugettext('attribute_3'), 'date'),
#      ('attribute4', ugettext('attribute_4'), 'datetime'),
#      ('attribute5', ugettext('attribute_5'), 'number'),
#      ]),
#    ('freppledb.input.models.Operation', [
#      ('attribute1', ugettext('attribute_1'), 'string'),
#      ])
#    ]
ATTRIBUTES = []

REST_FRAMEWORK = {
  # Use Django's standard `django.contrib.auth` permissions,
  # or allow read-only access for unauthenticated users.
  'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.DjangoModelPermissions'
  ],
  'DEFAULT_AUTHENTICATION_CLASSES': (
    'rest_framework.authentication.BasicAuthentication',
    'rest_framework.authentication.SessionAuthentication',
  ),
  'DEFAULT_RENDERER_CLASSES': (
    'rest_framework.renderers.JSONRenderer',
    'freppledb.common.api.renderers.freppleBrowsableAPI',
  )
}

import django.contrib.admindocs
LOCALE_PATHS = (
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','django')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','auth')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','contenttypes')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','sessions')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','admin')),
    os.path.normpath(os.path.join(FREPPLE_HOME,'locale','messages')),
    os.path.normpath(os.path.join(FREPPLE_APP,'freppledb','locale')),
    os.path.normpath(os.path.join(os.path.dirname(django.contrib.admindocs.__file__),'locale')),
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

# Backends for user authentication and authorization.
# FrePPLe currently supports only this custom one.
AUTHENTICATION_BACKENDS = (
    "freppledb.common.auth.MultiDBBackend",
)

# IP address of the machine you are browsing from. When logging in from this
# machine additional debugging statements can be shown.
INTERNAL_IPS = ( '127.0.0.1', )

# Default charset to use for all ``HttpResponse`` objects, if a MIME type isn't
# manually specified.
DEFAULT_CHARSET = 'utf-8'

# Default characterset for writing and reading CSV files.
# FrePPLe versions < 3 used the default encoding of the server as default.
# From version 3 onwards the default is UTF-8.
CSV_CHARSET = 'utf-8' # locale.getdefaultlocale()[1]

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

# Configuration of the default dashboard
DEFAULT_DASHBOARD = [
  {'width':'50%', 'widgets':[
    ("welcome",{}),
    ("resource_queue",{"limit":20}),
    ("purchase_queue",{"limit":20}),
    ("shipping_queue",{"limit":20}),
  ]},
  {'width':'25%', 'widgets':[
    ("recent_actions",{"limit":10}),
    ("recent_comments",{"limit":10}),
    ("execute",{}),
    ("alerts",{}),
    ("late_orders",{"limit":20}),
    ("short_orders",{"limit":20}),
    ("purchase_order_analysis",{"limit":20}),
  ]},
  {'width':'25%', 'widgets':[
    ("news",{}),
    ('resource_utilization',{"limit":5, "medium": 80, "high": 90}),
    ("delivery_performance",{"green": 90, "yellow": 80}),
    ("inventory_by_location",{"limit":5}),
    ("inventory_by_item",{"limit":10}),
  ]},
  ]

# Port number for the CherryPy web server
PORT = 8000
