=========
Reference
=========

This page describes the standard frePPLe container. Start with
:doc:`quick-start` for a working Compose example and :doc:`installation`
for production guidance.

Image information
-----------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Item
     - Value
   * - Community image
     - ``ghcr.io/frepple/frepple-community:latest``, or (recommended)
       pin a specific release ``ghcr.io/frepple/frepple-community:VERSION``
   * - Enterprise image
     - ``ghcr.io/frepple/frepple-enterprise:latest``, or (recommended)
       pin a specific release ``ghcr.io/frepple/frepple-enterprise:VERSION``
   * - Ports
     - | The image exposes only the HTTP port 80.
       | You'll map it to a host port or reach it from a reverse proxy on
         the application network.
   * - Container user
     - | All processes in the container run as the unprivileged user ``frepple``.
       | Working in the container as this user ensures file permissions are
         correctly preserved.
       | If you need root access (eg to install additional packages), you should
         use a custom dockerfile to perform privileged operations.
   * - Entrypoint
     - | ``/etc/frepple/entrypoint.sh`` is the entrypoint script.
       | You can add custom initialization commands in the folder ``/etc/frepple/entrypoint.d``.
   * - Processes
     - Four processes are running in the container.

         - | The process supervisor ``supervisord`` manages the other processes.
           | It is configured in ``/etc/frepple/supervisord.conf``

         - | The web server ``nginx`` handles the HTTP requests.
           | It is configured in ``/etc/frepple/nginx.conf``

         - | The application server ``Uvicorn`` generates the web pages. The
           | web application is coded in Python using the Django framework.

         - | The task scheduler ``freppledb.scheduler`` manages background tasks.
           | It provides cron-like scheduling of tasks.


Volumes and paths
-----------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Container path
     - Contents and persistence
   * - ``/etc/frepple``
     - Declared volume. Main configuration, optional local overrides,
       license, entrypoint, startup hooks, nginx and supervisor
       configuration. Back it up and review its contents on upgrades.
   * - ``/var/log/frepple``
     - Declared volume. Task logs, database dumps, interface files and
       uploads/attachments. Persist and back up; not all contents are logs.
   * - ``/usr/share/frepple/python_packages``
     - Declared volume on the Python import path for custom packages.
       Back up packages maintained here. A derived image with pinned
       dependencies is preferable for reproducible deployments.
   * - ``/etc/frepple/djangosettings.py``
     - Main application settings. Must be writable by the container user
       for initialization and application management.
   * - ``/etc/frepple/localsettings.py``
     - Optional deployment overrides, read after the main settings file.
   * - ``/etc/frepple/license.xml``
     - Enterprise license. Can be mounted as a separate read-only file.
   * - ``/etc/frepple/entrypoint.d``
     - Optional executable startup hooks.
   * - ``/var/log/frepple/data/default``
     - Default scenario's import/export folder. Other scenarios use
       ``data/scenarioN``.
   * - ``/var/log/frepple/uploads``
     - Uploaded attachments.
   * - ``/usr/share/frepple/venv``
     - Bundled Python environment. Add packages through a derived image,
       not by modifying a running container.
   * - ``/usr/share/frepple/static``
     - Static assets served by nginx.
   * - ``/var/lib/frepple``
     - Runtime nginx PID and temporary files. Must be writable; normally
       doesn't need backup.

PostgreSQL storage belongs to the separate database container. In the
PostgreSQL 17 example, persist ``/var/lib/postgresql/data``. Other major
versions can have a different image storage layout; consult that image's
documentation before changing versions.

Use explicit named volumes or deliberate bind mounts for persistent data.
Docker can create anonymous volumes for image-declared paths not listed in
Compose. Don't rely on anonymous volume names for your recovery procedure.
Mounting existing storage hides the image's contents at that path.

nginx access/error output and supervisor-managed process output go to
standard output/error and are visible through ``docker compose logs``.
Legacy Apache paths such as ``/etc/apache2`` and ``/var/log/apache2`` are
not used by this image.

Configuration precedence
------------------------

#. The application loads its base settings.
#. ``/etc/frepple/djangosettings.py`` is executed. The standard file reads
   the environment variables listed below and selected database parameters.
#. ``/etc/frepple/localsettings.py``, if present, applies further overrides.
#. Derived settings, including ``DATABASES`` and reporting connections, are
   built from the resulting values.

Consequently, a custom Python assignment can override an environment
variable, and assigning ``DATABASES`` in ``localsettings.py`` does not replace
the subsequently generated dictionary.

The standard configuration reads ``scenarios``, ``optional_apps``,
``currency``, ``date_format`` and ``display_time`` from the default database.
Use the application screens for these settings where possible.

Environment variables
----------------------

