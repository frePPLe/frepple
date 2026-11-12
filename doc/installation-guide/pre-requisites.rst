==============
Pre-requisites
==============

Before you start installing the software, let's review what you need to know and have in place.

* :ref:`container-platform`
* :ref:`postgresql-database`
* :ref:`hardware-sizing`
* :ref:`edition-and-licensing`


.. _container-platform:

Container platform
------------------

FrePPLe is distributed as a container image.

You will need to install a container platform such as Docker on your host. You can run
frepple on any operating system, as long as it runs on amd64 or arm64 architecture.

Install Docker Engine and the Docker Compose plugin on your server, or Docker
Desktop on your workstation. Follow the
`Docker installation instructions <https://docs.docker.com/get-started/get-docker/>`_
for your operating system.

If you are new to container platforms, here are some introductory resources:

* `Docker website <https://www.docker.com/>`_
* `IBM containerization overview <https://www.ibm.com/think/topics/containerization>`_
* `Docker getting started <https://docs.docker.com/get-started/>`_
* `Docker Compose overview <https://docs.docker.com/compose/>`_

.. _postgresql-database:

PostgreSQL database
-------------------

Frepple uses a PostgreSQL relational database to store its data.
Use PostgreSQL 18, 17, 16 or 15 in this order of preference.

You can either:

* | Run PostgreSQL in a separate container on the Docker host.
  | This is the approach used in this quick start (since it doesn't require any
    separate installation)

* | You can install a postgreSQL server and let the frepple container connect to it.
  | If you go for this option, prepare a database user for frepple and grant it
    permissions to create databases.

If you are new to PostgreSQL, here are some introductory resources.

* `PostgreSQL website <https://www.postgresql.org/>`_
* `PostgreSQL documentation <https://www.postgresql.org/docs/>`_

.. _hardware-sizing:

Hardware sizing
---------------

A midrange laptop is more than sufficient for a small to medium-sized installation.

Below are some example configurations for a medium-sized deployment.
Hardware requirements are a complex topic and depend on several factors, so this
is meant as a guideline only.

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Deployment
     - CPU cores
     - RAM
     - Disk space
   * - Application and database on one server
     - 4
     - 16 GB
     - 80 GB
   * - Separate application server
     - 2
     - 8 GB
     - 30 GB
   * - Separate database server
     - 2
     - 8 GB
     - 50 GB

.. _edition-and-licensing:

Edition and licensing
---------------------

The Community Edition image is freely available at ghcr.io/frepple/frepple-community.

| The Enterprise Edition image is available at ghcr.io/frepple/frepple-enterprise.
| To use it you will need to create a GitHub account and request access to the image
  from the frepple team. The frepple team will also provide you a license key you
  will need to copy into your container.
