# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2015 by frePPLe bv
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

r"""
Main Django configuration file.
"""
import os
import sys
import pathlib

from django.utils.translation import gettext_lazy as _

try:
    DEBUG = "runserver" in sys.argv
except Exception:
    DEBUG = False
DEBUG_JS = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = "%@mzit!i8b*$zc&6oev96=RANDOMSTRING"

# Configuration of the frepple database
MIN_NUMBER_OF_SCENARIOS = 2
MAX_NUMBER_OF_SCENARIOS = 30
DATABASES = {
    "default" if i == 0 else f"scenario{i}": {
        "ENGINE": "freppledb.common.postgresql",
        # Database name
        "NAME": f"{os.environ.get("POSTGRES_DBNAME","frepple")}{i}",
        # Role name when using md5 authentication.
        # Leave as an empty string when using peer or
        # ident authencation.
        "USER": os.environ.get("POSTGRES_USER", "frepple"),
        # Role password when using md5 authentication.
        # Leave as an empty string when using peer or
        # ident authencation.
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "frepple"),
        # When using TCP sockets specify the hostname,
        # the ip4 address or the ip6 address here.
        # Leave as an empty string to use Unix domain
        # socket ("local" lines in pg_hba.conf).
        "HOST": os.environ.get("POSTGRES_HOST", ""),
        # Specify the port number when using a TCP socket.
        "PORT": os.environ.get("POSTGRES_PORT", ""),
        "OPTIONS": {
            "options": "-c lock_timeout=300000"  # Timeout (in milliseconds) to acquire a lock
        },
        "CONN_MAX_AGE": None,
        "CONN_HEALTH_CHECKS": True,
        "TEST": {
            # Database name used when running the test suite.
            "NAME": (f"{os.environ.get("POSTGRES_DBNAME","frepple")}_test{i}"),
            # Port for web service when running the test suite
            "FREPPLE_PORT": f"127.0.0.1:{i+9002}",
        },
        # The FILEUPLOADFOLDER setting is used by the "import data files" task.
        # By default all scenario databases use the same data folder on the server.
        # By configuring this setting you can configure a dedicated data folder for each
        # scenario database.
        "FILEUPLOADFOLDER": os.path.normpath(
            os.path.join(
                FREPPLE_LOGDIR, "data", "default" if i == 0 else f"scenario{i}"
            )
        ),
        # Role name for executing custom reports and processing sql data files.
        # Make sure this role has properly restricted permissions!
        # When left unspecified, SQL statements run with the full read-write
        # permissions of the user specified above. Which can be handy, but is not secure.
        "SQL_ROLE": None,  # "report_role",
        "SECRET_WEBTOKEN_KEY": SECRET_KEY,
        # Port for the frepple web service
        "FREPPLE_PORT": f"127.0.0.1:{i+8002}",
    }
    # Adjust the range to include extra scenarios in the list.
    # When changing this, your apache configuration file also needs a matching adjustment.
    # THE NEXT LINE IS AUTOMATICALLY UPDATED IN SCENARIO MANAGEMENT WIDGET!
    for i in range(3)
}

# Google analytics code to report usage statistics to.
# The value None disables this feature.
GOOGLE_ANALYTICS = None

# Installed applications.
# The order is important: urls, templates and menus of the earlier entries
# take precedence over and override later entries.
#
# IMPORTANT: the apps screen updates this section of the file.
# So, please don't change the layout of this section: just keep a separate
# line for each app.
# ================= START UPDATED BLOCK =================
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "freppledb.boot",
    # Add any project specific apps here
    # "freppledb.odoo",
    # "freppledb.erpconnection",
    "freppledb.wizard",
    "freppledb.input",
    "freppledb.forecast",
    "freppledb.output",
    "freppledb.metrics",
    "freppledb.execute",
    "freppledb.webservice",
    "freppledb.common",
    "django_filters",
    "rest_framework",
    "django.contrib.admin",
    "freppledb.archive",
    # The next two apps allow users to run their own SQL statements on
    # the database, using the SQL_ROLE configured above.
    "freppledb.reportmanager",
    "freppledb.executesql",
    "freppledb.debugreport",
)
# ================= END UPDATED BLOCK =================

