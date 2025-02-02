================
Docker container
================

* `Basic installation`_
* `Deployment with external PostgreSQL database`_
* `Deployment of the Enterprise Edition`_
* `Deployment with docker compose`_
* `Deployment with Kubernetes`_
* `Deployment with custom extension apps`_
* `Running frepplectl commands on a container`_

******************
Basic installation
******************

Use one of the following command to bring the frePPLe image to your local
docker repository:

.. code-block:: none

   # Login into github with your access token
   docker login ghcr.io --username <github_user>

   # Get the Community Edition
   docker pull ghcr.io/frepple/frepple-community:latest

   # Get the Enterprise Edition
   docker pull ghcr.io/frepple/frepple-enterprise:latest

| The container includes the frePPLe planning software, plus a web server.
| It does NOT include the required PostgreSQL database, which needs to provided
  as a separate service: see below.

The image can be extended and customized using the following:

* The container exposes **port** 80 for HTTP access.

* The following **environment variables** configure the access to the PostgreSQL database:

    * | POSTGRES_HOST:
      | Required. Points to IP address or name of the host running the database.

    * | POSTGRES_PORT:
      | TCP port of the database. Defaults to "5432".

    * | POSTGRES_USER:
      | Database role or user. Defaults to "frepple".

    * | POSTGRES_PASSWORD:
      | Password for the database role or user. Defaults to "frepple".

    * | POSTGRES_DBNAME:
      | Prefix to use for the database name.
      | The default database names are "frepple", "scenario1", "scenario2", "scenario3".
      | If this argument is passed as "X", the database names will be "X0", "X1", "X2" and "X3".

* The following **volumes** let you access all logs, configuration and license files:

    * | /etc/frepple:
      | Contains the main configuration file djangosettings.py and the
        license file license.xml (for the Enterprise Edition).

    * | /var/log/frepple:
      | Contains log files of the application.

    * | /var/log/apache2:
      | Log files of the web server.

* The **entry point** of the container can be customized by placing files in the folder
  /etc/frepple/entrypoint.d

* Custom code can be added to the container by **inheriting from this image**. A section
  below illustrates how this is done.

********************************************
Deployment with external PostgreSQL database
********************************************

The example below creates a container that is using the PostgreSQL database installed on
the Docker host server.
The container is called frepple-community-local, and you can access it with your browser
on the URL http://localhost:9000/

.. code-block:: bash

   docker run \
     -e POSTGRES_HOST=host.docker.internal \
     -e POSTGRES_PORT=5432 \
     -e POSTGRES_USER=frepple \
     -e POSTGRES_PASSWORD=frepple \
     -e POSTGRES_DBNAME=freppledb \
     --name frepple-community-local \
     --publish 9000:80 \
     --restart always \
     --detach \
     ghcr.io/frepple/frepple-community:latest

The following environment variables can be set to configure your container:

.. code-block:: bash

        POSTGRES_HOST: ""
        POSTGRES_PORT: 5432
        POSTGRES_USER: "frepple"
        POSTGRES_PASSWORD: "frepple"
        FREPPLE_DATE_STYLE: "year-month-day"
        FREPPLE_DATE_STYLE_WITH_HOURS: "false"
        FREPPLE_TIME_ZONE: "UTC"
        FREPPLE_THEMES: "earth grass lemon odoo openbravo orange snow strawberry water"
        FREPPLE_DEFAULT_THEME: "earth"
        FREPPLE_EMAIL_USE_TLS: "true"
        FREPPLE_DEFAULT_FROM_EMAIL: "your_email@domain.com"
        FREPPLE_SERVER_EMAIL: "your_email@domain.com"
        FREPPLE_EMAIL_HOST_USER: "your_email@domain.com"
        FREPPLE_EMAIL_HOST_PASSWORD: "frePPLeIsTheBest"
        FREPPLE_EMAIL_HOST: ""
        FREPPLE_EMAIL_PORT: 25
        FREPPLE_CONTENT_SECURITY_POLICY: "frame-ancestors 'self'"
        FREPPLE_X_FRAME_OPTIONS: "SAMEORIGIN"
        FREPPLE_CSRF_TRUSTED_ORIGINS: ""
        FREPPLE_SECURE_PROXY_SSL_HEADER: ""
        FREPPLE_SESSION_COOKIE_SECURE: "false"
        FREPPLE_CSRF_COOKIE_SAMESITE: "lax"
        FREPPLE_FTP_PROTOCOL: "SFTP"
        FREPPLE_FTP_HOST: ""
        FREPPLE_FTP_PORT: 22
        FREPPLE_FTP_USER: ""
        FREPPLE_FTP_PASSWORD: ""

************************************
Deployment of the Enterprise Edition
************************************

The Enterprise Edition needs a license file to be copied into the container.
This is handled by inheriting from the frePPLe image.

Create a new folder and copy the license file into it. Also create
a dockerfile in it with the following content:

.. code-block:: docker

   FROM ghcr.io/frepple/frepple-enterprise:latest

   # Add the license key for the Enterprise Edition to the container
   COPY license.xml /etc/frepple

Next, you build and your container with commands like:

.. code-block:: bash

   docker build my_frepple -t -my_frepple

   docker run \
     -e POSTGRES_HOST=host.docker.internal \
     -e POSTGRES_PORT=5432 \
     -e POSTGRES_USER=frepple \
     -e POSTGRES_PASSWORD=frepple \
     -e POSTGRES_DBNAME=freppledb \
     --name my_frepple \
     --publish 9000:80 \
     --restart always \
     --detach \
     my_frepple

