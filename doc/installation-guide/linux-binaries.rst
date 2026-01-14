=====================
Linux binary packages
=====================

* `Supported distributions`_
* `Installation and configuration`_
* `Ubuntu installation script`_
* `Ubuntu uninstallation script`_

***********************
Supported distributions
***********************

A binary installation packages is only available for **Ubuntu 24**.

On all other operating systems install through a docker container (which
is easier, simpler and more maintainable anyway).

******************************
Installation and configuration
******************************

The binary package installs the solver engine executables as well as the user
interface. The user interface is installed as a WSGI application deployed on
the Apache web server with the mod_wsgi module.

Here are the steps to get a fully working environment.

#. **Download the installation package**

   Download the .deb installation package.

   The Community Edition is a free downloaded from github at https://github.com/frePPLe/frepple/releases.

   The Enterprise Edition is available to customers from github at https://github.com/frePPLe/frepple-enterprise/releases

#. **Install and tune the PostgreSQL database**

   Install postgreSQL 17, 16, 15 (in this order of preference).

   FrePPLe assumes that the database uses UTF-8 encoding.

   FrePPLe needs the following settings for its database connections. If these
   values are configured as default for the database (in the file postgresql.conf)
   or the database role (using the 'alter role' command), a small performance
   optimization is achieved:
   ::

       client_encoding: 'UTF8',
       default_transaction_isolation: 'read committed',
       timezone: 'Europe/Brussels'  # Value of TIME_ZONE in your djangosettings.py file

   FrePPLe can communicate with the PostgreSQL server using either a) Unix
   domain sockets ('local' in pg_hba.conf) or b) TCP IP4 or IP6 sockets.

   FrePPLe can authenticate on the PostgreSQL database using either a) a
   password ('md5' in pg_hba.conf) or b) OS username ('peer' and 'ident'
   in pg_hba.conf).

   In case of error (while creating the databases) "Postgres PG::Error: ERROR: new encoding (UTF8) is incompatible":
   ::

       UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';
       DROP DATABASE template1;
       CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING = 'UNICODE';
       UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template1';
       \c template1
       VACUUM FREEZE;

#. **Tune the database**

   The default installation of PostgreSQL is not configured right for
   scalable production use.

   We advice using pgtune http://pgtune.leopard.in.ua/ to optimize the configuration
   for your hardware. Use "data warehouse" as application type and also assure the
   max_connection setting is moved from the default 100 to eg 400.

#. **Create the database and database user**

   A database needs to be created for the default database, and one for each of
   the what-if scenarios you want to configure.

   The same user can be used as the owner of these databases. Make sure to grant the
   createrole permissions to the database user.

   The typical SQL statements are shown below. Replace USR, PWD, DB with the suitable
   values.
   ::

       create user USR with password 'PWD' createrole;
       create database DB0 encoding 'utf-8' owner USR;
       create database DB1 encoding 'utf-8' owner USR;
       create database DB2 encoding 'utf-8' owner USR;
       create database DB3 encoding 'utf-8' owner USR;