# This setting contains a list containing:
#   - names of installable apps.
#   - a Path object pointing to a folder where installable apps are found.
INSTALLABLE_APPS = (
    "freppledb.odoo",
    "freppledb.forecast",
    "freppledb.mlforecast",
    "freppledb.wizard",
    "freppledb.metrics",
    "freppledb.reportmanager",
    "freppledb.executesql",
    "freppledb.debugreport",
    pathlib.Path(os.path.join(FREPPLE_APP, "apps")),
    pathlib.Path(os.path.join(FREPPLE_APP, "freppleapps")),
    pathlib.Path(os.path.join(FREPPLE_HOME, "apps")),
    pathlib.Path(os.path.join(FREPPLE_HOME, "freppleapps")),
    pathlib.Path(os.path.join(FREPPLE_CONFIGDIR, "apps")),
    pathlib.Path(os.path.join(FREPPLE_CONFIGDIR, "freppleapps")),
    pathlib.Path(os.path.join(FREPPLE_LOGDIR, "apps")),
    pathlib.Path(os.path.join(FREPPLE_LOGDIR, "freppleapps")),
)

# Odoo connection parameters in this file they override the ones set in the database parameters table.
# Configuring them here is more secure and eases automated deployments.
ODOO_URL = {i: os.environ.get("ODOO_URL", None) for i in DATABASES.keys()}
ODOO_DB = {i: os.environ.get("ODOO_DB", None) for i in DATABASES.keys()}
ODOO_USER = {i: os.environ.get("ODOO_USER", None) for i in DATABASES.keys()}
ODOO_COMPANY = {i: os.environ.get("ODOO_COMPANY", None) for i in DATABASES.keys()}
ODOO_SINGLECOMPANY = {
    i: os.environ.get("ODOO_SINGLECOMPANY", None) for i in DATABASES.keys()
}
ODOO_PASSWORDS = {i: os.environ.get("ODOO_PASSWORD", None) for i in DATABASES.keys()}
ODOO_LANGUAGE = {i: os.environ.get("ODOO_LANGUAGE", None) for i in DATABASES.keys()}

# If passwords are set in this file they will be used instead of the ones set in the database parameters table
OPENBRAVO_PASSWORDS = {
    i: os.environ.get("OPENBRAVO_PASSWORD", "") for i in DATABASES.keys()
}

if "FREPPLE_TIME_ZONE" in os.environ:
    # Choices can be found here http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    TIME_ZONE = os.environ["FREPPLE_TIME_ZONE"]
    if not TIME_ZONE:
        # A value of None will cause Django to use the same timezone as the operating system.
        TIME_ZONE = None
else:
    # Retrieve the server time zone and use it for the database
    # we need to convert that string into iana/olson format using package tzlocal
    try:
        from tzlocal import get_localzone

        TIME_ZONE = str(get_localzone())
    except Exception:
        TIME_ZONE = "Europe/Brussels"

# Tests have to be done in UTC time zone to guarantuee portable results!
if not hasattr(sys, "argv") or "test" in sys.argv or "FREPPLE_TEST" in os.environ:
    TIME_ZONE = "UTC"

# We provide 3 options for formatting dates (and you always add your own).
#  - month-day-year: US format
#  - day-month-year: European format
#  - year-month-day: international format. This is the default
# As option you can choose to hide the hour, minutes and seconds.
DATE_STYLE = os.environ.get("FREPPLE_DATE_STYLE", "year-month-day")
DATE_STYLE_WITH_HOURS = (
    os.environ.get("FREPPLE_DATE_STYLE_WITH_HOURS", "false").lower() == "true"
)

# Supported language codes, sorted by language code.
# Language names and codes should match the ones in Django.
# You can see the list supported by Django at:
#    https://github.com/django/django/blob/master/django/conf/global_settings.py
LANGUAGES = (
    ("en", _("English")),
    ("fr", _("French")),
    ("de", _("German")),
    ("he", _("Hebrew")),
    ("hr", _("Croatian")),
    ("it", _("Italian")),
    ("ja", _("Japanese")),
    ("nl", _("Dutch")),
    ("pt", _("Portuguese")),
    ("pt-br", _("Brazilian Portuguese")),
    ("ru", _("Russian")),
    ("es", _("Spanish")),
    ("zh-hans", _("Simplified Chinese")),
    ("zh-hant", _("Traditional Chinese")),
    ("uk", _("Ukrainian")),
)

# Default language
LANGUAGE_CODE = LANGUAGES[0][0] or "en"

