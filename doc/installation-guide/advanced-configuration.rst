======================
Advanced configuration
======================

The installation guide covers a standard installation. But not all installations
are standard. You may have specific requirements that require additional
configuration to deploy frepple.

This page captures some common additional configuration tasks.

You have a topic you'd like to see covered on this page? Let us know on
https://github.com/frePPLe/frepple/discussions or https://github.com/frePPLe/frepple/issues

* :ref:`https`
* :ref:`extra_scenarios`
* :ref:`websocket`
* :ref:`proxy`
* :ref:`moveserver`
* :ref:`external_authentication`


.. _https:

Enable https encryption for all web traffic
-------------------------------------------

The standard installation uses unencrypted web traffic over HTTP. The IT policy
of many companies requires encrypting all web traffic of all web applications
over HTTPS.

#. | Activate HTTPS encryption on your web server.
   | FrePPLe uses a standard `Apache <https://httpd.apache.org/>`_ web server. 
     A google search will provide a lot of info on the required configuration steps.

   .. code-block:: bash

      a2enmod ssl       # Enable the ssl module
      a2ensite default-ssl    # Configure the module. Adjust this step to use your own ssl certificate!

   | You can also use a proxy server in front of frepple. Typically you will do
     the HTTPS encryption on the proxy server then, and you can thus skip this first step.

#. | Update the settings SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE to true. You do this 
     by editing the /etc/frepple/djangosettings.py file or by setting these variables in
     a docker deployment.
   | This step is required regardless of where the HTTPS encryption is done.

.. _extra_scenarios:

Add extra scenarios
-------------------

Frepple by default is configured for 3 (Community and Enterprise Editions)
or 6 (Cloud Edition) scenario databases.

You can change the configuration to include a different amount of database
with the following steps:

#. | Update the DATABASES section of the /etc/frepple/djangosettings.py file.
     Each scenario is identified by a unique key in this dictionary.
   | Note that the first database MUST have 'default' as key.
   | Normally all database are on the same PostgreSQL instance and the USER,
     PASSWORD, HOST and PORT are the same for all scenarios. The database name
     will be different for each scenario.
   | The FREPPLE_PORT must be unique for each scenario database. It'll be
     used in the next step.

#. | The apache configuration file /etc/apache2/sites-enabled/z_frepple.conf
     needs a section as shown below for each scenario.
   | Edit the file, and replace SCENARIO_KEY and FREPPLE_PORT with the values
     you used in the /etc/frepple/djangosettings.py file.

   .. code-block:: bash

       Proxypass "/ws/SCENARIO_KEY/" "ws://localhost:FREPPLE_PORT>/ws/scenario2/" retry=0
       Proxypass "/svc/SCENARIO_KEY/" "http://localhost:FREPPLE_PORT/" retry=0

#. | A database administrator needs to create the database with the
     `createddb command <https://www.postgresql.org/docs/current/app-createdb.html>`_
     and assign the ownership to the database user configured in the first step.
   | If the database user has permissions to create PostgreSQL databases you can
     use the following command line as a convenient shortcut to create the scenario
     databases.

   .. code-block:: bash

       frepplectl createdatabase SCENARIO_KEY

#. | Restart the apache web server for the changes take effect.

#. | The new scenarios will be empty at the start. Use the scenario-copy command
     to copy data in a database.

.. _websocket:

Firewall issues with "plan editor" screen
-----------------------------------------

The "plan editor" screen of the Enterprise Edition doesn't work in some corporate
networks. The symptom is a message that the connection to the web service fails,
while the web service is up and running correctly on the server.

This can be caused by the firewall configuration on your network. This screen
uses the `websocket protocol <https://en.wikipedia.org/wiki/WebSocket>`_ which might
not be accepted by default on your firewall.

.. _proxy:

Proxy server configuration
--------------------------

Some companies deploy frepple behind a proxy server. The proxy server can take
care of the https encryption, can facilitate monitoring, and can improve security on
your network.

Some additional configuration is needed to make the django (which is the
web application framework used by frepple) run in this configuration.
See https://stackoverflow.com/questions/70501974/django-returning-csrf-verification-failed-request-aborted-behind-nginx-prox
for a thread discussing this topic.

The solution is to add the parameter
`CSRF_TRUSTED_ORIGINS <https://docs.djangoproject.com/en/4.2/ref/settings/#csrf-trusted-origins>`_
to your /etc/frepple/djangosettings.py configuration file, or to configure
the proxy to set some http headers.

.. _moveserver:

Move your frepple instance to a new server
------------------------------------------

First install frepple on the new server. Next, bring across the
following data elements from the old instance:

- The postgres database of each scenario needs to be dumped and restored.

- | The folder /etc/frepple contains the configuration files.
  | If the new server uses a different version of frepple, please don't copy
    the djangosettings.py file. Instead, reapply all configuration changes done
    in the old file to the file coming with the new release.

- The folder /var/log/frepple contains log files, data files,
  and attachment files.

