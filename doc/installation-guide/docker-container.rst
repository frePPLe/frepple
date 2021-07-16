================
Docker container
================

* `Basic installation`_
* `Deployment with external PostgreSQL database`_
* `Deployment with docker compose`_
* `Deployment with Kubernetes`_
* `Deployment with custom extension apps`_

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

    * | POSTGRESQL_HOST:
      | Required. Points to IP address or name of the host running the database.

    * | POSTGRESQL_PORT:
      | TCP port of the database. Defaults to "5432".

    * | POSTGRESQL_USER:
      | Database role or user. Defaults to "frepple".

    * | POSTGRESQL_PASSWORD:
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

Todo

******************************
Deployment with docker compose
******************************

Todo

**************************
Deployment with Kubernetes
**************************

Todo

*************************************
Deployment with custom extension apps
*************************************

Todo