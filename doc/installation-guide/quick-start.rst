===========
Quick Start
===========

This guide starts a frePPLe and PostgreSQL container on your machine using
Docker Compose.

It is intended for evaluation. For production, continue with :doc:`installation`
to further configuration steps.

This guide assumes you already have installed docker. If not, go back to :doc:`pre-requisites`
to do that first.

Create a deployment directory
-----------------------------

Create a folder where you will configura your deployment.

.. code-block:: bash

   mkdir frepple
   cd frepple

Create a file named ``.env`` with the content as shown below.
A complete installation will configure additional settings in this file. But
for a quick evaluation, these minimal settings are sufficient.

.. code-block:: text

   FREPPLE_EDITION=community    # or enterprise
   FREPPLE_VERSION=latest
   POSTGRES_PASSWORD=replace-with-a-long-random-password

For security, keep this file private: do not put in version control, and
restrict access to it.

Create the Compose file
-----------------------

Save the following as ``compose.yml``:

.. code-block:: yaml

   services:
     frepple:
       image: ghcr.io/frepple/frepple-{FREPPLE_EDITION:?Set FREPPLE_EDITION in .env}:${FREPPLE_VERSION:?Set FREPPLE_VERSION in .env}
       restart: unless-stopped
       ports:
         - "127.0.0.1:9000:80"
       depends_on:
         postgres:
           condition: service_healthy
       environment:
         POSTGRES_HOST: postgres
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

     postgres:
       image: postgres:18
       restart: unless-stopped
       environment:
         POSTGRES_USER: frepple
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
         POSTGRES_DB: postgres
       volumes:
         - postgres-data:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U frepple -d postgres"]
         interval: 5s
         timeout: 3s
         retries: 20
       logging:
         driver: json-file
         options:
           max-size: "10m"
           max-file: "3"

   volumes:
     frepple-config:
     frepple-data:
     frepple-packages:
     postgres-data:

A complete installation will need additional configuration for tuning the database performance,
secure the database credentials, include a licensing file for the Enterprise Edition,
deploy custom application code, etc... But for a quick evaluation, the minimal settings above are sufficient.

Start frepple
-------------

Run the commands below to start the frepple and postgresql containers:

.. code-block:: bash

   docker compose config --quiet
   docker compose pull
   docker compose up -d
   docker compose logs -f frepple

| For the Enterprise Edition, your github user needs to be granted access to
  the Enterprise Edition package by the frepple team.
| You'll need to first run ``docker login ghcr.io --username YOUR_GITHUB_USER``
  and provide a login token.
| The Community Edition does not require github authentication.

On its first start, frepple performs a number of initialization tasks:
- It creates its PostgreSQL databases
- It initializes the tables in the database schema
- It loads 2 example datasets
- Finally, it starts the frepple web application
Allow for some time for this initialization to finish.

The last command in the above snippet follows the frepple logs in real time.
You can omit that command or press Ctrl-C to stop following the logs. This does
not stop the containers.

Verify the installation
------------------------

Point your browser to http://localhost:9000/ and log in with username ``admin`` and password
``admin``. If you are able to log in successfully, the installation is verified.

We recommend changing the default password immediately. Click on the user icon in the upper
right corner to open a preferences screen.

Stop, restart and remove
------------------------

You can stop the services with this command. No data is lost when stopping the services.

.. code-block:: bash

   docker compose stop

You can restart the services later with this command.

.. code-block:: bash

   docker compose start

If you want to completely remove the containers and erase all data, use the
command:

.. code-block:: bash

   docker compose down --volumes

Next steps
----------

* Explore the documentation from the help menu of the application.
* Follow :doc:`installation` for a production ready deployment installation.
