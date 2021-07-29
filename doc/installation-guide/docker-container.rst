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

The container can easily be pulled from the github packages repository:

.. code-block:: none

   docker pull ghcr.io/frepple/frepple:latest

| The container includes the frePPLe planning software, plus a web server. 
| It does NOT include the required PostgreSQL database, which needs to provided 
  as a separate service: see below.

The image can be extended and customized using the following:

* The container exposes **ports** 80 and 443 for HTTP and HTTPS access.

* The following **environment variables** configure the access to the PostgreSQL database:

    * | POSTGRES_HOST:
      | Required. Points to IP address or name of the host running the database.

    * | POSTGRES_PORT:
      | TCP port of the database. Defaults to "5432".

    * | POSTGRES_USER:
      | Database role or user. Defaults to "frepple".

    * | POSTGRES_PASSWORD:
      | Password for the database role or user. Defaults to "frepple".

* The following **volumes** let you deploy custom code and license files into the container:

    * | /etc/frepple: 
      | Contains the main configuration file djangosettings.py and the
        license file license.xml (for the Enterprise Edition).

    * | /var/log/frepple: 
      | Contains log files of the application.
    
    * | /var/log/apache2:
      | Log files of the web server.

    * | /etc/apache2:
      | Configuration files of the web server.

* The **entry point** of the container can be customized by placing files in the folder
  /etc/frepple/entrypoint.d

* Custom code can be added to the container by **inheriting from this image**. A section
  below illustrates how this is done.

********************************************
Deployment with external PostgreSQL database
********************************************

The example below creates a container that is using the postgres database installed on
the docker host server.
The container is called frepple_local, and you can access it with your browser 
on the URL http://localhost:9000/

.. code-block:: none

   docker run \
     -e POSTGRES_HOST=host.docker.internal \
     -e POSTGRES_PORT=5432 \
     -e POSTGRES_USER=frepple \
     -e POSTGRES_PASSWORD=frepple \
     --name frepple_local \
     --publish 9000:80 \ 
     --detach \
     frepple:latest 

******************************
Deployment with docker compose
******************************

Here is a sample docker-compose file that defines 2 containers: 1) a postgres container to run the database
and 2) a frepple web application server.

You access the application with your browser on the URL http://localhost:9000/

The frepple log and configuration files are put in volumes (which allows to reuse
them between different releases of the frepple image).

.. code-block:: none

  services:

    frepple:
      image: "frepple:latest"
      container_name: frepple-webserver
      ports:
        - 9000:80
      depends_on:
        - frepple-postgres
      networks:
        - backend
      volumes:
        - log-apache:/var/log/apache2
        - log-frepple:/var/log/frepple
        - config-frepple:/etc/frepple
        - config-apache:/etc/apache2
      environment:
        POSTGRES_HOST: frepple-postgres
        POSTGRES_PORT: 5432
        POSTGRES_USER: frepple
        POSTGRES_PASSWORD: frepple

    frepple-postgres:
      image: "postgres:13"
      container_name: frepple-postgres
      networks:
        - backend
      environment:
        POSTGRES_PASSWORD: frepple
        POSTGRES_DB: frepple
        POSTGRES_USER: frepple

  volumes:
    log-apache:
    log-frepple:
    config-frepple:
    config-apache:
    data-postgres:

  networks:
    backend:

**************************
Deployment with Kubernetes
**************************

Todo

*************************************
Deployment with custom extension apps
*************************************

Todo

******************************************
Running frepplectl commands on a container
******************************************

It is possible to execute a frepplectl command (or any linux command) 
on a running container. 

.. code-block:: none

   docker exec -it <container name> frepplectl importfromfolder

   docker exec -it <container name> /bin/bash
