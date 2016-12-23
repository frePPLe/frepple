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
    'USER': 'frepple',     # Role name when using md5 authentication.
                           # Leave as an empty string when using peer or
                           # ident authencation.
    'PASSWORD': 'frepple', # Role password when using md5 authentication.
                           # Leave as an empty string when using peer or
                           # ident authencation.
    'HOST': '',            # When using TCP sockets specify the hostname,
                           # the ip4 address or the ip6 address here.
                           # Leave as an empty string to use Unix domain
                           # socket ("local" lines in pg_hba.conf).
    'PORT': '',            # Leave to empty string when using Unix domain sockets.
                           # Specify the port number when using a TCP socket.
    'OPTIONS': {},         # Backend specific configuration parameters.
    'TEST': {
      'NAME': 'test_frepple' # Database name used when running the test suite.
      },
    'FILEUPLOADFOLDER': os.path.normpath(os.path.join(FREPPLE_LOGDIR,'data','default')),
    'SECRET_WEBTOKEN_KEY': SECRET_KEY,
    },
   'scenario1': {
     'ENGINE': 'django.db.backends.postgresql_psycopg2',
     'NAME': 'scenario1_4.0',
     'USER': 'frepple',     # Role name when using md5 authentication.
                            # Leave as an empty string when using peer or
                            # ident authencation.
     'PASSWORD': 'frepple', # Role password when using md5 authentication.
                            # Leave as an empty string when using peer or
                            # ident authencation.
     'HOST': '',            # When using TCP sockets specify the hostname,
                            # the ip4 address or the ip6 address here.
                            # Leave as an empty string to use Unix domain
                            # socket ("local" lines in pg_hba.conf).
     'PORT': '',            # Leave to empty string when using Unix domain sockets.
                            # Specify the port number when using a TCP socket.
     'OPTIONS': {},         # Backend specific configuration parameters.
     'TEST': {
       'NAME': 'test_scenario1' # Database name used when running the test suite.
       },
     'FILEUPLOADFOLDER': os.path.normpath(os.path.join(FREPPLE_LOGDIR,'data','scenario1')),
     'SECRET_WEBTOKEN_KEY': SECRET_KEY,
     },
   'scenario2': {
     'ENGINE': 'django.db.backends.postgresql_psycopg2',
     'NAME': 'scenario2_4.0',
     'USER': 'frepple',     # Role name when using md5 authentication.
                            # Leave as an empty string when using peer or
                            # ident authencation.
     'PASSWORD': 'frepple', # Role password when using md5 authentication.
                            # Leave as an empty string when using peer or
                            # ident authencation.
     'HOST': '',            # When using TCP sockets specify the hostname,
                            # the ip4 address or the ip6 address here.
                            # Leave as an empty string to use Unix domain
                            # socket ("local" lines in pg_hba.conf).
     'PORT': '',            # Leave to empty string when using Unix domain sockets.
                            # Specify the port number when using a TCP socket.
     'OPTIONS': {},         # Backend specific configuration parameters.
     'TEST': {
       'NAME': 'test_scenario2' # Database name used when running the test suite.
       },
     'FILEUPLOADFOLDER': os.path.normpath(os.path.join(FREPPLE_LOGDIR,'data','scenario2')),
     'SECRET_WEBTOKEN_KEY': SECRET_KEY,
     },
   'scenario3': {
     'ENGINE': 'django.db.backends.postgresql_psycopg2',
     'NAME': 'scenario3_4.0',
     'USER': 'frepple',     # Role name when using md5 authentication.
                            # Leave as an empty string when using peer or
                            # ident authencation.
     'PASSWORD': 'frepple', # Role password when using md5 authentication.
                            # Leave as an empty string when using peer or
                            # ident authencation.
     'HOST': '',            # When using TCP sockets specify the hostname,
                            # the ip4 address or the ip6 address here.
                            # Leave as an empty string to use Unix domain
                            # socket ("local" lines in pg_hba.conf).
     'PORT': '',            # Leave to empty string when using Unix domain sockets.
                            # Specify the port number when using a TCP socket.
     'OPTIONS': {},         # Backend specific configuration parameters.
     'TEST': {
       'NAME': 'test_scenario3' # Database name used when running the test suite.
       },
     'FILEUPLOADFOLDER': os.path.normpath(os.path.join(FREPPLE_LOGDIR,'data','scenario3')),
     'SECRET_WEBTOKEN_KEY': SECRET_KEY,
     },
  }

