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

- A secret ``frepple-secret`` holding the Django ``DJANGO_SECRET_KEY``.

Secret key
----------

A pod's ``/etc/frepple`` is not persisted, so the Django secret key cannot be
stored there — it would be regenerated on every restart, invalidating all
sessions and rotating the Odoo single-sign-on token. ``frepple-deployment.yaml``
therefore reads ``DJANGO_SECRET_KEY`` from the ``frepple-secret`` secret, which
keeps it stable across restarts.

The sample file ships a placeholder value. Replace it with a unique key before
deploying, for example:

.. code-block:: bash

   kubectl create secret generic frepple-secret \
     --from-literal=DJANGO_SECRET_KEY="$(openssl rand -base64 48)"
