================================
Upgrade an existing installation
================================

FrePPLe allows migrating an existing installation to a new release without any loss of data.

This page documents the steps for this process.

* `Generic instructions`_
* `Ubuntu upgrade script`_

********************
Generic instructions
********************

#. **Backup your old environment**

   You're not going to start without a proper backup of the previous installation,
   are you? We strongly recommend you start off with a backup of a) all PostgreSQL
   databases and b) the configuration file /etc/frepple/djangosettings.py.

#. **Upgrade the PostgreSQL database**

   FrePPLe requires 12 or higher. If you're on an older version, upgrading
   your PostgreSQL database is the first step.

#. **Install the new frePPLe release.**

   Install the new .deb or .rpm package.
   ::

      sudo dpkg --force-confold -i ./*.deb

   The installer will prompt you whether you want to migrate your database now
   to the new release. If you case you allow run it now, you can skip one
   of the steps below.

#. **Update the configuration file /etc/frepple/djangosettings.py**

   The installation created a new version of the configuration file. Now,
   you'll need to merge your edits from the old file into the new file.

   In our experience an incorrectly updated configuration file is the most
   common mistake when upgrading. So, take this edit seriously and don't just use
   the old file without a very careful comparison.

#. **Migrate the frePPLe databases**

   In case you didn't opt to migrate your databases as part of the installation
   process you will need to run it manually.
   ::

      frepplectl migrate

   On a fresh installation, this command intializes all database objects. When
   running it on an existing installation it will incrementally update the
   database schema without any loss of data.

#. **Restart your apache server**

   After a restart of the web server, the new environment will be up and running.

*********************
Ubuntu upgrade script
*********************

The commands below are a convenience summary of the above steps implemented for
a Ubuntu Linux server.

::

  sudo apt -y -q update
  sudo apt -y -q upgrade

  # Upgrade of the PostgreSQL database isn't covered in these commands.

  # Download the ubuntu package of the new release here.

  sudo dpkg --force-confold -i <frepple installation package>.deb

  # Manually edit the /etc/frepple/djangosettings.py file. The previous line
  # keeps the old configuration file, which may not be ok for the new release.

  # This step can be skipped if you choose to run it during the installation.
  frepplectl migrate

  sudo service apache2 reload
