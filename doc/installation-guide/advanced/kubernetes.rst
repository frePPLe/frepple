==========================
Deployment with Kubernetes
==========================

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

- Persistent volumes to store the web server logs (50MB), the application logs (100MB),
  the frepple configuration in ``/etc/frepple`` (50MB) and the postgresql data (1GB).

- A network policy to keep the connection between frepple and its postgres database private.

frepple stores its runtime configuration in ``/etc/frepple/djangosettings.py``: the
Django secret key, the list of installed apps, the number of scenarios and some display
settings are all written to this file as you use the application. The deployment therefore
mounts ``/etc/frepple`` on a persistent volume, seeded from the image on the first start by
an init container, so that this configuration survives pod restarts - the same way the
docker-compose deployment persists it on a named volume. Without it the directory resets to
the image defaults on every restart: a new secret key is generated (invalidating sessions),
and installed apps and scenario settings are lost.

The volume is seeded only once. After upgrading to a newer frepple image, any new default
settings shipped in the image are not copied over an existing ``djangosettings.py``; review
and apply such changes manually after an upgrade.
