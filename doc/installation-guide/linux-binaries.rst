=====================
Linux binary packages
=====================

* `Supported distributions`_
* `Installation and configuration`_
* `Debian installation script`_
* `Red Hat installation script`_

***********************
Supported distributions
***********************

Binary installation packages are available for the following Linux
distributions:

#. | **Fedora 22** and higher
   | FrePPLe is included in the official repositories.

   .. image:: _images/fedorainstall.png

#. | **Ubuntu LTS**
   | A 64-bit binary package for Ubuntu 16 is available.

Other Linux distributions aren't really a problem, but you'll need to build
the frePPLe package from the source .deb or .rpm files, as described on the
next page. The build process is completely standardized.

******************************
Installation and configuration
******************************

The binary package installs the solver engine executables as well as the user
interface. The user interface is installed as a WSGI application deployed on
the Apache web server with the mod_wsgi module.

Here are the steps to get a fully working environment.

#. **Install and tune the PostgreSQL database**

   Install postgreSQL 9.3 or higher, the world's most advanced open source database.

   FrePPLe assumes that the database uses UTF-8 encoding.

   FrePPLe needs the following settings for its database connections. If these
   values are configured as default for the database (in the file postgresql.conf)
   or the database role (using the 'alter role' command), a small performance
   optimization is achieved:
   ::

       client_encoding: 'UTF8',
       default_transaction_isolation: 'read committed',
       timezone: 'UTC' when USE_TZ is True, value of TIME_ZONE otherwise.

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
   intensive use. We highly recommend using the pgtune utility (or its online
   version at http://pgtune.leopard.in.ua/) to optimize the configuration for your
   hardware.

#. **Create the database and database user**

   A database needs to be created for the default database, and one for each of
   the what-if scenarios you want to configure.

   The same user is normally used as the owner of these databases.

   The typical SQL statements are shown below. Replace USR, PWD, DB with the suitable
   values.
   ::

       create user USR with password 'PWD';
       create database DB encoding 'utf-8' owner USR;

#. **Install Python3 and pip3**

   You'll need to install the Python 3.4 or higher and ensure the pip3 command is available.
   Most Linux distributions provide python2 by default, and you'll need python3 in parallel
   with it.

   On RPM based distributions:
   ::

     yum install python3 python3-pip

   On Debian based distributions:
   ::

     apt-get install python3 python3-pip

#. **Install the Python modules**

   The python3 modules used by frePPLe are listed in the file "requirements.txt". You can download
   it from https://raw.githubusercontent.com/frepple/frepple/3.2/contrib/django/requirements.txt
   (make sure to replace 3.2 with the appropriate version number!)

   Alternatively you can create the file yourself with the following content:
   ::

      CherryPy == 3.2.2
      djangorestframework == 3.3.1
      djangorestframework-bulk == 0.2.1
      djangorestframework-filters == 0.6.0
      django-admin-bootstrapped
      django-bootstrap3
      html5lib == 0.999
      jdcal >= 1.0.1
      Markdown == 2.6.4
      openpyxl == 2.3.4
      https://github.com/frePPLe/django/tarball/frepple_3.1

   Next, install these modules with a pip3 command:
   ::

      pip3 install -r requirements.txt

#. **Install the frepple binary package**

   On Fedora:
   ::

     yum install frepple

   On Debian based distributions:
   ::

     dpkg -i frepple_*.deb
     apt-get -f -y -q install

   On RHEL:
   ::

    yum --nogpgcheck localinstall  *.rpm

#. **Configure frePPLe**

   The previous step installed a number of configuration files, which you
   now need to review and edit:

   #. **/etc/frepple/djangosettings.py**

      | Edit the "TIMEZONE" variable to your local setting:

      ::

          TIME_ZONE = 'Europe/Brussels'

      Edit the "DATABASES" with your database parameters. Make sure the
      settings match the connection and authentication configured in the
      file pg_hba.conf of the PostgreSQL database.
      ::

        DATABASES = {
          'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
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
            'TEST': {
              'NAME': 'test_frepple' # Database name used when running the test suite.
              }
            },
         ...

      Change the "SECRET_KEY" to some arbitrary value - important for security reasons.
      ::

         SECRET_KEY = '%@mzit!i8b*$zc&6oev96=RANDOMSTRING'

   #. | **/etc/frepple/license.xml**
      | No license file is required for the Community Edition.
      | If you are using the Enterprise Edition, replace this file with the
      | license file you received from us.

   #. | **/etc/frepple/init.xml**
      | For a standard deployment this file doesn't need modification.
      | Comment out the lines loading modules you are not using for a small
      | performance improvement.

   #. | **/etc/httpd/conf.d/z_frepple.conf**
      | For a standard deployment this file doesn't need modification.
      | It only needs review if you have specific requirements for the setup of
      | the Apache web server.

#. **Optionally, define custom attributes**

   It is pretty common to add customized attributes on items, locations,
   operations, etc to reflect the specifics of your business. They can be edited
   in the property ATTRIBUTES in the file /etc/frepple/djangosettings.py.
   ::

      ATTRIBUTES = [
        ('freppledb.input.models.Item', [
          ('attribute1', ugettext('attribute_1'), 'string'),
          ('attribute2', ugettext('attribute_2'), 'boolean'),
          ('attribute3', ugettext('attribute_3'), 'date'),
          ('attribute4', ugettext('attribute_4'), 'datetime'),
          ('attribute5', ugettext('attribute_5'), 'duration'),
          ('attribute6', ugettext('attribute_6'), 'number'),
          ('attribute7', ugettext('attribute_7'), 'integer'),
          ]),
        ('freppledb.input.models.Operation', [
          ('attribute1', ugettext('attribute_1'), 'string'),
          ])
        ]

   After editing the file, a script needs to be executed to generate a
   migration script for the database schema:
   ::

     frepplectl makemigrations

   Attributes can be added, changed and deleted at any later time as well,
   but it's most convenient to define them upfront before the database
   schema is created in the next step. When you later edit attributes you
   need to run the following commands to apply the changes to the database
   schema:
   ::

     frepplectl makemigrations
     frepplectl migrate

#. **Create the database schema**

   Your database is still empty now. The command below will create all
   objects in the database schema and load some standard parameters.

   ::

     frepplectl migrate

#. **Optionally, load the demo dataset**

   On a first installation, you may choose to install the demo dataset.

   ::

     frepplectl loaddata demo

#. **Update apache web server (Ubuntu only)**

  On Ubuntu the following statements are required to complete the deployment
  on the Apache web server.
  ::

    sudo a2enmod expires
    sudo a2enmod wsgi
    sudo a2enmod ssl
    sudo a2ensite default-ssl
    sudo a2ensite frepple
    sudo service apache2 restart

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
Debian installation script
**************************

This section shows the completely automated installation script for installing
and configuring frePPLe with a PostgreSQL database on a Debian server.

We use this script for our unit tests. You can use it as a guideline and
inspiration for your own deployments.

::

  # Bring the server up to date
  sudo apt-get -y -q update
  sudo apt-get -y -q upgrade

  # Install PostgreSQL
  # For a production installation you'll need to tune the database
  # configuration to match the available hardware.
  sudo apt-get -y install postgresql
  sudo su - postgres
  psql template1 -c "create user frepple with password 'frepple'"
  psql template1 -c "create database frepple encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario3 encoding 'utf-8' owner frepple"
  exit
  # The default frePPLe configuration uses md5 authentication on unix domain
  # sockets to communicate with the PostgreSQL database.
  sudo sed -i 's/local\(\s*\)all\(\s*\)all\(\s*\)peer/local\1all\2all\3\md5/g' /etc/postgresql/9.*/main/pg_hba.conf
  sudo service postgresql restart

  # Install python3 and required python modules
  sudo apt-get -y install python3 python3-pip
  sudo pip3 install -r requirements.txt

  # Install the frePPLe binary .deb package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev debian package files.
  # Normally you only need to install the frepple debian package.
  sudo dpkg -i frepple_*.deb
  sudo apt-get -f -y -q install

  # Configure apache web server
  sudo a2enmod expires
  sudo a2enmod wsgi
  sudo a2enmod ssl
  sudo a2ensite default-ssl
  sudo a2ensite frepple
  sudo service apache2 restart

  # Create frepple database schema
  frepplectl migrate --noinput

***************************
Red Hat installation script
***************************

This section shows the completely automated installation script for installing
and configuring frePPLe with a PostgreSQL database on a RHEL 6 server.

We use this script for our unit tests. You can use it as a guideline and
inspiration for your own deployments.

::

  # Update and upgrade
  sudo -S -n yum -y update

  # Install the PostgreSQL database
  # For a production installation you'll need to tune the database
  # configuration to match the available hardware.
  sudo yum install postgresql postgresql-server
  sudo service postgresql initdb
  sudo service postgresql start
  sudo su - postgres
  psql -dpostgres -c "create user frepple with password 'frepple'"
  psql -dpostgres -c "create database frepple encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario3 encoding 'utf-8' owner frepple"
  exit
  # The default frePPLe configuration uses md5 authentication on unix domain
  # sockets to communicate with the PostgreSQL database.
  sudo sed -i 's/local\(\s*\)all\(\s*\)all\(\s*\)peer/local\1all\2all\3\md5/g' /etc/postgresql/9.*/main/pg_hba.conf
  sudo service postgresql restart

  # Install python3 and required python modules
  sudo yum install python3 python3-pip
  sudo pip3 install -r requirements.txt

  # Install the frePPLe binary RPM package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev package files.
  # Normally you only need to install the frepple package.
  yum --nogpgcheck localinstall  frepple*.rpm

  # Create frepple database schema
  frepplectl migrate --noinput

******************************
Suse installation instructions
******************************

This section shows the instructions for installing
and configuring frePPLe with a PostgreSQL database on a SLES 12 server.

You can use it as a guideline and inspiration for your own deployments.

::

  # Update and Upgrade
  sudo zypper refresh
  sudo zypper update

  # Install the PostgreSQL database
  # tip: "sudo zypper se PACKAGENAME" to look for the correct package names
  sudo zypper install postgresql94 postgresql94-server postgresql94-devel

  # Note: frePPLe requires packages that may not be present in the basic Suse Enterprise Server repositories so you may need to add these repositories and install:
  sudo zypper addrepo http://download.opensuse.org/repositories/Apache:Modules/SLE_12_SP1/Apache:Modules.repo
  sudo zypper refresh
  sudo zypper install apache2-mod_wsgi-python3
  sudo zypper addrepo http://download.opensuse.org/repositories/devel:languages:python3/SLE_12_SP1/devel:languages:python3.repo
  sudo zypper refresh
  sudo zypper install python3-psycopg2

  # Create user, create databases, configure access
  sudo su
  sudo systemctl start postgresql
  su - postgres
  psql
  postgres=# ALTER USER postgres WITH PASSWORD 'postgres';
  postgres=# \q
  exit
  sudo systemctl restart postgresql
  su - postgres
  psql -dpostgres -c "create user frepple with password 'frepple'"
  psql -dpostgres -c "create database frepple encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario3 encoding 'utf-8' owner frepple"
  exit
  # Allow local connections to the database using a username and password.
  # The default peer authentication isn't good for frepple.
  sudo sed -i 's/local\(\s*\)all\(\s*\)all\(\s*\)peer/local\1all\2all\3\md5/g' /var/lib/pgsql/data/pg_hba.conf
  sudo systemctl restart postgresql

  # Install python3 and required python modules
  sudo zypper install python3 python3-pip
  sudo python3 -m ensure pip
  sudo pip3 install -r requirements.txt

  #install Apache2 modules:
  sudo a2enmod mod_access_compat mod_deflate
  sudo systemctl restart apache2
  #for some reason some modules may not be loading in apache
  #use "sudo httpd -t" to check is the syntax is ok
  #is there are errors you may need to edit  "/etc/apache2/loadmodule.conf" and add the modules:
  # LoadModule wsgi_module                               /usr/lib64/apache2/mod_wsgi.so
  # LoadModule access_compat_module                 /usr/lib64/apache2/mod_access_compat.so
  # LoadModule deflate_module                            /usr/lib64/apache2/mod_deflate.so

  # Install the frePPLe binary RPM package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev package files.
  # Normally you only need to install the frepple package.
  sudo rpm -i *.rpm
  or
  sudo zypper install *.rpm

  # Create frepple database schema
  sudo frepplectl migrate --noinput
