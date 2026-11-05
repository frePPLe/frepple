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

- Persistent volumes to store the web server logs (50MB), the application logs (100MB)
  and the postgresql data (1GB).

- A network policy to keep the connection between frepple and its postgres database private.
