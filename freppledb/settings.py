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

r"""
Main Django configuration file.

It is recommended not to edit this file!
Instead put all your settings in the file FREPPLE_CONFDIR/djangosettings.py.

"""
import locale
import os
import sys
import importlib
import freppledb
import pathlib

from django.contrib import messages
import django.contrib.admindocs
from django.utils.translation import gettext_lazy as _


# FREPPLE_APP directory
if "FREPPLE_APP" in os.environ:
    FREPPLE_APP = os.environ["FREPPLE_APP"]
else:
    FREPPLE_APP = os.path.abspath(
        os.path.join(os.path.dirname(freppledb.__file__), "..")
    )

# FREPPLE_HOME directory
if "FREPPLE_HOME" in os.environ:
    FREPPLE_HOME = os.environ["FREPPLE_HOME"]
elif os.sep == "/" and os.path.isfile("/usr/share/frepple/frepple.xsd"):
    # Linux installation layout with prefix /usr
    FREPPLE_HOME = "/usr/share/frepple"
elif os.sep == "/" and os.path.isfile("/usr/local/share/frepple/frepple.xsd"):
    # Linux installation layout with prefix /usr/local
    FREPPLE_HOME = "/usr/local/share/frepple"
elif os.path.isfile(os.path.abspath(os.path.join(FREPPLE_APP, "..", "frepple.xsd"))):
    # Cx_freeze layout
    FREPPLE_HOME = os.path.abspath(os.path.join(FREPPLE_APP, ".."))
elif os.path.isfile(os.path.abspath(os.path.join(FREPPLE_APP, "bin", "frepple.xsd"))):
    # Development layout
    FREPPLE_HOME = os.path.abspath(os.path.join(FREPPLE_APP, "bin"))
else:
    print("Error: Can't locate frepple.xsd")
    sys.exit(1)
os.environ["FREPPLE_HOME"] = FREPPLE_HOME

# FREPPLE_LOGDIR directory
if "FREPPLE_LOGDIR" in os.environ:
    FREPPLE_LOGDIR = os.environ["FREPPLE_LOGDIR"]
elif os.sep == "/" and os.access("/var/log/frepple", os.W_OK):
    # Linux installation layout
    FREPPLE_LOGDIR = "/var/log/frepple"
else:
    FREPPLE_LOGDIR = os.path.abspath(os.path.join(FREPPLE_APP, "logs"))

# FREPPLE_CONFIGDIR directory
if "FREPPLE_CONFIGDIR" in os.environ:
    FREPPLE_CONFIGDIR = os.environ["FREPPLE_CONFIGDIR"]
elif os.sep == "/" and os.path.isfile("/etc/frepple/djangosettings.py"):
    # Linux installation layout
    FREPPLE_CONFIGDIR = "/etc/frepple"
else:
    FREPPLE_CONFIGDIR = FREPPLE_APP

try:
    DEBUG = "runserver" in sys.argv
except Exception:
    DEBUG = False