These are application/container variables, not an exhaustive list of
variables understood by PostgreSQL, Docker or third-party libraries.
Boolean variables below accept ``true`` (case-insensitive) to enable them;
other strings evaluate to false. Whitespace-separated lists are not JSON
arrays.

Database connection
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Variable
     - Default
     - Meaning
   * - ``POSTGRES_HOST``
     - ``localhost``
     - Database hostname. Set explicitly for a separate database container.
   * - ``POSTGRES_PORT``
     - Empty
     - Database port. An empty value uses the PostgreSQL client default,
       normally 5432.
   * - ``POSTGRES_USER``
     - ``frepple``
     - Application database role.
   * - ``POSTGRES_PASSWORD``
     - ``frepple``
     - Application database password. Replace the default.
   * - ``POSTGRES_DB_PREFIX``
     - ``frepple``
     - Prefix for numbered database names: ``frepple0``, ``frepple1``, etc.
   * - ``POSTGRES_DBNAME``
     - Unset
     - Legacy alias for the prefix, not a single database name.
       ``POSTGRES_DB_PREFIX`` takes precedence when nonempty.
   * - ``POSTGRES_REPORTING_USER``
     - ``report_role``
     - Restricted database login for custom SQL/report processing.

The standard configuration uses the application password for the reporting
connection as well. If you rotate passwords, coordinate the application and
reporting roles.

Changing the database prefix does not rename or move existing databases.
With a new prefix, startup can create a new, empty environment instead of
opening your existing data. Treat a prefix change as a database migration.

The PostgreSQL image uses its own ``POSTGRES_DB`` variable when initializing
the database server. That variable does not configure frePPLe's database
prefix. PostgreSQL-image initialization variables only take effect when
initializing empty database storage.

Web processes and presentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Variable
     - Default
     - Meaning
   * - ``FREPPLE_WEBWORKERS``
     - ``4``
     - Number of Uvicorn workers started by supervisor.
   * - ``FREPPLE_AUTOSTART_WEBSERVICE``
     - Empty
     - Space-separated scenario identifiers whose planning web services
       should start automatically, for example ``default scenario1``.
   * - ``FREPPLE_TIME_ZONE``
     - Detected local timezone
     - IANA timezone such as ``UTC`` or ``Europe/Brussels``. If detection
       fails, the standard configuration falls back to ``Europe/Brussels``.
   * - ``FREPPLE_THEMES``
     - Bundled theme list
     - Space-separated names. The supplied list is ``earth grass dark lemon
       odoo openbravo orange snow strawberry water``.
   * - ``FREPPLE_DEFAULT_THEME``
     - ``earth``
     - Default theme. If not in the enabled list, its first entry is used.
   * - ``FREPPLE_DATE_STYLE``
     - ``year-month-day`` in base settings
     - Legacy base setting. The standard main configuration overrides it
       with the database's ``date_format`` parameter.
   * - ``FREPPLE_DATE_STYLE_WITH_HOURS``
     - ``false`` in base settings
     - Legacy base setting. The standard main configuration overrides it
       with the database's ``display_time`` parameter, defaulting to true.

HTTPS, cookies and embedding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Variable
     - Default
     - Meaning
   * - ``FREPPLE_CSRF_TRUSTED_ORIGINS``
     - Empty
     - Space-separated trusted origins, including scheme.
   * - ``FREPPLE_SECURE_PROXY_SSL_HEADER``
     - Empty
     - Header/value pair separated by whitespace, normally
       ``HTTP_X_FORWARDED_PROTO https``. Requires trusted proxy handling
       at both proxy layers; see :ref:`installation-https`.
   * - ``FREPPLE_SESSION_COOKIE_SECURE``
     - ``false``
     - Restrict session cookies to HTTPS. Enable in production.
   * - ``FREPPLE_CSRF_COOKIE_SECURE``
     - ``false``
     - Restrict CSRF cookies to HTTPS. Enable in production.
   * - ``FREPPLE_SESSION_COOKIE_SAMESITE``
     - ``lax``
     - SameSite policy for session cookies.
   * - ``FREPPLE_CSRF_COOKIE_SAMESITE``
     - ``lax``
     - SameSite policy for CSRF cookies.
   * - ``FREPPLE_CONTENT_SECURITY_POLICY``
     - ``frame-ancestors 'self'``
     - Content Security Policy header, restricting framing by default.
   * - ``FREPPLE_X_FRAME_OPTIONS``
     - ``SAMEORIGIN``
     - Additional framing restriction.

Use Python settings for values that cannot be represented by these string
variables, for example ``X_FRAME_OPTIONS = None``. Review the security impact
before enabling cross-site framing or cookies.

