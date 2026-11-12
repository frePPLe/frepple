======================
Advanced Configuration
======================

The :doc:`installation` page covers the key installation steps.
On this page we cover some advanced configuration topics that only apply to
specific deployments.

* :ref:`external_auth`
* :ref:`kubernetes`


.. _external_auth:

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


.. _kubernetes:

Kubernetes and other orchestrators
----------------------------------

Throughout this guide we used docker compose to define and run the frePPLe container.
Many companies use Kubernetes or other orchestrators to manage containerized
applications at scale.

The frepple repository contains
`example Kubernetes manifests <https://github.com/frePPLe/frepple/tree/master/contrib/kubernetes>`_.
This kubernete configuration is not actively maintained and is a bit dated. We'll be happy to
include your contributions to improve it.
