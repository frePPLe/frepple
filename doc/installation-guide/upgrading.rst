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

   FrePPLe requires 13 or higher. If you're on an older version, upgrading
   your PostgreSQL database is the first step.

   When you move your frepple databases to a new server, there are some special
   considerations to follow. Depending on the method you used to dump and restore the
   databases some extra steps may be required.

   #. Assure the new database is correctly tuned.

      The default installation of PostgreSQL is not configured right for
      scalable production use.

      We advice using pgtune http://pgtune.leopard.in.ua/ to optimize the configuration
      for your hardware. Use "data warehouse" as application type and also assure the
      max_connection setting is moved from the default 100 to eg 400.

   #. Frepple uses 2 database roles to access the database. These are configured as USER 
      (for full access) and SQL_ROLE (for read-only access to some tables in report manager)
      in the DATABASES section of your /etc/frepple/djangosettings.py file.
      
      All objects in your new databases should be owned by the USER.

   #. The database user USER should be granted the SQL_ROLE.
   
      It's possible that this grant was not part of your dump-restore process. If so, you
      can correct that by running the following SQL command as a database administrator.

      ::

         GRANT <SQL_ROLE> TO <USER>;
   
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