#. **Install the frepple package**

   On the command line:
   ::

     apt install -f ./*.deb

#. **Configure frePPLe**

   The previous step installed a number of configuration files, which you
   now need to review and edit:

   #. | **/etc/frepple/license.xml**
      | The Community Edition requires no license file and you can skip this step.
      | For the Enterprise Edition, replace this file with the
        license file you received from us.

   #. **/etc/frepple/djangosettings.py - DATABASES**

      Edit the "DATABASES" with your database parameters. Make sure the
      settings match the connection and authentication configured in the
      file pg_hba.conf of the PostgreSQL database.
      ::

        DATABASES = {
          'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'frepple',
            'USER': 'frepple',     # Role name when using md5 authentication.
                                   # Leave as an empty string when using peer or
                                   # ident authencation.
            'PASSWORD': 'frepple', # Role password when using md5 authentication.
                                   # Leave as an empty string when using peer or
                                   # ident authencation.
            'HOST': '',            # When using TCP sockets specify the hostname,
                                   # the ip4 address or the ip6 address here.
                                   # Leave as an empty string to use Unix domain
                                   # socket ("local" lines in pg_hba.conf).
            'PORT': '',            # Leave to empty string when using Unix domain sockets.
                                   # Specify the port number when using a TCP socket.
            'OPTIONS': {},         # Backend specific configuration parameters.
            'CONN_MAX_AGE': None,
            'CONN_HEALTH_CHECKS': True,
            'FILEUPLOADFOLDER": os.path.normpath(
                os.path.join(FREPPLE_LOGDIR, 'data', 'default')
            ),
            'SQL_ROLE': 'report_role',
            'FREPPLE_PORT': '127.0.0.1:8002',   # Enterprise Edition only
            'SECRET_WEBTOKEN_KEY': SECRET_KEY,
            'TEST': {
              'NAME': 'test_frepple' # Database name used when running the test suite.
              }
            },
         ...

      You can configure as many scenario database as you desire. Just assure the NAME
      points to a separate database name for each scenario. In the Enterprise Edition
      you also need to assign a unique port number in the FREPPLE_PORT setting.

      Also pay attention to the FILEUPLOADFOLDER setting of each scenario. The
      setting is used by the `import data files <../command-reference.html#importfromfolder>`_
      task. By default all scenario databases use the same data folder on the server.
      By updating this setting you can configure a dedicated data folder for each
      scenario database.

   #. **/etc/frepple/djangosettings.py - SECRET_KEY**

      Change the "SECRET_KEY" to some arbitrary value - very important for security reasons.
      ::

         SECRET_KEY = '%@mzit!i8b*$zc&6oev96=RANDOMSTRING'

   #. **/etc/frepple/djangosettings.py - DATE_STYLE**

      Each country has its own preferred format of displaying dates.

      With this setting you can choose from 3 preconfigured styles, or you can
      customize your own format:
      ::

        # We provide 3 options for formatting dates (and you always add your own).
        #  - month-day-year: US format
        #  - day-month-year: European format
        #  - year-month-day: international format. This is the default
        # As option you can choose to hide the hour, minutes and seconds.
        DATE_STYLE = "year-month-date"
        DATE_STYLE_WITH_HOURS = True

   #. **/etc/frepple/djangosettings.py - INSTALLED_APPS**

      Change the "INSTALLED_APPS" to match your environment and the licensed modules.
      ::

        INSTALLED_APPS = (
          'django.contrib.auth',
          'django.contrib.contenttypes',
          'django.contrib.messages',
          'django.contrib.staticfiles',
          'freppledb.boot',
          #                                << ADD YOUR CUSTOM EXTENSION APPS HERE
          'freppledb.wizard',              << COMMENT IF MODEL BUILDING WIZARD ISN'T NEEDED
          'freppledb.input',
          #'freppledb.odoo',             # << UNCOMMENT TO ACTIVATE THE ODOO INTEGRATION
          #'freppledb.erpconnection',    # << UNCOMMENT TO ACTIVATE THE GENERIC ERP INTEGRATION
          'freppledb.metrics',
          'freppledb.output',
          'freppledb.execute',
          'freppledb.common',
          'django_filters',
          'rest_framework',
          'django.contrib.admin',
          # The next two apps allow users to run their own SQL statements on
          # the database, using the SQL_ROLE configured above.
          'freppledb.reportmanager',
          'freppledb.executesql',
          )

   #. **/etc/frepple/djangosettings.py - TIMEZONE**

      | Edit the "TIME_ZONE" variable if required. By default, the server time zone
        (where frepple is installed) will be used for both the database and the server.
        It's however possible to override this setting with a different time zone
        by uncommenting following line and setting desired time zone.

      ::

          # TIME_ZONE = 'Europe/Brussels'

   #. | **/etc/httpd/conf.d/z_frepple.conf**
      | For a standard deployment this file doesn't need modification.
      | It only needs review if you have specific requirements for the setup of
        the Apache web server.

#. **Create the database schema**

   Your database is still empty now. The command below will create all
   objects in the database schema and load some standard parameters.

   ::

     frepplectl migrate

   Note that the frepplectl command is only accessible to members of the "frepple"
   linux group. You'll need to assure you are member of that group or run the command
   as superuser.

#. **Optionally, load the demo dataset**

   On a first installation, you may choose to install the demo dataset.

   ::

     frepplectl loaddata demo

#. **Verify the installation**

   If all went well you can now point your browser to http://localhost.

   An administrative user account is created by default: **admin**, with password **admin**.

   Try the following as a mini-test of the installation:

   #. Open the screen "input/demand" to see demand inputs.

   #. Open the screen "admin/execute" and generate a plan.

   #. Use the same "admin/execute" screen to copy the default data in a new scenario.

   #. Open the screen "output/resource report" to see the planned load on the resources.

   If these steps all give the expected results, you're up and running!

.. tip::
   For security reasons it is recommended to change the password of the admin user.
   Until it is changed, a message is displayed on the login page.

**************************
Ubuntu installation script
**************************

This section shows the completely automated installation script for installing
and configuring frePPLe with a PostgreSQL database on an Ubuntu server.

We use this script for our unit tests and docker images. You can use it as a guideline and
inspiration for your own deployments.

::

  # Bring the server up to date
  sudo apt -y -q update
  sudo apt -y -q upgrade

  # Install PostgreSQL
  # For a production installation you'll need to tune the database
  # configuration to match the available hardware.
  sudo apt -y install postgresql
  sudo su - postgres
  psql template1 -c "create user frepple with password 'frepple' createrole"
  psql template1 -c "create database frepple encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario3 encoding 'utf-8' owner frepple"
  exit
  # The default frePPLe configuration uses md5 authentication on unix domain
  # sockets to communicate with the PostgreSQL database.
  sudo sed -i 's/local\(\s*\)all\(\s*\)all\(\s*\)peer/local\1all\2all\3\md5/g' /etc/postgresql/*/main/pg_hba.conf
  sudo service postgresql restart

  # Install the frePPLe binary .deb package and the necessary dependencies.
  sudo apt -f ./*.deb

  # Create frepple database schema
  sudo frepplectl migrate --noinput


****************************
Ubuntu uninstallation script
****************************

Uninstallation is as simple as:

::

  # Drop all postgresql database. Repeat this command for all databases
  # configured in the /etc/frepple/djangosettings.py file
  sudo dropdb -U <db-user> <db-name>

  # Uninstall the package, including log files and configuration files
  sudo apt purge frepple
