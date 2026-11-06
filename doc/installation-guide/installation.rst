============
Installation
============

The instructions in the :doc:`quick-start` remain valid for a production deployment.
This page provides some additional steps and considerations to make your installation
secure and performant.

* :ref:`tune-postgresql`
* :ref:`external-postgres`
* :ref:`configure-https`
* :ref:`persistent-data`
* :ref:`configure_smtp`
* :ref:`installation-enterprise`
* :ref:`deploy_customizations`
* :ref:`go_live_checklist`



.. _tune-postgresql:

Tune PostgreSQL
~~~~~~~~~~~~~~~

This is definitely your first step forward.

The default PostgreSQL configuration is only suitable for small databases and
simple queries. Any real-world frepple deployment will be need a database with
4GB or 8GB of memory.

Use `PGTune <https://pgtune.leopard.in.ua/>`_ to get the correct parameters for
the memory size you allocate to the database. In pgtune, choose "data warehouse"
as the workload type.

If you run PostgreSQL locally, apply the recommendations from pgtune by editing
the database configuration file ``postgresql.conf``.

If you are running postgresql as a container, you implement the recommendations
from pgtune in the compose file.

.. code-block:: yaml

   services:
   db:
      image: postgres:18
      restart: always
      shm_size: 4g  # Memory you give as available in pgtune
      environment:
         POSTGRES_PASSWORD: secretpassword
      command: >
         postgres
         -c max_connections=200
         -c shared_buffers=1GB
         -c effective_cache_size=3GB
         -c maintenance_work_mem=512MB
         -c checkpoint_completion_target=0.9
         -c wal_buffers=16MB
         -c default_statistics_target=500
         -c random_page_cost=1.1
         -c effective_io_concurrency=200
         -c work_mem=14198kB
         -c min_wal_size=4GB
         -c max_wal_size=16GB
         -c huge_pages = off
         -c wal_compression=lz4
         -c io_method = io_uring


.. _external-postgres:

Run your own postgresql
-----------------------

Many administrators will prefer to run PostgreSQL locally on the host machine
or as a managed database cloud service (like Amazon RDSor Microsoft Azure). It offers
improved performance, monitoring and maintenance advantages over a deployment as
a container.

To make such a PostgreSQL database accessible to frepple, your need to create
a database role.

.. code-block:: sql

   CREATE ROLE frepple WITH LOGIN PASSWORD 'replace-with-a-random-password'
     CREATEDB CREATEROLE;

You will need to pass the following environment variables to the frepple container:

.. code-block:: yaml

   environment:
     POSTGRES_HOST: database.example.com
     POSTGRES_PORT: "5432"
     POSTGRES_USER: frepple
     POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
     POSTGRES_DB_PREFIX: frepple

The frepple container automatically creates the configured databases
at startup if they don't already exist. If they already exist, the frepple
container takes also care of migrating to database schema to the release you
are deploying.

If you are using the docker compose file from the quick start guide, can now
remove the postgres service from the file. It will looks as follows:

.. code-block:: yaml

   services:
     frepple:
       image: ghcr.io/frepple/frepple-{FREPPLE_EDITION:?Set FREPPLE_EDITION in .env}:${FREPPLE_VERSION:?Set FREPPLE_VERSION in .env}
       restart: unless-stopped
       ports:
         - "127.0.0.1:9000:80"
       environment:
         POSTGRES_HOST: database.example.com
         POSTGRES_PORT: "5432"
         POSTGRES_USER: frepple
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
         POSTGRES_DB_PREFIX: frepple
         FREPPLE_TIME_ZONE: UTC
       volumes:
         - frepple-config:/etc/frepple
         - frepple-data:/var/log/frepple
         - frepple-packages:/usr/share/frepple/python_packages
       logging:
         driver: json-file
         options:
           max-size: "10m"
           max-file: "3"

   volumes:
     frepple-config:
     frepple-data:
     frepple-packages:

If you postgres on the docker host, use the host's IP address, hostname or
 "host.docker.internal" instead of ``localhost`` as the database host.

We recommend using UTF-8 encoding for the database.


.. _configure-https:

Configure HTTPS
---------------

There is a mad world on the internet. Securing your network traffic
is a must for any serious web application.

To configure HTTPS on your frePPLe deployment, you have 2 options.
Either you configure HTTPS directly in the frePPLe container, either
you use a reverse proxy in front of the frePPLe container.

If you want to configure HTTPS directly in the frePPLe container, you
need to customize the configuration of the nginx web server that is
included in the frepple container. You find the configuration file at
``/etc/frepple/nginx.conf``. You'll find enough examples on the web
for configuring HTTPS with nginx.

Terminating HTTPS at a reverse proxy in front of the frePPLe container
is the second approach. The frepple container then only handles
unencrypted traffic from the proxy.
Set these variables on the frePPLe service as shown below. Also edit
the ``/etc/frepple/nginx.conf`` file and change the directive
``proxy_set_header X-Forwarded-Proto $scheme;``
to directive ``proxy_set_header X-Forwarded-Proto https;``.

.. code-block:: yaml

   FREPPLE_CSRF_TRUSTED_ORIGINS: "https://planning.example.com"
   FREPPLE_SECURE_PROXY_SSL_HEADER: "HTTP_X_FORWARDED_PROTO https"
   FREPPLE_SESSION_COOKIE_SECURE: "true"
   FREPPLE_CSRF_COOKIE_SECURE: "true"











REVIEWED UP TO HERE



.. _persistent-data:

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

.. _configure_smtp:

Configure email server
----------------------



.. _deploy_customizations:

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

.. _go_live_checklist:

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
