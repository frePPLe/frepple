======================
Advanced Configuration
======================

This page covers scenarios, external authentication and startup customization.
Complete :doc:`installation` first. The ordinary production requirements,
including HTTPS and database configuration, are covered there.

.. _extra_scenarios:
.. _installation-scenarios:

Scenarios and multiple planning models
--------------------------------------

FrePPLe can host multiple planning models in one application:

* What-if scenarios let planners experiment in a copy of the production model.
* Independent models can serve different factories, product lines or planning
  processes, with separate data and permissions.

Each model uses a separate PostgreSQL database. The ``default`` database also
stores shared information such as user identities and scenario configuration.
Include it in every complete environment backup.

Manage scenario slots from the execution screen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The standard configuration reads the number of scenario slots from the
``scenarios`` parameter in the default database. It initially provides three
slots in Community Edition, including ``default``. Use the *Add* and *Delete*
actions in the execution screen to manage available slots, and *Copy* to
populate a free slot.

See :doc:`../user-interface/what-if-scenarios` for the workflow and permissions.
Only delete or release a scenario after checking that its data is no longer
needed.

For example, to copy the main model into a free, configured slot:

.. warning::

   Scenario copying replaces the destination's data. Confirm the source and
   destination and back up any data you need to retain.

.. code-block:: bash

   docker compose exec frepple frepplectl scenario_copy default scenario1

After a copy, the user performing the copy and the superusers from the source
have access to the destination. Review each scenario's active users and
permissions before opening it to planners.

Constrain the number of scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The supplied ``djangosettings.py`` limits the scenario count between
``MIN_NUMBER_OF_SCENARIOS`` (2) and ``MAX_NUMBER_OF_SCENARIOS`` (30).
An administrator can adjust these limits for a controlled deployment.
These limits must be set in the main configuration before ``SCENARIOS`` is
clamped to the permitted range.

The current configuration derives database names and internal service ports
from the prefix and scenario number. For example:

.. list-table::
   :header-rows: 1

   * - Application identifier
     - Database with prefix ``frepple``
     - Internal planning service
   * - ``default``
     - ``frepple0``
     - ``127.0.0.1:8002``
   * - ``scenario1``
     - ``frepple1``
     - ``127.0.0.1:8003``
   * - ``scenario2``
     - ``frepple2``
     - ``127.0.0.1:8004``

Don't copy the old native-installation instructions that replace ``DATABASES``
with arbitrary names: the current settings build this dictionary after
reading the deployment configuration. Custom names, separate database
servers per model or a larger scenario range require coordinated changes to
settings and nginx's ``/ws/`` and ``/svc/`` routing. Prefer separate Compose
deployments when models need independent administration or isolation.

After changing scenario configuration, recreate or restart the application
as appropriate and verify scenario selection, copying and the plan editor.

.. _websocket:

Planning web services and WebSockets
------------------------------------

The Enterprise plan editor uses a per-scenario planning web service and
WebSocket connections. Corporate firewalls and reverse proxies must allow
the WebSocket protocol, even when ordinary application pages work.

The standard nginx configuration routes ``/ws/default/`` and
``/ws/scenarioN/`` to the corresponding internal service, with matching
``/svc/`` routes for HTTP requests. These internal ports don't need to be
published on the Docker host.

To start selected planning web services automatically, set a space-separated
list of scenario identifiers in Compose:

.. code-block:: yaml

   FREPPLE_AUTOSTART_WEBSERVICE: "default scenario1"

Only list configured scenarios with initialized data. To investigate a
connection failure, check application logs, confirm the scenario's service
is running, and check WebSocket upgrades through every proxy layer.

External authentication
-----------------------

FrePPLe includes
`django-allauth <https://docs.allauth.org/en/latest/>`_ for integrating external
identity providers. The bundled ``freppledb.external_auth`` package supplies
frePPLe-specific authentication and account adapters.

The example below outlines an Auth0 OAuth2 integration. Microsoft and other
providers require their corresponding allauth provider and settings. Verify
the configuration against the allauth version bundled with your image.

#. Create an application at the identity provider. Register this callback,
   replacing the hostname:

   .. code-block:: text

      https://planning.example.com/accounts/auth0/login/callback/

   Record the client ID and keep the client secret in protected deployment
   configuration.

#. In ``djangosettings.py``, add these entries to ``APPS`` before
   ``readDatabaseParameters`` is called. Place them ahead of the other
   project-specific applications:

   .. code-block:: python

      {"name": "freppledb.external_auth", "status": "required"},
      {"name": "django.contrib.sites", "status": "required"},
      {"name": "allauth", "status": "required"},
      {"name": "allauth.account", "status": "required"},
      {"name": "allauth.socialaccount", "status": "required"},
      {"name": "allauth.socialaccount.providers.auth0", "status": "required"},