LANGUAGE_CODE = 'en'
# ================= END UPDATED BLOCK BY WINDOWS INSTALLER =================

# If passwords are set in this file they will be used instead of the ones set in the database parameters table
ODOO_PASSWORDS = {
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
)

# Prefix and suffix for currency strings
CURRENCY=("", "$")           # Dollar symbol
#CURRENCY=("", u"\u20AC")    # Euro symbol

# Installed applications.
# The order is important: urls, templates and menus of the earlier entries
# take precedence over and override later entries.
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'freppledb.boot',
    # Add any project specific apps here
    #'freppledb.odoo',
    #'freppledb.openbravo',
    'freppledb.input',
    'freppledb.output',
    'freppledb.execute',
    'freppledb.common',
    'rest_framework',
    'django_admin_bootstrapped',
    'django.contrib.admin',
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

TEMPLATES_TODO = [ #to be used in the future, now interferes with middleware
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            #os.path.normpath(os.path.join(FREPPLE_HOME,'templates')),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

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
            'class':'logging.NullHandler',
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

# A list of available user interface themes.
# If multiple themes are configured in this list, the user's can change their
# preferences among the ones listed here.
# If the list contains only a single value, the preferences screen will not
# display users an option to choose the theme.
THEMES = [
  'earth', 'grass', 'lemon', 'odoo', 'openbravo', 'orange', 'snow', 'strawberry', 'water'
  ]

# A default user-group to which new users are automatically added
DEFAULT_USER_GROUP = None

# The default user interface theme
DEFAULT_THEME = 'earth'

# The default number of records to pull from the server as a page
DEFAULT_PAGESIZE = 100

# Configuration of the default dashboard
DEFAULT_DASHBOARD = [
  { 'rowname': 'Welcome', 'cols': [
    {'width':8, 'widgets':[
      ("welcome",{}),
      ("news",{}),
    ]},
    {'width':4, 'widgets':[
      #("execute",{}),
      ("recent_comments",{"limit":10}),
      ("recent_actions",{"limit":10}),
      ("wizard",{}),
    ]},
  ]},
  { 'rowname': 'sales', 'cols': [
    {'width':9, 'widgets':[
      ("late_orders",{"limit":20}),
      ("short_orders",{"limit":20}),
    ]},
    {'width':3, 'widgets':[
      ("demand_alerts", {}),
      ("delivery_performance",{"green": 90, "yellow": 80}),
    ]},
  ]},
  { 'rowname': 'purchasing', 'cols': [
    {'width':9, 'widgets':[
      ("purchase_orders",{"fence1": 7, "fence2": 30}),
      #("purchase_queue",{"limit":20}),
      ("purchase_order_analysis",{"limit":20}),
    ]},
    {'width':3, 'widgets':[
      ("inventory_by_location",{"limit":5}),
      ("inventory_by_item",{"limit":10}),
    ]},
  ]},
  { 'rowname': 'distribution', 'cols': [
    {'width':12, 'widgets':[
      ("distribution_orders",{"fence1":7, "fence2": 30}),
      #("shipping_queue",{"limit":20}),
    ]},
  ]},
  { 'rowname': 'manufacturing', 'cols': [
    {'width':9, 'widgets':[
      ("manufacturing_orders",{"fence1":7, "fence2": 30}),
      #("resource_queue",{"limit":20}),
    ]},
    {'width':3, 'widgets':[
      ('capacity_alerts',{}),
      ('resource_utilization',{"limit":5, "medium": 80, "high": 90}),
    ]},
  ]},
]

# Port number for the CherryPy web server
PORT = 8000