# The remember-me checkbox on the login page allows to keep a session cookie
# active in your browser. The session will expire after the age configured
# in the setting below (epxressed in seconds).
# Set the value to 0 to force users to log in for every browser session.
SESSION_COOKIE_AGE = 3600 * 24 * 3  # 3 days

# Users are automatically logged out after this period of inactivity
SESSION_LOGOUT_IDLE_TIME = 60 * 24  # minutes

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Uncomment the next line to automatically log on as the admin user,
    # which can be useful for development or for demo models.
    # "freppledb.common.middleware.AutoLoginAsAdminUser",
    "freppledb.common.middleware.MultiDBMiddleware",
    # Uncomment the next line to only allow a list of IP addresses
    # to access the application (see variable ALLOWED_IPs) below
    # "freppledb.common.middleware.AllowedIpMiddleware",
    "freppledb.common.middleware.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
)

# Variable ALLOWED_IPS defines a list of IP adresses allowed to access the application
# AllowedIpMiddleware needs to be active. /24 mask IP address is supported.
# ALLOWED_IPS = [
#     "127.0.0.1",
# ]

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

# Memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "CRITICAL",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        # A handler to log all SQL queries.
        # The setting "DEBUG" also needs to be set to True higher up in this file.
        # "django.db.backends": {
        #     "handlers": ["console"],
        #     "level": "DEBUG",
        #     "propagate": False,
        # },
        "django": {"handlers": ["console"], "level": "INFO"},
        "freppledb": {"handlers": ["console"], "level": "INFO"},
        "freppleapps": {"handlers": ["console"], "level": "INFO"},
    },
}

# Maximum allowed memory size for the planning engine. Only used on Linux!
MAXMEMORYSIZE = None  # limit in MB, minimum around 230, use None for unlimited

# Maximum allowed memory size for the planning engine. Only used on Linux!
MAXCPUTIME = None  # limit in seconds, use None for unlimited

# Maximum allowed storage.
# The storage counts database storage, data files, engine log files, database dump files, plan export files.
MAXSTORAGE = None  # limit in MB, use None for unlimited.

# Max total log files size in MB
# If the limit is reached we automatically delete the oldest log files.
MAXTOTALLOGFILESIZE = 200

# Specify number of objects we are allowed to cache and the number of
# threads we create to write changed objects
CACHE_MAXIMUM = 1000000
CACHE_THREADS = 1

# A list of available user interface themes.
# If multiple themes are configured in this list, the user's can change their
# preferences among the ones listed here.
# If the list contains only a single value, the preferences screen will not
# display users an option to choose the theme.
THEMES = os.environ.get(
    "FREPPLE_THEMES", "earth grass lemon odoo openbravo orange snow strawberry water"
).split()

# A default user-group to which new users are automatically added.
# If this setting is left unspecified or when the group has no assigned permissions,
# then new users will be marked super-users by default.
DEFAULT_USER_GROUP = None

# The default user interface theme
DEFAULT_THEME = os.environ.get("FREPPLE_DEFAULT_THEME", "earth")
if DEFAULT_THEME not in THEMES:
    DEFAULT_THEME = THEMES[0]

# The default number of records to pull from the server as a page
DEFAULT_PAGESIZE = 100

