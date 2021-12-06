================
Docker container
================

* `Basic installation`_
* `Deployment with external PostgreSQL database`_
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

   # Community Edition
   docker pull ghcr.io/frepple/frepple-community:latest

   # Enterprise Edition: download image from portal and load into your registry
   docker load --input frepple*.tar

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

.. code-block:: none

   docker run \
     -e POSTGRES_HOST=host.docker.internal \
     -e POSTGRES_PORT=5432 \
     -e POSTGRES_USER=frepple \
     -e POSTGRES_PASSWORD=frepple \
     --name frepple-community-local \
     --publish 9000:80 \
     --detach \
     frepple-community:latest

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
      image: "frepple-community:latest"
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
        POSTGRES_HOST: frepple-community-postgres
        POSTGRES_PORT: 5432
        POSTGRES_USER: frepple
        POSTGRES_PASSWORD: frepple

    frepple-community-postgres:
      image: "postgres:13"
      container_name: frepple-community-postgres
      networks:
        - backend
      environment:
        POSTGRES_PASSWORD: frepple
        POSTGRES_DB: frepple
        POSTGRES_USER: frepple

  volumes:
    log-apache-community:
    log-frepple-community:
    config-frepple-community:

  networks:
    backend:

**************************
Deployment with Kubernetes
**************************

Todo

*************************************
Deployment with custom extension apps
*************************************

Extending the container with your customizations is simple by inheriting from the frePPLe
image. Here is a an example dockerfile that adds a new frePPLe app (coded as a Python package):

.. code-block:: none

   FROM frepple-enterprise:latest

   COPY my-requirements.txt /
   COPY my-python-package /

   # Add the license key for the Enterprise Edition to the container
   COPY license.xml /etc/frepple

   # Install python dependencies and package
   RUN python3 -m pip install -r my-requirements.txt && \
     python3 my-python-package/setup.py install

   # Update the djangosettings.py configuration file with extra settings
   echo "MYAPPSETTING=True" >> /etc/frepple/djangosettings.py

******************************************
Running frepplectl commands on a container
******************************************

It is possible to execute a frepplectl command (or any linux command)
on a running container.

.. code-block:: none

   docker exec -it <container name> frepplectl importfromfolder

   docker exec -it <container name> /bin/bash