DEBUG_JS = DEBUG

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
ALLOWED_HOSTS = ["*"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
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

# We provide 3 options for formatting dates (and you always add your own).
#  - month-day-year: US format
#  - day-month-year: European format
#  - year-month-day: international format. This is the default
# As option you can choose to hide the hour, minutes and seconds.
DATE_STYLE = os.environ.get("FREPPLE_DATE_STYLE", "year-month-day")
DATE_STYLE_WITH_HOURS = (
    os.environ.get("FREPPLE_DATE_STYLE_WITH_HOURS", "false").lower() == "true"
)

# The default redirects URLs not ending with a slash.
# This causes trouble in combination with the DatabaseSelectionMiddleware.
# We prefer not to redirect and report this as an incorrect URL.
APPEND_SLASH = False

ASGI_APPLICATION = "freppledb.asgi.application"
WSGI_APPLICATION = "freppledb.wsgi.application"
ROOT_URLCONF = "freppledb.urls"
if "FREPPLE_STATIC" in os.environ:
    STATIC_ROOT = os.environ["FREPPLE_STATIC"]
elif os.sep == "/" and os.path.isdir("/usr/share/frepple/static"):
    # Standard Linux installation
    STATIC_ROOT = "/usr/share/frepple/static"
else:
    # All other layout types
    STATIC_ROOT = os.path.normpath(os.path.join(FREPPLE_APP, "static"))
STATIC_URL = "/static/"
USE_L10N = False  # No automatic localization
USE_I18N = True  # Use translated strings
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# A boolean that specifies if datetimes will be timezone-aware by default or not.
# If this is set to True, we will use timezone-aware datetimes internally.
# Otherwise, we use naive datetimes in local time.
USE_TZ = False

# Clickjacking security http headers
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

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_NAME = "sessionid"  # Cookie name. This can be whatever you want.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 2  # Age of cookie, in seconds: 2 days
SESSION_COOKIE_DOMAIN = None  # A string, or None for standard domain cookie.
SESSION_SAVE_EVERY_REQUEST = True  # Whether to save the session data on every request.
# Needs to be True to have the breadcrumbs working correctly!
SESSION_EXPIRE_AT_BROWSER_CLOSE = (
    True  # Whether sessions expire when a user closes his browser.
)
SESSION_COOKIE_HTTPONLY = True

# Users are automatically logged out after this period of inactivity
SESSION_LOGOUT_IDLE_TIME = 60 * 24  # minutes

MESSAGE_STORAGE = "django.contrib.messages.storage.fallback.SessionStorage"

TEST_RUNNER = "django.test.runner.DiscoverRunner"

DATABASE_ROUTERS = ["freppledb.common.models.MultiDBRouter"]

CSRF_FAILURE_VIEW = "freppledb.common.views.csrf_failure"

# Settings for user uploaded files
MEDIA_URL = "/uploads/"  # Do not change this
# This list of allowed extensions is what github.com allows.
# Be VERY careful about security when enlarging this list!
MEDIA_EXTENSIONS = ".gif,.jpeg,.jpg,.png,.docx,.gz,.log,.pdf,.pptx,.txt,.xlsx,.zip"
# Number of seconds a browser can cache uploaded content
MEDIA_MAX_AGE = 12 * 3600

LOGOUT_REDIRECT_URL = "/data/login/"

# Mail settings
# DEFAULT_FROM_EMAIL #if not pass from_email to send_mail func.
# EMAIL_HOST #required
# EMAIL_PORT #required
# EMAIL_HOST_USER #if required authentication to host
# EMAIL_HOST_PASSWORD #if required auth.

# Backends for user authentication and authorization.
# FrePPLe currently supports only this custom one.
AUTHENTICATION_BACKENDS = ("freppledb.common.auth.MultiDBBackend",)

# Custom user model
AUTH_USER_MODEL = "common.User"

# IP address of the machine you are browsing from. When logging in from this
# machine additional debugging statements can be shown.
INTERNAL_IPS = ("127.0.0.1",)

# Default charset to use for all ``HttpResponse`` objects, if a MIME type isn't
# manually specified.
DEFAULT_CHARSET = "utf-8"

BRANDING = "frePPLe"

# Default characterset for writing and reading CSV files.
# We are assuming here that the default encoding of clients is the same as the server.
# If the server is on Linux and the clients are using Windows, this guess will not be good.
# For Windows clients you should set this to the encoding that is better suited for Excel or
# other office tools.
#    Windows - western europe -> 'cp1252'
CSV_CHARSET = "utf-8"  # locale.getdefaultlocale()[1]

# A list of available user interface themes.
# If multiple themes are configured in this list, the user's can change their
# preferences among the ones listed here.
# If the list contains only a single value, the preferences screen will not
# display users an option to choose the theme.
THEMES = os.environ.get(
    "FREPPLE_THEMES", "earth grass lemon odoo openbravo orange snow strawberry water"
).split()

# Website where all documentation is available.
# - The DOCUMENTATION_URL is used as the main URL for the about box
# - The documentation is expected to be found in 'DOCUMENTATION_URL/docs/MAJOR_VERSION.MINOR_VERSION"
# - The URL shouldn't have an ending slash
DOCUMENTATION_URL = "https://frepple.com"

# A default user-group to which new users are automatically added
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
        "rowname": _("execute"),
        "cols": [
            {
                "width": 6,
                "widgets": [
                    ("execute", {}),
                ],
            },
            {
                "width": 6,
                "widgets": [
                    ("executegroup", {}),
                ],
            },
        ],
    },
    {
        "rowname": _("sales"),
        "cols": [
            {
                "width": 6,
                "widgets": [
                    ("forecast", {"history": 36, "future": 12}),
                    # (
                    #     "analysis_demand_problems",
                    #     {"top": 20, "orderby": "latedemandvalue"},
                    # ),
                    # ("outliers", {"limit": 20}),
                ],
            },
            {
                "width": 3,
                "widgets": [
                    # ("demand_alerts", {}),
                    ("delivery_performance", {"green": 90, "yellow": 80}),
                ],
            },
            {
                "width": 3,
                "widgets": [
                    ("forecast_error", {"history": 12}),
                    # ("archived_demand", {"history": 12}),
                ],
            },
        ],
    },
    {
        "rowname": _("purchasing"),
        "cols": [
            {
                "width": 8,
                "widgets": [
                    ("purchase_orders", {"fence1": 7, "fence2": 30}),
                    # ("purchase_queue",{"limit":20}),
                    # ("purchase_order_analysis", {"limit": 20}),
                ],
            },
            {
                "width": 4,
                "widgets": [
                    # ("archived_purchase_order", {"history": 12}),
                    ("inventory_by_location", {"limit": 5}),
                    # ("inventory_by_item", {"limit": 10}),
                ],
            },
        ],
    },
    {
        "rowname": _("manufacturing"),
        "cols": [
            {
                "width": 8,
                "widgets": [
                    ("manufacturing_orders", {"fence1": 7, "fence2": 30}),
                    # ("resource_queue",{"limit":20}),
                ],
            },
            {
                "width": 4,
                "widgets": [
                    # ("capacity_alerts", {}),
                    ("resource_utilization", {"limit": 5, "medium": 80, "high": 90}),
                ],
            },
        ],
    },
    {
        "rowname": _("distribution"),
        "cols": [
            {
                "width": 8,
                "widgets": [
                    ("distribution_orders", {"fence1": 7, "fence2": 30}),
                    # ("shipping_queue",{"limit":20}),
                    # ("archived_buffer", {"history": 12}),
                ],
            },
            {
                "width": 4,
                "widgets": [
                    ("inventory_evolution", {"history": 12}),
                ],
            },
        ],
    },
]

# Memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

GLOBAL_PREFERENCES = {}

# Maximum allowed memory size for the planning engine. Only used on Linux!
MAXMEMORYSIZE = None  # limit in MB, minimum around 230, use None for unlimited

# Maximum allowed memory size for the planning engine. Only used on Linux!
MAXCPUTIME = None  # limit in seconds, use None for unlimited

# Maximum allowed storage.
# The storage counts database storage, data files, engine log files, database dump files, plan export files.
MAXSTORAGE = None  # limit in MB, use None for unlimited.

# Max total log files size in MB, if the limit is reached deletes the oldest.
MAXTOTALLOGFILESIZE = 200

# Google analytics code to report usage statistics to.
# The default value of None disables this feature.
GOOGLE_ANALYTICS = None

# Specify number of objects we are allowed to cache and the number of
# threads we create to write changed objects
CACHE_MAXIMUM = 1000000
CACHE_THREADS = 1

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.DjangoModelPermissions"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "freppledb.common.api.renderers.freppleBrowsableAPI",
    ),
}

# Bootstrap
MESSAGE_TAGS = {
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
    messages.INFO: "alert-success",
    messages.DEBUG: "alert-danger",
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # os.path.normpath(os.path.join(FREPPLE_HOME,'templates')),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "builtins": ["freppledb.common.templatetags"],
            "context_processors": [
                "freppledb.common.contextprocessors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.static",
            ],
        },
    }
]

LOCALE_PATHS = (
    os.path.normpath(os.path.join(FREPPLE_HOME, "locale", "django")),
    os.path.normpath(os.path.join(FREPPLE_HOME, "locale", "auth")),
    os.path.normpath(os.path.join(FREPPLE_HOME, "locale", "contenttypes")),
    os.path.normpath(os.path.join(FREPPLE_HOME, "locale", "sessions")),
    os.path.normpath(os.path.join(FREPPLE_HOME, "locale", "admin")),
    os.path.normpath(os.path.join(FREPPLE_HOME, "locale", "messages")),
    os.path.normpath(os.path.join(FREPPLE_APP, "freppledb", "locale")),
    os.path.normpath(
        os.path.join(os.path.dirname(django.contrib.admindocs.__file__), "locale")
    ),
)