# Configuration of the default dashboard
DEFAULT_DASHBOARD = [
    {
        "rowname": _("default"),
        "cols": [
            {
                "width": 12,
                "widgets": [
                    ("execute", {}),
                    ("executegroup", {}),
                    ("forecast", {"history": 36, "future": 12}),
                    # (
                    #     "analysis_demand_problems",
                    #     {"top": 20, "orderby": "latedemandvalue"},
                    # ),
                    # ("outliers", {"limit": 20}),
                    # ("demand_alerts", {}),
                    ("delivery_performance", {"green": 90, "yellow": 80}),
                    ("forecast_error", {"history": 12}),
                    # ("archived_demand", {"history": 12}),
                    ("purchase_orders", {"fence1": 7, "fence2": 30}),
                    # ("purchase_queue",{"limit":20}),
                    # ("purchase_order_analysis", {"limit": 20}),
                    # ("archived_purchase_order", {"history": 12}),
                    ("inventory_by_location", {"limit": 5}),
                    # ("inventory_by_item", {"limit": 10}),
                    ("manufacturing_orders", {"fence1": 7, "fence2": 30}),
                    # ("resource_queue",{"limit":20}),
                    # ("capacity_alerts", {}),
                    ("resource_utilization", {"limit": 5, "medium": 80, "high": 90}),
                    ("distribution_orders", {"fence1": 7, "fence2": 30}),
                    # ("shipping_queue",{"limit":20}),
                    # ("archived_buffer", {"history": 12}),
                    ("inventory_projection", {"history": 12}),
                ],
            },
        ],
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Configuration of SMTP mail server
EMAIL_USE_TLS = os.environ.get("FREPPLE_EMAIL_USE_TLS", "true").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get(
    "FREPPLE_DEFAULT_FROM_EMAIL", "your_email@domain.com"
)
SERVER_EMAIL = os.environ.get("FREPPLE_SERVER_EMAIL", "your_email@domain.com")
EMAIL_HOST_USER = os.environ.get("FREPPLE_EMAIL_HOST_USER", "your_email@domain.com")
EMAIL_HOST_PASSWORD = os.environ.get("FREPPLE_EMAIL_HOST_PASSWORD", "frePPLeIsTheBest")
EMAIL_HOST = os.environ.get("FREPPLE_EMAIL_HOST", "")
if not EMAIL_HOST:
    EMAIL_HOST = None
EMAIL_PORT = int(os.environ.get("FREPPLE_EMAIL_PORT", 25))
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# ADVANCED HTTP SECURITY SETTING: Clickjacking security http headers
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
# Default: allow content from same domain
CONTENT_SECURITY_POLICY = os.environ.get(
    "FREPPLE_CONTENT_SECURITY_POLICY", "frame-ancestors 'self'"
)
X_FRAME_OPTIONS = os.environ.get("FREPPLE_X_FRAME_OPTIONS", "SAMEORIGIN")
CSRF_COOKIE_SAMESITE = os.environ.get("FREPPLE_CSRF_COOKIE_SAMESITE", "lax")
# Alternative: prohibit embedding in any frame
#   CONTENT_SECURITY_POLICY = "frame-ancestors 'none'"
#   X_FRAME_OPTIONS = "DENY"
# Alternative: allow embedding in a specific domain
#   CONTENT_SECURITY_POLICY = "frame-ancestors 'self' mydomain.com;"
#   X_FRAME_OPTIONS = None
#   CSRF_COOKIE_SAMESITE = "none"

# ADVANCED HTTP SECURITY SETTING: Secure cookies
SESSION_COOKIE_SECURE = (
    os.environ.get("FREPPLE_SESSION_COOKIE_SECURE", "false").lower() == "true"
)
CSRF_COOKIE_SECURE = (
    os.environ.get("FREPPLE_CSRF_COOKIE_SECURE", "false").lower() == "true"
)

# ADVANCED HTTP SECURITY SETTING: When using https and a proxy server in front of frepple.
# CSRF_TRUSTED_ORIGINS = ["https://yourserver", "https://*.yourdomain.com"]
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = os.environ.get("FREPPLE_CSRF_TRUSTED_ORIGINS", "").split()
SECURE_PROXY_SSL_HEADER = os.environ.get("FREPPLE_SECURE_PROXY_SSL_HEADER", "").split()

# Configuration of the ftp/sftp/ftps server where to upload reports
# Note that for SFTP protocol, the host needs to be defined
# in the known_hosts file
# These variables can either be a string if common to all scenarios
# or a dictionary if they vary per scenario (see FTP_FOLDER EXAMPLE)
FTP_PROTOCOL = os.environ.get(
    "FREPPLE_FTP_PROTOCOL", "SFTP"
)  # supported protocols are SFTP, FTPS and FTP (unsecure)
FTP_HOST = os.environ.get("FREPPLE_FTP_HOST", "")
FTP_PORT = int(os.environ.get("FREPPLE_FTP_PORT", 22))
FTP_USER = os.environ.get("FREPPLE_FTP_USER", "")
FTP_PASSWORD = os.environ.get("FREPPLE_FTP_PASSWORD", "")
FTP_FOLDER = {
    "default": None,
    "scenario1": None,
    "scenario2": None,
    "scenario3": None,
}  # folder where the files should be uploaded on the remote server

# Browser to test with selenium
SELENIUM_TESTS = "chrome"
SELENIUM_HEADLESS = True
