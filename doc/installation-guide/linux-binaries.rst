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

#. | **Fedora 20** and higher
   | FrePPLe is included in the official repositories.

   .. image:: _images/fedorainstall.png

#. | **Ubuntu LTS**
   | A 64-bit binary package for Ubuntu 14 is available.

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

   Install postgreSQL 9.0 or higher, the world's most advanced open source database.

   FrePPLe assumes that the database uses UTF-8 encoding.

   FrePPLe needs the following settings for its database connections. If these
   values are configured as default for the database (in the file postgresql.conf)
   or the database role (using the 'alter role' command), a small performance
   optimization is achieved:
   ::

       client_encoding: 'UTF8',
       default_transaction_isolation: 'read committed',
       timezone: 'UTC' when USE_TZ is True, value of TIME_ZONE otherwise.

   For the user that will run the user interface application (normally
   'www-data' on debian and 'apache' on rhel) you need to create a file .pgpass
   in their home directory. This allows them to connect without entering a password.

   See the Django documentation at http://docs.djangoproject.com/en/dev/ref/databases/
   for more details.

#. **Tune the database**

   The default installation of PostgreSQL is not configured right for
   intensive use. We highly recommend using the pgtune utility (or its online
   version at http://pgtune.leopard.in.ua/) to optimize the configuration for your
   hardware.

#. **Create the database and database user**

   A database needs to be created for the default database, and one for each of
   the what-if scenarios you want to configure.

   A single user is normally used as the owner of these databases.

   The typical SQL statements are shown below. Replace USR, PWD, DB with the suitable
   values.
   ::

       create user USR with password 'PWD';
       create database DB encoding 'utf-8' owner USR;

#. **Install the Python database drivers**

   You'll need to install the python-psycopg2 package for PostgreSQL.

#. **Install Django**

   Since frePPle requires some patches to the standard Django package,
   you can't install the binary package that comes with your Linux distribution.
   Instead, download the source from http://www.djangoproject.com and expand
   it in a local folder. Next, download and apply frePPLe's django patch
   and install the package.

   A version of frePPle requires a specific version of Django. FrePPLe 2.2, 2.3 require
   Django 1.6.x. FrePPLe 3.0 requires django 1.8.x.

   The patch file is available at https://github.com/frePPLe/frePPLe/tree/3.0/contrib/django
   - replace the version number to match the frePPLe release

   The shell commands for these steps are:
   ::

      wget https://www.djangoproject.com/download/1.8/tarball/
      tar xvfz Django-1.8.tar.gz
      cd Django-1.8
      patch -p0 < django.patch
      python setup.py install

#. **Install OpenPyXL**

   This python package allows us to read and write Excel spreadsheet files. It
   is best to install it from PyPi using pip.
   ::

     pip install openpyxl

   Most linux distributions don't install pip by default, so you'll need to install
   that first. See below for the commands for this on Ubuntu and RHEL.

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

   #. | **/etc/frepple/djangosettings.py**
      | Edit the "TIMEZONE" variable to your local setting.
      | Edit the "DATABASES" with your database parameters.
      | Change "SECRET_KEY" to some arbitrary value - important for security reasons.

   #. | /etc/frepple/license.xml
      | No license file is required for the community edition.
      | If you are using the Enterprise Edition, replace this file with the
      | license file you received from us.

   #. | /etc/frepple/init.xml
      | Comment out the lines loading modules you are not using.

   #. | /etc/httpd/conf.d/z_frepple.conf
      | For a standard deployment this file doesn't need modification.
      | It only needs review if you have specific requirements for the setup of
      | the Apache web server.

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

**************************
Debian installation script
**************************

This section shows the completely automated installation script for installing
and configuring frePPLe with a PostgreSQL database on a Debian server.

We use this script for our unit tests. You can use it as a guideline and
inspiration for your own deployments.

::

  # Bring the server up to date with the latest and greatest
  sudo apt-get -y -q update
  sudo apt-get -y -q upgrade

  # Install PostgreSQL
  sudo apt-get -y install postgresql-9.1 python-psycopg2
  sudo su - postgres
  psql template1 -c "create user frepple with password 'frepple'"
  psql template1 -c "create database frepple encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario3 encoding 'utf-8' owner frepple"
  sed -i 's/peer$/md5/g' /etc/postgresql/9.1/main/pg_hba.conf
  service postgresql restart
  exit

  # Install Django
  wget -q -O Django-$DJANGORELEASE.tar.gz https://www.djangoproject.com/download/$DJANGORELEASE/tarball/
  tar xfz Django-$DJANGORELEASE.tar.gz
  cd ~/Django-$DJANGORELEASE
  patch -p0 < frepple_directory/contrib/django/django.patch
  sudo python setup.py install

  # Install openpyxl
  sudo apt-get -y install python-pip
  sudo pip install openpyxl

  # Install the frePPLe binary .deb package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev debian package files.
  # You only need to install the frepple debian package.
  cd ~
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

  # Make postgresql accessible for apache user without password
  sudo sh -c 'echo "localhost:5432:frepple:frepple:frepple" > ~www-data/.pgpass'
  sudo sh -c 'echo "localhost:5432:scenario1:frepple:frepple" >> ~www-data/.pgpass'
  sudo sh -c 'echo "localhost:5432:scenario2:frepple:frepple" >> ~www-data/.pgpass'
  sudo sh -c 'echo "localhost:5432:scenario3:frepple:frepple" >> ~www-data/.pgpass'
  sudo chown www-data:www-data ~www-data/.pgpass
  sudo chmod 0600 ~www-data/.pgpass

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
  sudo yum install postgresql postgresql-server python-psycopg2
  sudo service postgresql initdb
  sudo service postgresql start
  sudo su - postgres
  psql -dpostgres -c "create user frepple with password 'frepple'"
  psql -dpostgres -c "create database frepple encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario3 encoding 'utf-8' owner frepple"
  sed -i 's/peer$/md5/g' /var/lib/pgsql/data/pg_hba.conf

  # Install django
  wget -q -O Django-$DJANGORELEASE.tar.gz https://www.djangoproject.com/download/$DJANGORELEASE/tarball/
  tar xfz Django-$DJANGORELEASE.tar.gz
  cd ~/Django-$DJANGORELEASE
  patch -p0 < ~/frepple-$RELEASE/contrib/django/django.patch
  sudo -S -n python setup.py install

  # Install openpyxl
  # The sequence is a bit weird: we first enable the EPEL repository, then install pip, and
  # finish by installing openpyxl itself.
  sudo -S -n rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
  sudo -S -n yum -y install yum-plugin-protectbase.noarch
  sudo -S -n yum -y install python-pip
  sudo pip install openpyxl

  # Build frepple RPM
  yum --nogpgcheck localinstall  *.rpm

  # Make PostgreSQL accessible for apache user
  sudo sh -c 'echo "localhost:5432:frepple:frepple:frepple" > ~apache/.pgpass'
  sudo sh -c 'echo "localhost:5432:scenario1:frepple:frepple" >> ~apache/.pgpass'
  sudo sh -c 'echo "localhost:5432:scenario2:frepple:frepple" >> ~apache/.pgpass'
  sudo sh -c 'echo "localhost:5432:scenario3:frepple:frepple" >> ~apache/.pgpass'
  sudo chown apache:apache ~apache/.pgpass
  sudo chmod 0600 ~apache/.pgpass
