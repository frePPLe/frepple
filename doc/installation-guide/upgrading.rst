================================
Upgrade an existing installation
================================

FrePPLe allows migrating an existing installation (any release >= 3.0)
to a new release without any loss of data.
A set of migration scripts is available to migrate the database schema to the
new release. 

This page documents the steps for this process.

* `Generic instructions`_
* `Debian upgrade script`_

********************
Generic instructions
********************

#. **Backup your old environment**

   You're not going to start without a proper backup of the previous installation,
   are you? We strongly recommend you start off with a backup of a) all PostgreSQL
   databases and b) the configuration file djangosettings.py.
   
#. **Upgrade the PostgreSQL database**

   FrePPLe requires postgresql 9.5 or higher. If you're on an older version, upgrading
   your PostgreSQL database is the first step.
  
   Note: When running on Windows, the migration process described here
   assumes that you are NOT using the embedded PostgreSQL database. Migrating data
   between different PostgreSQL installations is possible but requires additional
   steps.

#. **Install the new python package dependencies**

   Different frePPLe releases may require different versions of third party
   Python libraries.
   
   Minor releases (ie the third number in the release number changes) never require
   new dependencies, and you can skip this step.
   
   The following commands will bring these to the right level as required for the
   new release. Make sure to run it as root user or use sudo (otherwise the packages
   will be installed locally for that user instead of system-wide), and to replace 4.3
   with the appropriate major release number
   (if you are installing 4.3.5 for instance then the URL should only contain 4.3).
   ::
   
      pip3 install --force-reinstall -r https://raw.githubusercontent.com/frePPLe/frepple/4.3/requirements.txt


#. **Install the new frePPLe release.**

   Install the new version as described on the other pages.

   You can skip the step to generate the database schema. We'll do this
   a bit later.

#. **Update the configuration file djangosettings.py**

   The installation created a new version of the configuration file. Now,
   you'll need to merge your edits from the old file into the new file.
   
   In our experience an incorrectly updated configuration file is the most
   common mistake when upgrading. So, take this edit seriously and don't just use
   the old file without a very careful comparison.   
   
#. **Migrate the frePPLe databases**

   The following command needs to be repeated for each scenario database (as
   found in the keys in the DATABASES setting in /etc/frepple/djangosettings.py).
   ::
      
      frepplectl migrate --database=default
      
   On a fresh installation, this command intializes all database objects. When 
   running it on an existing installation it will incrementally update the
   database schema without any loss of data.

#. **Restart your apache server**

   After a restart of the web server, the new environment should be up and running.

.. tip::
   It is not possible to have multiple versions simultaneously on the same server.

*********************
Debian upgrade script
*********************

The commands below are a convenience summary of the above steps implemented for
a Debian/Ubuntu Linux server.

::

  sudo apt-get -y -q update
  sudo apt-get -y -q upgrade
  
  # Upgrade of the PostgreSQL database isn't covered in these commands.
  
  sudo pip3 install --force-reinstall -r https://raw.githubusercontent.com/frePPLe/frepple/4.3/requirements.txt
  
  # Download the debian package of the new release here.
  
  sudo dpkg --force-confold -i <frepple installation package>.deb
  
  # Manually edit the /etc/frepple/djangosettings.py file. The previous line
  # keeps the old configuration file, which may not be ok for the new release.
  
  frepplectl migrate --database=default
  
  # Repeat the above line for all scenarios that are in use
  
  sudo service apache2 reload
  