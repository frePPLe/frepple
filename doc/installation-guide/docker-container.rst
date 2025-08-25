================
Docker container
================

* `Basic concepts`_
* `Basic installation`_
* `Deployment of the Enterprise Edition`_
* `Deployment with custom extension apps`_

**************
Basic concepts
**************

* | Container:
  | A container is an isolated environment where you can run applications.
  | This is very useful for software companies, because it allows them to focus on
  | the software development and not on maintaining different versions of the software
  | for different operating systems (and operating system versions).

* | Image (in a Docker context):
  | A Docker image is a package that includes everything you need to run your application.
  | The image is defined in a template called dockerfile. This template defines the Operating System,
  | environment variables used by applications, shared folders with the system where Docker is running, ...

* | Docker:
  | Docker is the application used to launch/run the containers. It reads a file that defines
  | the container (OS, installed applications, environment variables, volumes, ...),
  | and builds an image () according to that definition. Docker then launches/runs a container
  | with that image.

* | Docker-compose:
  | Docker-compose is a level above Docker, it is an application that allows you to launch multiple
  | (usually related to eachother) Docker containers.
  | In our instructions you can have a docker-compose script that launces a Frepple container and a
  | PostgreSQL database container (:doc:`advanced/docker-compose`).

* | Kubernettes:
  | Kuberbetes is a level above Docker-compose, it is a container orchestrator. It is used to separated
  | and manage containers distributed across multiple servers.
  | In our instructions you can find a kuberbetes script that launces a Frepple container and a
  | PostgreSQL database container (:doc:`advanced/kubernetes`).

Use one of the following command to bring the frePPLe image to your local
docker repository:

******************
Basic installation
******************

The first step towards a working frePPLe application is the database installation.
Frepple is developed and tested using PostgreSQL, other SQL database engines may be
used but it is up to the user to support them.

To install PostgreSQL just `download <https://www.postgresql.org/download/>`_ and follow the instructions relevant to your Operating System.

There is also the more advanced option to also deploy PostgreSQL in a container with :doc:`advanced/docker-compose`.

============================================
Deployment with external PostgreSQL database
============================================

The example below creates a container that is using the PostgreSQL database installed on
the Docker host server.
The container is called frepple-community-local, and you can access it with your browser
on the URL http://localhost:9000/

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

* Custom code can be added (:doc:`advanced/custom-aoo`_) to the container by **inheriting from this image**. A section
  below illustrates how this is done.

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
        FREPPLE_AUTOSTART_WEBSERVICE: ""  # List of scenarios for which to automatically start the web service, separated by space

************************************
Deployment of the Enterprise Edition
************************************

The Enterprise Edition needs a license file to be copied into the container.
This is handled by inheriting from the frePPLe image.

Create a new folder and copy the license file intofile:///mnt/dev/frepple-enterprise-dev/build/doc/_build/html/ it. Also create
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

*******************************
Running commands on a container
*******************************

It is possible to execute a frepplectl command (or any linux command)
on a running container.

.. code-block:: bash

   # Run a single command in the container
   docker exec <container name> frepplectl importfromfolder

   # Run an interactive bash shell inside the container
   docker exec -it <container name> /bin/bash


*************************************
Deployment with custom extension apps
*************************************

Extending the container with your own customizations is simple by inheriting from the frePPLe
image. Here is a an example dockerfile that adds a new frePPLe app (coded as a Python package):

.. code-block:: docker

   FROM ghcr.io/frepple/frepple-enterprise:latest

   # Copy the custom app. Apps in this folder are automatically detected
   # and you can install them from the admin/apps screen.
   # Please note that the python version in the instruction bellow could be different
   COPY my-app /usr/share/frepple/venv/lib/python3.12/site-packages/

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
