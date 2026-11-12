============
Installation
============

The instructions in the :doc:`quick-start` remain valid for a production deployment.
This page provides some additional steps and considerations to make your installation
secure, performant and production-ready.

* :ref:`reset-admin-password`
* :ref:`tune-postgresql`
* :ref:`external-postgres`
* :ref:`configure-https`
* :ref:`configure-smtp`
* :ref:`installation-enterprise`
* :ref:`deploy-custom-addons`
* :ref:`custom_image`


.. _reset-admin-password:

Reset the admin password
~~~~~~~~~~~~~~~~~~~~~~~~

The default installation creates the "admin" user with the default password "admin".

Log in as the admin user, and open the preferences form (click on the user icon
in the top right corner). Change that password right away.


.. _tune-postgresql:

Tune PostgreSQL
~~~~~~~~~~~~~~~

Start by tuning PostgreSQL for your deployment.

The default PostgreSQL configuration is only suitable for small databases and
simple queries. Any real-world frepple deployment will need a more powerful
database with 4GB to 8GB memory.

Use `PGTune <https://pgtune.leopard.in.ua/>`_ to get the correct parameters for
the memory size you give to the database. Choose "data warehouse" as the workload
type in PGTune.

If you run PostgreSQL locally, apply the recommendations from PGTune by editing
the database configuration file ``postgresql.conf``.

If you are running PostgreSQL as a container, you add the recommendations
from PGTune in the compose file, as shown below.

.. code-block:: yaml

   services:
   db:
      image: postgres:18
      restart: always
      shm_size: 4g  # Memory you give as available in PGTune
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

Running your own PostgreSQL
---------------------------

Many administrators will prefer to run PostgreSQL locally on the host machine
or as a managed database cloud service (like Amazon RDS, Google Cloud SQL, or
Microsoft Azure). It offers improved performance, monitoring and maintenance
advantages over a deployment as a container.

To make such a PostgreSQL database accessible to frepple, you need to create
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
container will automatically migrate the database schema to the frepple version
of your image.

If you are using the docker compose file from the quick start guide, you can now
remove the PostgreSQL service from the file. It will look as follows:

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
 ``host.docker.internal`` instead of ``localhost`` as the database host. That's
 because ``localhost`` would refer to the container itself, not the host machine.

We highly recommend using UTF-8 encoding for the database.


.. _configure-https:

Configure HTTPS
---------------

It's is a mad world on the internet. Securing your network traffic
is a must for any serious web application.

To configure HTTPS on your frePPLe deployment, you have 2 options.
Either you configure HTTPS directly in the frePPLe container, or
you use a reverse proxy in front of the frePPLe container.

If you want to configure HTTPS directly in the frePPLe container, you
need to customize the configuration of the nginx web server that is
included in the frepple container. You find the configuration file at
``/etc/frepple/nginx.conf``. You'll find enough documentation on the web
for configuring HTTPS with nginx.

Terminating HTTPS at a reverse proxy in front of the frePPLe container
is the second approach. The frepple container then only handles
unencrypted traffic from the proxy.
Pass the extra environment variables on the frepple service as shown below.

.. code-block:: yaml

   FREPPLE_CSRF_TRUSTED_ORIGINS: "https://planning.example.com"
   FREPPLE_SECURE_PROXY_SSL_HEADER: "HTTP_X_FORWARDED_PROTO https"
   FREPPLE_SESSION_COOKIE_SECURE: "true"
   FREPPLE_CSRF_COOKIE_SECURE: "true"


.. _configure-smtp:

Configure email
---------------

Frepple can send users emails: eg to reset passwords, notify about failed
tasks, email reports, etc...

This requires the following settings to be passed to the frepple service.
More advanced email settings are available in the
`Django documentation <https://docs.djangoproject.com/en/5.2/topics/email/#smtp-backend>`_.

.. code-block:: yaml

   EMAIL_USE_TLS = True
   DEFAULT_FROM_EMAIL = "frepple <no-reply@yourdomain.com>"
   SERVER_EMAIL = "no-reply@frepple.com"
   EMAIL_HOST = "your-smtp-server"
   EMAIL_PORT = 587
   EMAIL_HOST_USER = "your-smtp-user"
   EMAIL_HOST_PASSWORD = "your-smtp-password"
   EMAIL_URL_PREFIX = "https://yourdomain.com"


.. _installation-enterprise:

Deploy the Enterprise Edition
-----------------------------

Installing the Enterprise Edition is identical to installing the Community Edition,
except for the image and the license handling.

First, the download of the container image needs to be authenticated.

.. code-block:: bash

   docker login ghcr.io --username YOUR_GITHUB_USER
   # Enter your GitHub password or personal access token when prompted

   docker pull ghcr.io/frepple/frepple-enterprise:latest

Second, place the license you received from the frepple team as the
file ``etc/frepple/license.xml`` in your container. The files is persisted
in the docker volume ``frepple-config``, so you need to run this
command on once.

.. code-block:: bash

   docker cp license.xml <container_name_or_id>:/etc/frepple/license.xml


.. _deploy-custom-addons:

Deploy custom addons
--------------------

Many customers use custom addons to extend frepple's functionality.

The development of custom addons involves creating Python packages that
follow frepple's addon structure. This development is described in detail in the
developer guide.

You deploy such custom addon by copying them into the container
folder /usr/share/frepple/python_packages. Addons in this folder
are automatically detected, and can be installed from the *Admin / Apps* screen.

.. code-block:: bash

   docker cp myaddon/ <container_name_or_id>:/usr/share/frepple/python_packages/myaddon/


.. _custom_image:

Make your own derived image
---------------------------

If your deployment requires more complex customizations, the recommended approach is
to build a derived image that includes your custom addons. You create your own Dockerfile
that starts from the frepple base image, and then adds whatever you like.

Here is an example ``Dockerfile``:

.. code-block:: docker

   FROM frepple-enterprise:latest

   # Install extra ubuntu packages
   USER root
   RUN apt update && \
      apt install -y any_ubuntu_package ca-certificates && \
   USER frepple

   # Copy license file and other configuration files
   COPY license.xml /etc/frepple
   COPY my_configuration_file /etc/frepple

   # Copy a custom frepple addon
   COPY my_addon /usr/share/frepple/python_packages/my_addon

   # Environment settings
   ENV POSTGRES_HOST    "my_postgres_host"
   ENV POSTGRES_PORT    "5432"
   ENV POSTGRES_USER     "my_postgres_user"
   ENV POSTGRES_PASSWORD   "my_postgres_password"
   ENV POSTGRES_DBNAME    "my_postgres_database"

Build the image, using your chosen frePPLe release:

.. code-block:: bash

   docker build -t my-frepple:1.0.0 .

Finally, you can use your custom image in your Compose deployment.

Keep the application source and dockerfile and non-secret
configuration managed in version control.
