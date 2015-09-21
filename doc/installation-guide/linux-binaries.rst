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

   The same user is normally used as the owner of these databases.

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

   Instead, download the source from our cloned and patched version of django
   and install that. The URL of the django clone is https://github.com/frePPLe/django

   Make sure you download the branch for the correct frePPLe version

   The shell commands for these steps are (replace 3.0 with the correct frePPLe
   version:
   ::

      wget https://github.com/frePPLe/django/archive/frepple_3.0.tar.gz
      tar xvfz frepple_3.0.tar.gz
      cd django-frepple_3.0
      python3 setup.py install

#. **Install OpenPyXL**

   This python package allows us to read and write Excel spreadsheet files. It
   is best to install it from PyPi using pip.
   ::

     pip3 install openpyxl

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
   Until it is changed, a message is displayed on the login page.

**************************
Debian installation script
**************************

This section shows the completely automated installation script for installing
and configuring frePPLe with a PostgreSQL database on a Debian server.

We use this script for our unit tests. You can use it as a guideline and
inspiration for your own deployments.

::

  export FREPPLERELEASE=3.0

  # Bring the server up to date
  sudo apt-get -y -q update
  sudo apt-get -y -q upgrade

  # Install PostgreSQL
  sudo apt-get -y install postgresql python3-psycopg2
  sudo su - postgres
  psql template1 -c "create user frepple with password 'frepple'"
  psql template1 -c "create database frepple encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql template1 -c "create database scenario3 encoding 'utf-8' owner frepple"
  sed -i 's/peer$/md5/g' /etc/postgresql/9.*/main/pg_hba.conf
  service postgresql restart
  exit

  # Install a patched version of Django
  wget -q https://github.com/frePPLe/django/archive/frepple_$FREPPLERELEASE.tar.gz
  tar xfz frepple_$FREPPLERELEASE.tar.gz
  cd django-frepple_$FREPPLERELEASE
  sudo python3 setup.py install

  # Install openpyxl
  sudo apt-get -y install python3-pip
  sudo pip3 install openpyxl

  # Install the frePPLe binary .deb package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev debian package files.
  # Normally you only need to install the frepple debian package.
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

***************************
Red Hat installation script
***************************

This section shows the completely automated installation script for installing
and configuring frePPLe with a PostgreSQL database on a RHEL 6 server.

We use this script for our unit tests. You can use it as a guideline and
inspiration for your own deployments.

::

  export FREPPLERELEASE=3.0

  # Update and upgrade
  sudo -S -n yum -y update

  # Install the PostgreSQL database
  sudo yum install postgresql postgresql-server python3-psycopg2
  sudo service postgresql initdb
  sudo service postgresql start
  sudo su - postgres
  psql -dpostgres -c "create user frepple with password 'frepple'"
  psql -dpostgres -c "create database frepple encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario3 encoding 'utf-8' owner frepple"
  sed -i 's/peer$/md5/g' /var/lib/pgsql/data/pg_hba.conf
  sudo service postgresql restart

  # Install a patched version of Django
  wget -q https://github.com/frePPLe/django/archive/frepple_$FREPPLERELEASE.tar.gz
  tar xfz frepple_$FREPPLERELEASE.tar.gz
  cd django-frepple_$FREPPLERELEASE
  sudo -S -n python3 setup.py install

  # Install openpyxl
  # The sequence is a bit weird: we first enable the EPEL repository, then install pip, and
  # finish by installing openpyxl itself.
  sudo -S -n rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
  sudo -S -n yum -y install yum-plugin-protectbase.noarch
  sudo -S -n yum -y install python3-pip
  sudo pip3 install openpyxl

  # Install the frePPLe binary RPM package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev package files.
  # Normally you only need to install the frepple package.
  yum --nogpgcheck localinstall  *.rpm

  # Create frepple database schema
  frepplectl migrate --noinput
  
***************************
Suse installation instructions
***************************

This section shows the instructions for installing
and configuring frePPLe with a PostgreSQL database on a SLES 12 server.

You can use it as a guideline and inspiration for your own deployments.

::

  export FREPPLERELEASE=3.0

  # Update and Upgrade
  sudo zypper update
  sudo zypper upgrade
  
  # Install the PostgreSQL database
  
  tip: "sudo zypper se PACKAGENAME" to look for the correct package names 
  
  sudo zypper install postgresql postgresql-server postgres-devel
  
  sudo su
  rcpostgresql start
  su - postgres
  psql
  postgres=# ALTER USER postgres WITH PASSWORD 'postgres';
  postgres=# \q
  exit
  rcpostgresql restart
  su - postgres
  psql -dpostgres -c "create user frepple with password 'frepple'"
  psql -dpostgres -c "create database frepple encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario1 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario2 encoding 'utf-8' owner frepple"
  psql -dpostgres -c "create database scenario3 encoding 'utf-8' owner frepple"
  sed -i 's/peer$/md5/g' /var/lib/pgsql/data/pg_hba.conf
  exit
  rcpostgrsql restart

  # Install a patched version of Django
  wget -q https://github.com/frePPLe/django/archive/frepple_$FREPPLERELEASE.tar.gz
  tar xfz frepple_$FREPPLERELEASE.tar.gz
  cd django-frepple_$FREPPLERELEASE
  sudo -S -n python3 setup.py install

  # Install openpyxl
  # pip is in SUSE included in the Python3 package but must be enabled.
  # After pip3 is available we can finish by installing openpyxl itself.
  sudo python3 -m ensure pip
  sudo pip3 install openpyxl

  # Install the frePPLe binary RPM package and the necessary dependencies.
  # There are frepple, frepple-doc and frepple-dev package files.
  # Normally you only need to install the frepple package.
  sudo rpm -i *.rpm

  # Create frepple database schema
  frepplectl migrate --noinput
