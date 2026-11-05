============
Installation
============

Use the Compose configuration in :doc:`quick-start` as the starting point for
a production deployment. This page describes the changes and checks needed
before putting that installation into service.

The frePPLe container includes the planning engine, nginx, the application
server and the task scheduler. PostgreSQL is a separate service. Keep one
frePPLe application container per deployment unless you have designed and
validated a different arrangement; adding replicas is not a substitute for
sizing the planning engine and database.

Prepare the deployment
----------------------

#. Check :doc:`pre-requisites` and size the host for your actual model.
#. Select a specific frePPLe image version and a maintained PostgreSQL
   version. Record the versions in your deployment configuration.
#. Store ``compose.yml``, custom image sources and non-secret configuration
   in version control. Keep ``.env``, license files, database dumps and
   credentials out of version control.
#. Decide which storage to use for PostgreSQL, ``/etc/frepple`` and
   ``/var/log/frepple``. These must survive container replacement.
#. Arrange a maintenance window, backups, monitoring and an HTTPS endpoint.

Keep the Compose project name and deployment directory stable. A different
project name can select a new set of named volumes, making an existing
installation appear empty.

.. _installation-external-postgres:

Configure PostgreSQL
--------------------

For production, use a dedicated application role instead of connecting as a
PostgreSQL superuser.

For example, a database administrator can create the role as follows,
substituting a strong password:

.. code-block:: sql

   CREATE ROLE frepple WITH LOGIN PASSWORD 'replace-with-a-random-password'
     CREATEDB CREATEROLE;

FrePPLe creates the configured databases at startup if they don't already
exist. The application role must own its databases and the objects in them,
and must be able to create and configure the restricted reporting role
(``report_role`` by default). Database migrations configure this role for
custom SQL reports and SQL-file processing.

Where your database service restricts role or database creation, have the
database administrator provision the databases and reporting role and grant
the required privileges. Validate migrations, scenario copying and custom
reports before going live. Don't work around missing permissions by
disabling the reporting role: that would allow custom SQL to run with the
application's full database privileges.

The default database names are ``frepple0``, ``frepple1`` and ``frepple2``.
The application calls these ``default``, ``scenario1`` and ``scenario2``.
``POSTGRES_DB_PREFIX`` changes the prefix; it doesn't name a single database.
Extra scenario slots require extra databases.

For an external database, change the frePPLe service's environment:

.. code-block:: yaml

   environment:
     POSTGRES_HOST: database.example.com
     POSTGRES_PORT: "5432"
     POSTGRES_USER: frepple
     POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
     POSTGRES_DB_PREFIX: frepple
     FREPPLE_TIME_ZONE: UTC

Remove the ``depends_on`` entry for the bundled PostgreSQL service, and omit
that service and its volume from the Compose file if they are no longer used.

* Use the database service's DNS name, not ``localhost``: inside the
  application container, ``localhost`` is the application container itself.
* Restrict database access to the application network in the firewall and
  PostgreSQL's ``pg_hba.conf``.
* Use UTF-8 encoding. The connection timezone should match frePPLe's
  ``TIME_ZONE``; the transaction isolation level is ``read committed``.
* Configure database connection encryption as required by your database
  service. See PostgreSQL's
  `libpq SSL documentation <https://www.postgresql.org/docs/current/libpq-ssl.html>`_
  for certificate verification and connection options.

Tune PostgreSQL
~~~~~~~~~~~~~~~

The default PostgreSQL configuration isn't tuned for planning workloads.
Use `PGTune <https://pgtune.leopard.in.ua/>`_ with the data warehouse workload
as a starting point, then validate with your model.

Budget memory for the database, the planning engine and concurrent tasks
together. Review ``max_connections`` across all active scenarios and web
workers; the old deployment guidance suggested around 400 rather than the
default 100, but the appropriate value depends on workload and available
memory.

Manage persistent configuration
-------------------------------

The container runs as the unprivileged ``frepple`` user. Named volumes are
the simplest starting point. When using host bind mounts, set ownership and
permissions so this user can read configuration and licenses and write
application files.

Don't mount an empty host directory over ``/etc/frepple``: it hides the
configuration supplied by the image. To obtain a copy from a running
installation:

.. code-block:: bash

   docker compose cp frepple:/etc/frepple ./frepple-config

The main configuration is ``/etc/frepple/djangosettings.py``. For deployment
overrides, you can also create ``/etc/frepple/localsettings.py``. It is read
after the main configuration. For example:

.. code-block:: python

   ALLOWED_HOSTS = ["planning.example.com"]
   EMAIL_URL_PREFIX = "https://planning.example.com"
   MAXSTORAGE = 20000

Copy it into the configuration volume and restart:

.. code-block:: bash

   docker compose cp localsettings.py frepple:/etc/frepple/localsettings.py
   docker compose restart frepple

Use the supported environment variables for routine deployment settings;
see :doc:`reference`. Changes to the Compose environment require
``docker compose up -d`` to recreate the container: a restart alone does
not load a changed environment.

.. important::

   The entrypoint must be able to update ``djangosettings.py`` and its
   permissions. Don't bind-mount this file or the entire configuration
   directory read-only.

   A persistent configuration volume also retains the old release's
   ``djangosettings.py``, nginx configuration, supervisor configuration and
   entrypoint. Review these against the new image on every upgrade.
   Persisting configuration does not automatically merge new defaults.

.. _https:
.. _proxy:
.. _installation-https:

Configure HTTPS and a reverse proxy
-----------------------------------