The folder with the license file and the dockerfile are typically put under
version control. A section below shows how this structure can be extended
with custom apps or configurations.

******************************
Deployment with docker compose
******************************

Here is a sample docker-compose file that defines 2 containers: 1) a postgres container
to run the database and 2) a frepple web application server.

You access the application with your browser on the URL http://localhost:9000/

The frepple log and configuration files are put in volumes (which allows to reuse
them between different releases of the frepple image).

Note that the postgres database container comes with default settings. For production
use you should update the configuration with the pgtune recommendations from
https://pgtune.leopard.in.ua/ (use "data warehouse" as application type and also assure
the max_connections setting is moved from the default 100 to eg 400).

.. code-block:: none

  services:

    frepple:
      image: "ghcr.io/frepple/frepple-community:latest"
      container_name: frepple-community-webserver
      ports:
        - 9000:80
      depends_on:
        - frepple-community-postgres
      networks:
        - backend
      volumes:
        - log-apache-community:/var/log/apache2
        - log-frepple-community:/var/log/frepple
        - config-frepple-community:/etc/frepple
      environment:
        POSTGRES_HOST: "frepple-community-postgres"
        POSTGRES_PORT: 5432
        POSTGRES_USER: "frepple"
        POSTGRES_PASSWORD: "frepple"
        FREPPLE_DATE_STYLE: "year-month-day"
        FREPPLE_DATE_STYLE_WITH_HOURS: "false"
        FREPPLE_TIME_ZONE: "UTC"
        FREPPLE_THEMES: "earth grass lemon odoo openbravo orange snow strawberry water"
        FREPPLE_DEFAULT_THEME: "earth"
        FREPPLE_EMAIL_USE_TLS: "true"
        FREPPLE_DEFAULT_FROM_EMAIL: "your_email@domain.com"
        FREPPLE_SERVER_EMAIL: "your_email@domain.com"
        FREPPLE_EMAIL_HOST_USER: "your_email@domain.com"
        FREPPLE_EMAIL_HOST_PASSWORD: "frePPLeIsTheBest"
        FREPPLE_EMAIL_HOST: ""
        FREPPLE_EMAIL_PORT: 25
        FREPPLE_CONTENT_SECURITY_POLICY: "frame-ancestors 'self'"
        FREPPLE_X_FRAME_OPTIONS: "SAMEORIGIN"
        FREPPLE_CSRF_TRUSTED_ORIGINS: ""
        FREPPLE_SECURE_PROXY_SSL_HEADER: ""
        FREPPLE_SESSION_COOKIE_SECURE: "false"
        FREPPLE_CSRF_COOKIE_SAMESITE: "lax"
        FREPPLE_FTP_PROTOCOL: "SFTP"
        FREPPLE_FTP_HOST: ""
        FREPPLE_FTP_PORT: 22
        FREPPLE_FTP_USER: ""
        FREPPLE_FTP_PASSWORD: ""

    frepple-community-postgres:
      image: "postgres:13"
      container_name: frepple-community-postgres
      networks:
        - backend
      environment:
        POSTGRES_PASSWORD: frepple
        POSTGRES_DB: frepple
        POSTGRES_USER: frepple
        POSTGRES_DBNAME: frepple

  volumes:
    log-apache-community:
    log-frepple-community:
    config-frepple-community:

  networks:
    backend:

**************************
Deployment with Kubernetes
**************************

A set of Kubernetes configuration files is available on
https://github.com/frePPLe/frepple/tree/master/contrib/kubernetes

Create a copy of these files on your machine. Then run the following commands
to deploy frepple.

.. code-block:: bash

   kubectl apply -f frepple-deployment.yaml,frepple-postgres-deployment.yaml,frepple-networkpolicy.yaml

The following resources are then defined in your cluster:

- A frepple service that runs the frepple planning engine and an Apache web server.
  It exposes port 80 for HTTP access to the application.

- A postgresql service to store the frepple data.

- Persistent volumes to store the web server logs (50MB), the application logs (100MB)
  and the postgresql data (1GB).

- A network policy to keep the connection between frepple and its postgres database private.

*************************************
Deployment with custom extension apps
*************************************

Extending the container with your customizations is simple by inheriting from the frePPLe
image. Here is a an example dockerfile that adds a new frePPLe app (coded as a Python package):

.. code-block:: docker

   FROM ghcr.io/frepple/frepple-enterprise:latest

   # Copy the custom app. Apps in this folder are automatically detected
   # and you can install them from the admin/apps screen.
   COPY my-app /usr/share/frepple/venv/lib/python3.8/site-packages/

   # Add the license key for the Enterprise Edition to the container
   COPY license.xml /etc/frepple

   # Install extra python packages
   COPY requirements.txt /
   RUN python3 -m pip install -r requirements.txt

   # Update the djangosettings.py configuration file with extra settings
   RUN echo "MYAPPSETTING=True" >> /etc/frepple/djangosettings.py

The folder with all customizations is typically put under
version control. This allows a clear process for maintaining your custom code
and upgrading to new frePPLe releases.

******************************************
Running frepplectl commands on a container
******************************************

It is possible to execute a frepplectl command (or any linux command)
on a running container.

.. code-block:: bash

   docker exec -it <container name> frepplectl importfromfolder

   docker exec -it <container name> /bin/bash