- If you have tailored the apache configuration, you may also include
  the relevant files from the /etc/apache2 folder.

.. _external_authentication:

Integrate external authentication (Oauth2, Microsoft)
-----------------------------------------------------

Enterprises are moving towards authentication methods like OAuth, SAML,
OpenID, ... with multi-factor authentication to protect data access,
manage users and control their access rights.

Using the `django-allauth <https://docs.allauth.org/en/latest/>`_
library frepple can be configured to authenticate using a large number of
authentication protocols and social accounts.

The steps to authenticate using OAuth2 are as follows. Other methods supported by
django-allauth will have pretty similar instructions.

#. | Set up your Oauth provider.
   | You will need its CLIENT_ID and the CLIENT_SECRET later on in this process.
   | Assure that you have set the callback URL of the provider to
     https://<DOMAIN-OF-YOUR-FREPPLE-INSTALL>/accounts/auth0/login/callback/

#. | Install the django-allauth python package.   
   | Recent frepple releases (>=9.6) already include the package and you can skip
     this step.
   | In earlier versions you need to install it yourself in the frepple venv.

   .. code-block:: bash

      . /usr/share/frepple/venv/bin/activate
      pip3 install django-allauth --no-dependencies

#. | Update your /etc/frepple/djangosettings.py file.

     .. code-block:: python

        INSTALLED_APPS = (
          ...
          # Add these lines.
          "freppledb.external_auth",
          "django.contrib.sites",
          "allauth",
          "allauth.account",
          "allauth.socialaccount",
          "allauth.socialaccount.providers.auth0",
        )

        AUTHENTICATION_BACKENDS = (
          "freppledb.common.auth.MultiDBBackend",
          # Add the the following line.
          "freppledb.external_auth.auth.CustomAuthenticationBackend",
          )

        # Add new settings at the end of the file
        SITE_ID = 1
        LOGIN_URL = "/accounts/auth0/login/"
        LOGIN_REDIRECT_URL = "/accounts/auth0/login/"
        LOGOUT_REDIRECT_URL = "/accounts/logout/"
        ACCOUNT_LOGOUT_ON_GET = True
        ACCOUNT_EMAIL_VERIFICATION = "none"
        SOCIALACCOUNT_AUTO_SIGNUP = True
        SOCIALACCOUNT_LOGIN_ON_GET = True
        SOCIALACCOUNT_ADAPTER = 'freppledb.external_auth.auth.CustomAccountAdapter'
        ACCOUNT_ADAPTER = 'freppledb.external_auth.auth.CustomAdapter'
        SOCIALACCOUNT_PROVIDERS = {
              "auth0": {
                  "AUTH0_URL": "<URL-OF-YOUR-OAUTH-PROVIDER>", # UPDATE!!!
              }
            }
        DEFAULT_USER_GROUP = "Planner" # New users are automatically added to this group

       # The following settings may be needed to satisfy the CORS
       # requirements with the authentication provider. Don't copy these
       # lines blindly but carefully review what is really needed.
        CONTENT_SECURITY_POLICY = "frame-ancestors 'self' <URL-OF-EXTERNAL-APP>;"
        X_FRAME_OPTIONS = None
        SESSION_COOKIE_SAMESITE = "none"
        CSRF_COOKIE_SAMESITE = "none"

#. Migrate the database structure for the new apps.

   .. code-block:: bash

      frepplectl migrate

#. | Configure the authentication.
   | A few database records need to be created.

   .. code-block:: bash

      frepplectl dbshell

      sql> insert into django_site
        (id, domain, name)
        values(1, '<DOMAIN-OF-YOUR-FREPPLE-INSTALL>', '<DOMAIN-OF-YOUR-FREPPLE-INSTALL>')    -- UPDATE !!!
        on conflict (id)
        do update set domain=excluded.domain, name=excluded.name;

      sql> insert into socialaccount_socialapp
        (id, provider, provider_id, name, client_id, secret, key, settings)
        values
        (1, 'auth0', 'auth0' 'auth0',
        '<OAUTH-CLIENT>',   -- UPDATE !!!
        '<OAUTH-CLIENT-SECRET>', -- UPDATE !!!
        'frepple2',
        '{}'
        );

      sql> insert into socialaccount_socialapp_sites
        (socialapp_id, site_id)
        values (1, 1);


#. | Define which access rights you want to assign to newly added users.
   | Use the "admin/groups" screen to define a group called "Planner", and
     assign the correct permissions to the group.
   | Hint: Define only a minimal set of permissions to the group. You can
     always grant additional permissions later on to the handful of
     super-users that need those.

#. | Authorization is a different topic, closely related to authentication.
   | Authentication determines whether users are who they claim to be.
   | Authorization determines what users can and cannot access.
   | Authorization can be handled externally or in frePPLe. The file
     https://github.com/frePPLe/frepple/blob/master/freppledb/external_auth/auth.py
     may need to be tailored to handle your requirements. 
