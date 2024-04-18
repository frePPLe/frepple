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


.. _https:

Enable https encryption for all web traffic
-------------------------------------------

The standard installation uses unencrypted web traffic over HTTP. The IT policy
of many companies requires encrypting all web traffic of all web applications
over HTTPS.

This is pretty easy to configure in frePPLe. FrePPLe uses a standard
`Apache <https://httpd.apache.org/>`_ web server. A google search will
provide a lot of info on how to achieve this.

The basic steps for the ubuntu operating system we use are:

.. code-block:: bash

   a2enmod ssl       # Enable the ssl module
   a2ensite default-ssl    # Configure the module. Adjust this step to use your own ssl certificate!

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
