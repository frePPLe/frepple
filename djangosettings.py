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

import os
import sys
import pathlib

from django.utils.translation import gettext_lazy as _

try:
    DEBUG = "runserver" in sys.argv
except Exception:
    DEBUG = False
# Set to True to load the unminified javascript sources.
# When enabled, the build also skips the minification of the javascript files.
DEBUG_JS = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = "%@mzit!i8b*$zc&6oev96=RANDOMSTRING"

# Make this unique, and don't share it with anybody.
SECRET_WEBTOKEN_KEY = SECRET_KEY

# When using TCP sockets specify the hostname, the ip4 or ip6 addresshere.
# Leave as an empty string to use Unix domain socket ("local" lines in pg_hba.conf).
POSTGRES_HOST = os.environ.get("POSTGRES_HOST") or "localhost"

# Specify the port number when using a TCP socket. Leave empty when using a local unix socket.
POSTGRES_PORT = os.environ.get("POSTGRES_PORT") or ""
POSTGRES_DB_PREFIX = (
    os.environ.get("POSTGRES_DB_PREFIX")
    or os.environ.get("POSTGRES_DBNAME")
    or "frepple"
)

# Role name when using md5 authentication. Leave as an empty string when using peer or ident authencation.
POSTGRES_USER = os.environ.get("POSTGRES_USER") or "frepple"

# Role password when using md5 authentication. Leave as an empty string when using peer or ident authencation.
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or "frepple"

# Role name for executing custom reports and processing sql data files.
# Make sure this role has properly restricted permissions!
# When left unspecified, SQL statements run with the full read-write
# permissions of the user specified above. Which can be handy, but is not secure.
POSTGRES_REPORTING_USER = os.environ.get("POSTGRES_REPORTING_USER") or "report_role"

APPS = (
    {"name": "daphne", "status": "required"},
    {"name": "django.contrib.auth", "status": "required"},
    {"name": "django.contrib.contenttypes", "status": "required"},
    {"name": "django.contrib.messages", "status": "required"},
    {"name": "django.contrib.staticfiles", "status": "required"},
    {"name": "freppledb.boot", "status": "required"},
    # {"path": pathlib.Path(os.path.join(FREPPLE_APP, "apps"))},
    {"name": "freppledb.odoo", "status": "optional"},
    # {"name": "freppledb.erpconnection", "status": "optional"},
    {"name": "freppledb.wizard", "status": "optional_and_default"},
    {"name": "freppledb.input", "status": "required"},
    {"name": "freppledb.forecast", "status": "optional_and_default"},
    {"name": "freppledb.output", "status": "required"},
    {"name": "freppledb.metrics", "status": "optional_and_default"},
    {"name": "freppledb.execute", "status": "required"},
    {"name": "freppledb.webservice", "status": "required"},
    {"name": "freppledb.common", "status": "required"},
    {"name": "django_filters", "status": "required"},
    {"name": "rest_framework", "status": "required"},
    {"name": "django.contrib.admin", "status": "required"},
    {"name": "freppledb.archive", "status": "required"},
    {"name": "freppledb.reportmanager", "status": "optional_and_default"},
    {"name": "freppledb.executesql", "status": "optional"},
)

# Read database configurable settings
globals().update(
    readDatabaseParameters(
        APPS,
        database=f"{POSTGRES_DB_PREFIX}0",
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
)

MIN_NUMBER_OF_SCENARIOS = 2
MAX_NUMBER_OF_SCENARIOS = 30
SCENARIOS = max(MIN_NUMBER_OF_SCENARIOS, min(SCENARIOS, MAX_NUMBER_OF_SCENARIOS))

# Google analytics code to report usage statistics to.
# The value None disables this feature.
GOOGLE_ANALYTICS = None

# Odoo connection parameters in this file they override the ones set in the database parameters table.
# Configuring them here is more secure and eases automated deployments.
ODOO_URL = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("ODOO_URL", None)
    for i in range(SCENARIOS)
}
ODOO_DB = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("ODOO_DB", None)
    for i in range(SCENARIOS)
}
ODOO_USER = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("ODOO_USER", None)
    for i in range(SCENARIOS)
}
ODOO_COMPANY = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("ODOO_COMPANY", None)
    for i in range(SCENARIOS)
}
ODOO_SINGLECOMPANY = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("ODOO_SINGLECOMPANY", None)
    for i in range(SCENARIOS)
}
ODOO_PASSWORDS = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("ODOO_PASSWORD", None)
    for i in range(SCENARIOS)
}

# If passwords are set in this file they will be used instead of the ones set in the database parameters table
OPENBRAVO_PASSWORDS = {
    "default" if i == 0 else f"scenario{i}": os.environ.get("OPENBRAVO_PASSWORD", "")
    for i in range(SCENARIOS)
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
    "FREPPLE_THEMES",
    "earth grass dark lemon odoo openbravo orange snow strawberry water",
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

# Maximum allowed life time (in days) before an API key expires
APIKEY_MAX_LIFE = 10000

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
# Fill in this setting with the url of your server to get hyperlinks in emails
EMAIL_URL_PREFIX = None

# ADVANCED HTTP SECURITY SETTING: Clickjacking security http headers
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
# Default: allow content from same domain
CONTENT_SECURITY_POLICY = os.environ.get(
    "FREPPLE_CONTENT_SECURITY_POLICY", "frame-ancestors 'self'"
)
X_FRAME_OPTIONS = os.environ.get("FREPPLE_X_FRAME_OPTIONS", "SAMEORIGIN")
CSRF_COOKIE_SAMESITE = os.environ.get("FREPPLE_CSRF_COOKIE_SAMESITE", "lax")
SESSION_COOKIE_SAMESITE = os.environ.get("FREPPLE_SESSION_COOKIE_SAMESITE", "lax")
# Alternative: prohibit embedding in any frame
#   CONTENT_SECURITY_POLICY = "frame-ancestors 'none'"
#   X_FRAME_OPTIONS = "DENY"
# Alternative: allow embedding in a specific domain
#   CONTENT_SECURITY_POLICY = "frame-ancestors 'self' mydomain.com;"
#   X_FRAME_OPTIONS = None
#   CSRF_COOKIE_SAMESITE = "none"
#   SESSION_COOKIE_SAMESITE = "none"

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