Terminate HTTPS at a reverse proxy in front of the frePPLe container.
When the proxy runs on the Docker host, the quick start's
``127.0.0.1:9000:80`` mapping keeps the unencrypted backend local.
When the proxy runs in another container, connect it to the application
network and forward to ``frepple:80`` instead; its ``localhost`` is not
the Docker host.

Configure the proxy to:

* Present a valid TLS certificate for the public hostname.
* Preserve the original ``Host`` header.
* Support WebSocket upgrades for ``/ws/`` paths and forward ``/svc/`` paths.
* Allow the upload sizes and request timeouts needed by your planning process.
* Set, rather than trust client-supplied, forwarded headers.

Set these variables on the frePPLe service, substituting your public URL:

.. code-block:: yaml

   FREPPLE_CSRF_TRUSTED_ORIGINS: "https://planning.example.com"
   FREPPLE_SECURE_PROXY_SSL_HEADER: "HTTP_X_FORWARDED_PROTO https"
   FREPPLE_SESSION_COOKIE_SECURE: "true"
   FREPPLE_CSRF_COOKIE_SECURE: "true"

.. important::

   The image's nginx configuration sets ``X-Forwarded-Proto`` to its own
   connection scheme. With an external TLS terminator, that scheme is
   normally HTTP. Setting the environment variables above alone isn't
   sufficient.

   In ``/etc/frepple/nginx.conf``, adapt the existing
   ``proxy_set_header X-Forwarded-Proto $scheme;`` directive. For a backend
   reachable only through an HTTPS endpoint, it can be set to
   ``proxy_set_header X-Forwarded-Proto https;``. If you instead preserve
   an incoming forwarded header, ensure only the trusted proxy can reach
   the backend and that the proxy overwrites that header.

   Test the configuration with
   ``docker compose exec frepple nginx -t -c /etc/frepple/nginx.conf``
   before restarting the container.

Also restrict ``ALLOWED_HOSTS`` in ``localsettings.py``. Verify login, logout,
uploads, generated links and the plan editor through the public HTTPS URL.
Do not expose an alternate HTTP route that bypasses these controls.

.. _installation-enterprise:

Deploy the Enterprise Edition
-----------------------------

Authenticate to the registry using an account authorized to read the image:

.. code-block:: bash

   docker login ghcr.io --username YOUR_GITHUB_USER

Change the image in ``compose.yml`` to:

.. code-block:: yaml

   image: ghcr.io/frepple/frepple-enterprise:${FREPPLE_VERSION:?Set FREPPLE_VERSION in .env}

Place the license you received in a local file named ``license.xml`` and
mount it into the frePPLe service:

.. code-block:: yaml

   volumes:
     - frepple-config:/etc/frepple
     - frepple-data:/var/log/frepple
     - frepple-packages:/usr/share/frepple/python_packages
     - ./license.xml:/etc/frepple/license.xml:ro

The source must be an existing file, readable by the container's ``frepple``
user. Keep it private and include it in your protected backups. Don't bake
the license into a distributable image or commit it to source control.

Recreate the service with ``docker compose up -d`` and check the edition and
license information in *Help / About frePPLe*.

Deploy custom applications
--------------------------

Build a derived image rather than installing packages interactively in a
running container. This makes changes reproducible and prevents them from
disappearing when the container is replaced.

For example, this ``Dockerfile`` adds a Python application and dependencies:

.. code-block:: docker

   ARG FREPPLE_VERSION
   FROM ghcr.io/frepple/frepple-community:${FREPPLE_VERSION}

   COPY --chown=frepple:frepple myapp/ /usr/share/frepple/venv/lib/python3.12/site-packages/myapp/
   COPY --chown=frepple:frepple requirements.txt /tmp/custom-requirements.txt
   RUN /usr/share/frepple/venv/bin/python -m pip install --no-cache-dir -r /tmp/custom-requirements.txt

Check the Python version in your selected base image before using this path.
Keep custom dependencies compatible with the versions bundled with frePPLe.
Use the Enterprise base image instead if your application requires that edition.

Register the application in the ``APPS`` list in ``djangosettings.py``,
before the call to ``readDatabaseParameters``:

.. code-block:: python

   {"name": "myapp", "status": "optional"},

This makes it available on the *Admin / Apps* screen. Use ``required`` instead
of ``optional`` if the application must always be installed. For automatic
discovery, the standard configuration also scans Python packages in the
``freppleapps`` directory under ``FREPPLE_APP``.

Build the image, using your chosen frePPLe release:

.. code-block:: bash

   docker build --build-arg FREPPLE_VERSION=10.0.0 -t my-frepple:10.0.0-1 .

Use ``image: my-frepple:10.0.0-1`` in Compose, then recreate the service.
Install optional applications through *Admin / Apps* and verify their
database migrations, static assets and permissions. If the application
adds static files, incorporate ``frepplectl collectstatic --noinput``
in your image build after configuring the app.

Keep the application source, dependency pins, Dockerfile and non-secret
configuration together in version control. A configuration volume from an
older deployment hides configuration baked into the new image; apply the
app registration to that volume as well.

Go-live checklist
-----------------

* Replace the initial ``admin`` password and review users and permissions.
* Verify the production hostname, HTTPS, secure cookies and WebSocket access.
* Confirm persistent storage, database ownership and reporting-role access.
* Review demo scenarios before importing business data.
* Configure email and integration credentials where needed.
* Run a representative plan and check runtime, memory and database performance.
* Configure log rotation, disk monitoring and alerting.
* Complete and test a full backup and restore; see :doc:`maintenance`.
* Record the deployed image version, customizations and recovery procedure.