#. Add ``"allauth.account.middleware.AccountMiddleware"`` to ``MIDDLEWARE``
   after Django's authentication middleware. Preserve the existing
   middleware entries.

#. Configure the authentication backends and account adapters. These
   settings can be placed in ``localsettings.py``:

   .. code-block:: python

      AUTHENTICATION_BACKENDS = (
          "freppledb.common.auth.MultiDBBackend",
          "freppledb.external_auth.auth.CustomAuthenticationBackend",
      )
      SITE_ID = 1
      LOGIN_URL = "/accounts/auth0/login/"
      LOGIN_REDIRECT_URL = "/"
      LOGOUT_REDIRECT_URL = "/accounts/logout/"
      ACCOUNT_EMAIL_VERIFICATION = "none"
      SOCIALACCOUNT_AUTO_SIGNUP = True
      SOCIALACCOUNT_ADAPTER = (
          "freppledb.external_auth.auth.CustomAccountAdapter"
      )
      ACCOUNT_ADAPTER = "freppledb.external_auth.auth.CustomAdapter"
      SOCIALACCOUNT_PROVIDERS = {
          "auth0": {"AUTH0_URL": "your-tenant.auth0.com"},
      }
      ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
      DEFAULT_USER_GROUP = "Planner"

   Review account signup and linking policies for your organization. The
   settings above are an example, not a complete identity-security policy.

#. Restart the application so it loads the new apps and applies their
   migrations. Inspect the migration logs, or run the migration explicitly
   in the maintenance window:

   .. code-block:: bash

      docker compose exec frepple frepplectl migrate --noinput

#. In the administration screens, set the site with ID 1 to your public
   hostname. Create a social application for the Auth0 provider, enter the
   client ID and secret, and associate it with that site. Do not define the
   same provider credentials both here and in allauth's settings-based
   application configuration.

#. Create the ``Planner`` group and assign the minimum permissions that new
   users should receive. Do this before allowing external users to sign in.
   The standard frePPLe configuration can grant superuser access to new
   users when no effective default group is configured.

#. Test with a non-administrator account. Verify login, logout, group
   assignment and access to each scenario. Keep a tested administrative
   recovery route while introducing external authentication.

Authentication establishes who the user is; authorization controls what
that user can do. Provider-specific authorization rules may require a custom
adapter in a derived image.

Use the HTTPS configuration in :ref:`installation-https`. Don't relax
frame policies or same-site cookies simply because OAuth is enabled. If
embedding frePPLe in another application requires cross-site cookies,
review those settings explicitly and require secure cookies over HTTPS.

Startup customization
---------------------

The container entrypoint normally initializes the database and starts
supervisor, which manages nginx, the application server and the scheduler.

For additional startup actions, place executable scripts in
``/etc/frepple/entrypoint.d``. The entrypoint executes them with
``run-parts`` before supervisor starts.

* Use names accepted by ``run-parts``, for example ``10-custom-setup``
  rather than ``10-custom-setup.sh``.
* Scripts run as the unprivileged ``frepple`` user. They must be executable
  and must not require root access.
* Make scripts safe to run on every start. A failing script prevents normal
  startup; report failures rather than silently ignoring them.
* These hooks run after the built-in database initialization. They cannot
  replace configuration needed for that initialization.

Alternatively, pass a command to run instead of supervisor:

.. warning::

   A command passed to the container still goes through the normal entrypoint,
   including database creation and migrations when a database connection is
   configured. The custom startup hooks are skipped in this mode.

   For a command that must bypass initialization, explicitly override the
   entrypoint. For commands against an already-running installation, prefer
   ``docker compose exec``.

.. code-block:: bash

   docker compose run --rm --no-deps frepple ls /etc/frepple

Kubernetes and other orchestrators
----------------------------------

The same container can be deployed with an orchestrator, provided database
initialization, persistent storage, credentials, ingress and the singleton
scheduler are handled deliberately.

The repository contains
`example Kubernetes manifests <https://github.com/frePPLe/frepple/tree/master/contrib/kubernetes>`_.
They are a starting point, not an equivalent production deployment guide:
review their image tags, storage sizing, credentials and mounts against the
current :doc:`reference`. In particular, legacy Apache mounts do not apply
to the current nginx-based image. Don't apply these examples unchanged to a
production cluster.