# Configuration of the ftp/sftp/ftps server where to upload reports
# Note that for SFTP protocol, the host needs to be defined
# in the known_hosts file
FTP_PROTOCOL = os.environ.get(
    "FREPPLE_FTP_PROTOCOL", "SFTP"
)  # supported protocols are SFTP, FTPS and FTP (unsecure)
FTP_HOST = os.environ.get("FREPPLE_FTP_HOST", "")
FTP_PORT = int(os.environ.get("FREPPLE_FTP_PORT", 22))
FTP_USER = os.environ.get("FREPPLE_FTP_USER", "")
FTP_PASSWORD = os.environ.get("FREPPLE_FTP_PASSWORD", "")
FTP_FOLDER = None  # folder where the files should be uploaded

SILENCED_SYSTEM_CHECKS = ["admin.E408"]

# Override any of the above settings from a separate file
if not os.access(os.path.join(FREPPLE_CONFIGDIR, "djangosettings.py"), os.R_OK):
    print("\nError: Can't locate djangosettings.py configuration file")
    sys.exit(1)
with open(os.path.join(FREPPLE_CONFIGDIR, "djangosettings.py")) as mysettingfile:
    exec(mysettingfile.read(), globals())

# Another level of overrides for development settings
if os.access(os.path.join(FREPPLE_CONFIGDIR, "localsettings.py"), os.R_OK):
    with open(os.path.join(FREPPLE_CONFIGDIR, "localsettings.py")) as mysettingfile:
        exec(mysettingfile.read(), globals())

# duplicate the entries in the DATABASES dict to create the SQL roles entries.
for i in DATABASES.copy():
    if DATABASES[i].get("SQL_ROLE", "report_role"):
        DATABASES[f"{i}_report"] = {
            **DATABASES[i],
            "USER": DATABASES[i].get("SQL_ROLE", "report_role"),
            "IS_REPORTING_DATABASE": True,
        }


# We don't like some settings to be overriden
MANAGERS = ADMINS
MEDIA_ROOT = os.path.join(FREPPLE_LOGDIR, "uploads")

# Some settings depend on things you can override in localsettings.py
if DATE_STYLE == "month-day-year":
    # Option 1: US style
    DATE_FORMAT = (
        # see https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#std-templatefilter-date
        "m/d/Y"
    )
    DATETIME_FORMAT = (
        # see https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#std-templatefilter-date
        "m/d/Y H:i:s"
        if DATE_STYLE_WITH_HOURS
        else "m/d/Y"
    )
    DATE_FORMAT_JS = (
        # see https://bootstrap-datepicker.readthedocs.io/en/latest/options.html#format
        "MM/DD/YYYY"
    )
    DATETIME_FORMAT_JS = (
        # see https://momentjs.com/docs/#/displaying/
        "MM-DD-YYYY HH:mm:ss"
        if DATE_STYLE_WITH_HOURS
        else "MM-DD-YYYY"
    )
    DATE_INPUT_FORMATS = [
        # See https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-DATE_FORMAT
        "%Y-%m-%d",  # Still recognize input in international format with 4-digit year
        "%Y.%m.%d",  # Still recognize input in international format with 4-digit year
        "%Y/%m/%d",  # Still recognize input in international format with 4-digit year
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%m-%d-%y",
        "%m.%d.%Y",
        "%m.%d.%y",
        "%b %d %Y",
        "%b %d, %Y",
        "%d %b %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%d %B, %Y",
    ]
    DATETIME_INPUT_FORMATS = [
        # See https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-DATETIME_FORMAT
        "%Y-%m-%d %H:%M:%S",  # Still recognize input in international format with 4-digit year
        "%Y.%m.%d %H:%M:%S",  # Still recognize input in international format with 4-digit year
        "%Y/%m/%d %H:%M:%S",  # Still recognize input in international format with 4-digit year
        "%Y-%m-%d %H:%M",  # Still recognize input in international format with 4-digit year
        "%Y.%m.%d %H:%M",  # Still recognize input in international format with 4-digit year
        "%Y/%m/%d %H:%M",  # Still recognize input in international format with 4-digit year 
        "%m/%d/%Y %H:%M:%S",
        "%m-%d-%Y %H:%M:%S",
        "%m-%d-%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%m.%d.%Y %H:%M:%S",
        "%m.%d.%Y %H:%M",
        "%m.%d.%y %H:%M:%S",
        "%m.%d.%y %H:%M",
    ]