Email
~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Variable
     - Default
     - Meaning
   * - ``FREPPLE_EMAIL_HOST``
     - Empty (no host configured)
     - SMTP server hostname.
   * - ``FREPPLE_EMAIL_PORT``
     - ``25``
     - SMTP server port.
   * - ``FREPPLE_EMAIL_USE_TLS``
     - ``true``
     - Use STARTTLS for the SMTP connection.
   * - ``FREPPLE_EMAIL_HOST_USER``
     - ``your_email@domain.com``
     - SMTP username; replace the placeholder.
   * - ``FREPPLE_EMAIL_HOST_PASSWORD``
     - Placeholder
     - SMTP password; configure your own credential.
   * - ``FREPPLE_DEFAULT_FROM_EMAIL``
     - ``your_email@domain.com``
     - Default sender address.
   * - ``FREPPLE_SERVER_EMAIL``
     - ``your_email@domain.com``
     - Sender address for server messages.

Set ``EMAIL_URL_PREFIX`` in Python configuration to the public application
URL when email links need an absolute URL.

Report uploads
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Variable
     - Default
     - Meaning
   * - ``FREPPLE_FTP_PROTOCOL``
     - ``SFTP``
     - Upload protocol: ``SFTP``, ``FTPS`` or unencrypted ``FTP``.
   * - ``FREPPLE_FTP_HOST``
     - Empty
     - Remote server.
   * - ``FREPPLE_FTP_PORT``
     - ``22``
     - Remote port; set it explicitly when changing protocols.
   * - ``FREPPLE_FTP_USER``
     - Empty
     - Remote username.
   * - ``FREPPLE_FTP_PASSWORD``
     - Empty
     - Remote password.

Set ``FTP_FOLDER`` in Python configuration, either as a common value or a
dictionary keyed by scenario. For SFTP, provision the remote host's verified
key in the container user's SSH ``known_hosts`` file and persist that
configuration. Never disable host-key verification to bypass a connection
failure.

Connector credentials
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Variable
     - Meaning
   * - ``ODOO_URL``
     - Odoo server URL.
   * - ``ODOO_DB``
     - Odoo database name.
   * - ``ODOO_USER``
     - Odoo login.
   * - ``ODOO_PASSWORD``
     - Odoo credential.
   * - ``ODOO_COMPANY``
     - Company selection.
   * - ``ODOO_SINGLECOMPANY``
     - Connector's single-company option.
   * - ``OPENBRAVO_PASSWORD``
     - Openbravo credential.

These variables are unset by default. The standard configuration applies
them across scenarios. Configured credentials/settings can override the
corresponding database parameters; see the connector documentation for
scenario-specific configuration.


Settings without environment variables
--------------------------------------

Configure these in Python rather than inventing ``FREPPLE_`` variables:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Setting
     - Purpose
   * - ``ALLOWED_HOSTS``
     - Accepted hostnames. Restrict to the production hostname(s).
   * - ``SECRET_KEY``
     - Deployment secret. The entrypoint replaces the shipped placeholder
       on first startup; preserve the resulting value across restarts
       and recovery.
   * - ``SECRET_WEBTOKEN_KEY``
     - Key for planning-service tokens; defaults to ``SECRET_KEY``.
   * - ``DEFAULT_USER_GROUP``
     - Default permissions group for new users. Review carefully when
       enabling external signup.
   * - ``EMAIL_URL_PREFIX``
     - Public base URL for email links.
   * - ``MAXSTORAGE``
     - Application storage quota in MB; ``None`` means unlimited.
   * - ``MAXTOTALLOGFILESIZE``
     - Total task-log retention limit in MB, default 200.
   * - ``MAXMEMORYSIZE``
     - Planning engine memory limit in MB; ``None`` means unlimited.
   * - ``MAXCPUTIME``
     - Planning engine CPU-time limit in seconds; ``None`` means unlimited.
   * - ``MIN_NUMBER_OF_SCENARIOS``, ``MAX_NUMBER_OF_SCENARIOS``
     - Bounds on scenario count; see :ref:`installation-scenarios`.

Startup behavior
----------------

The standard entrypoint:

#. Replaces the shipped ``SECRET_KEY`` placeholder and makes the main
   configuration group-writable.
#. If ``POSTGRES_USER``, ``POSTGRES_HOST`` or ``POSTGRES_PORT`` is set,
   waits briefly for PostgreSQL, creates missing configured databases,
   and runs migrations for the default and active scenarios.
#. On a fresh default database, creates distribution and manufacturing
   demo scenarios and starts their initial planning runs.
#. Starts planning web services named by ``FREPPLE_AUTOSTART_WEBSERVICE``.
#. If a command was passed, executes it instead of supervisor. Otherwise,
   runs startup hooks and starts supervisor.

Database initialization isn't limited to the first container creation.
Restarting or recreating a container can run migrations again, so schedule
upgrades deliberately and inspect their output. A running container is not
proof that all scenarios migrated successfully.
