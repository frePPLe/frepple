=====================
Hardware requirements
=====================

Frepple models vary largely in size and complexity. A generic estimate of
the hardware you need is too much of an ask.

Nevertheless we can provide some example configurations:

- | **A medium size deployment (< 50000 item locations) running on a single server**

  - Ubuntu 24 linux physical or virtual server.
    Or deploy frepple as a docker container on the operating system of your choice.
  - Application server: 80 GB disk space, 4 cpu cores, 16 GB RAM

- | **A medium size deployment (< 50000 item locations) running with a separated
    application and database server**

  - Servers can be physical servers, virtual servers or containers.
  - Database server: Postgresql, 50 GB disk space, 2 cpu cores, 8 GB RAM
  - Application server: Unbuntu 24, 30 GB disk space, 2 cpu cores, 8 GB RAM