elif DATE_STYLE == "day-month-year":
    # Option 2: European style
    DATE_FORMAT = (
        # see https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#std-templatefilter-date
        "d-m-Y"
    )
    DATETIME_FORMAT = (
        # see https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#std-templatefilter-date
        "d-m-Y H:i:s"
        if DATE_STYLE_WITH_HOURS
        else "d-m-Y"
    )
    DATE_FORMAT_JS = (
        # see https://bootstrap-datepicker.readthedocs.io/en/latest/options.html#format
        "DD-MM-YYYY"
    )
    DATETIME_FORMAT_JS = (
        # see https://momentjs.com/docs/#/displaying/
        "DD-MM-YYYY HH:mm:ss"
        if DATE_STYLE_WITH_HOURS
        else "DD-MM-YYYY"
    )
    DATE_INPUT_FORMATS = [
        # See https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-DATE_FORMAT
        "%Y-%m-%d",  # Still recognize input in international format with 4-digit year
        "%Y.%m.%d",  # Still recognize input in international format with 4-digit year
        "%Y/%m/%d",  # Still recognize input in international format with 4-digit year        
        "%d-%m-%Y",
        "%d-%m-%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%b %d %Y",
        "%b %d, %Y",
        "%d %b %Y",
        "%d %b, %Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%d %B, %Y",
    ]
    DATETIME_INPUT_FORMATS = [
        # See https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-DATETIME_FORMAT
        "%Y-%m-%d %H:%M:%S",  # Still recognize input in international format with 4-digit year
        "%Y.%m.%d %H:%M:%S",  # Still recognize input in international format with 4-digit year
        "%Y/%m/%d %H:%M:%S",  # Still recognize input in international format with 4-digit year
        "%Y-%m-%d %H:%M",  # Still recognize input in international format with 4-digit year
        "%Y.%m.%d %H:%M",  # Still recognize input in international format with 4-digit year
        "%Y/%m/%d %H:%M",  # Still recognize input in international format with 4-digit year     
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%d/%m/%y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%f/%m/%Y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%d/%m/%y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%y %H:%M:%S",
        "%d.%m.%y %H:%M",
    ]
else:
    # Option 3: International style, default
    DATE_FORMAT = (
        # see https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#std-templatefilter-date
        "Y-m-d"
    )
    DATETIME_FORMAT = (
        # see https://docs.djangoproject.com/en/3.2/ref/templates/builtins/#std-templatefilter-date
        "Y-m-d H:i:s"
        if DATE_STYLE_WITH_HOURS
        else "Y-m-d"
    )
    DATE_FORMAT_JS = (
        # see https://bootstrap-datepicker.readthedocs.io/en/latest/options.html#format
        "YYYY-MM-DD"
    )
    DATETIME_FORMAT_JS = (
        # see https://momentjs.com/docs/#/displaying/
        "YYYY-MM-DD HH:mm:ss"
        if DATE_STYLE_WITH_HOURS
        else "YYYY-MM-DD"
    )
    DATE_INPUT_FORMATS = [
        # See https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-DATE_FORMAT
        "%Y-%m-%d",
        "%y-%m-%d",
        "%Y/%m/%d",
        "%y/%m/%d",
        "%Y.%m.%d",
        "%y.%m.%d",
        "%b %d %Y",
        "%b %d, %Y",
        "%d %b %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%d %B, %Y",
    ]
    DATETIME_INPUT_FORMATS = [
        # See https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-DATETIME_FORMAT
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%y-%m-%d %H:%M:%S",
        "%y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%y/%m/%d %H:%M:%S",
        "%y/%m/%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%y.%m.%d %H:%M:%S",
        "%y.%m.%d %H:%M",
    ]

# Change the default dashboard if the wizard is active
if "freppledb.wizard" in INSTALLED_APPS:
    DEFAULT_DASHBOARD.insert(
        0,
        {
            "rowname": _("Welcome"),
            "cols": [
                {"width": 12, "widgets": [("wizard", {})]},
            ],
        },
    )

# If a entry in INSTALLABLE_APPS points to a folder, we add this folder to the python path
try:
    for x in INSTALLABLE_APPS:
        if isinstance(x, pathlib.Path) and x.exists() and x.is_dir():
            sys.path.append(str(x.resolve()))
except NameError:
    pass

# Find the ERP connector module
ERP_CONNECTOR = None
for app in INSTALLED_APPS:
    app_module = importlib.import_module(app)
    if getattr(app_module, "ERP_module", False):
        if not ERP_CONNECTOR:
            ERP_CONNECTOR = app.replace("freppledb.", "")
        else:
            from django.core.exceptions import ImproperlyConfigured

            raise ImproperlyConfigured(
                "Only a single ERP connection app can be installed at a time"
            )
