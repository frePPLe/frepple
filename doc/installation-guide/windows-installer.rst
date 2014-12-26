=================
Windows installer
=================

Installing and uninstalling frePPLe is straightforward. After accepting the
license agreement, the installer will guide you to select:

* The components to install
* The installation directory
* The license file, applicable only for the Enterprise Edition
* The language and database connection parameters
* Whether or not to register the server as a service

The installer has been tested on Windows XP, Windows 7 and Windows 8.

#. Prior to the installation, it is recommended to **uninstall any previous
   version**.

#. **Start the installer**

   .. image:: _images/wininstall0.png

#. **Accept the license agreement**

   FrePPLe is released with a dual license: you can choose either to apply the
   GNU Affero General Public License (aka AGPL) or to buy a commercial license.

   .. image:: _images/wininstall1.png

#. **Select the type of installation**

   If you have administrator rights on your computer, the installer will allow you
   choose to install frePPLe for your account only or for anybody logging in on
   the machine.

   If you don’t have administrator rights, this screen will automatically be
   skipped. Nothing to worry about.

   .. image:: _images/wininstall2.png

#. **Select the installation directory**

   A default location is selected depending on the installation type.

   .. image:: _images/wininstall3.png

#. **Select the license file**

   The enterprise edition requires a license file to be activated. You get the
   license file when you register your copy on the support section of the website.

   .. image:: _images/wininstall4.png

#. **Select the components to install**

   Optional extra components can be enabled.

   .. image:: _images/wininstall5.png

#. **Select the installation parameters**

   Two types of parameters are specified during the installation:

   #. Default language for the user interface

   #. Database connection parameters

      FrePPLe supports the PostgreSQL 9 and SQLite databases.

      The SQLite database is included with frePPLe, allowing you to get
      started very quickly: No additional installations are required.

      The installer detects you have the PostgreSQL database installed. If it
      is available you can fill in the parameters: the database name, the
      database user and its password, and the host and port number.

      The PostgreSQL database and the database user have to be created by the
      database administrator. Make sure the database user has been created and
      has been granted sufficient privileges to create tables and indexes.
      The frePPLe database tables will be created further in the installation.

   Your selections are saved in the file custom/djangosettings.py. The file can
   later be edited with a text editor.

   .. image:: _images/wininstall6.png

#. **Installation**

   During the actual installation you can see the list of installed files, and
   monitor the creation of the database schema (when using PostgreSQL).

   .. image:: _images/wininstall7.png

#. **Finish**

   At the end of the installation you can choose to start the server immediately.

   For a test or development installation it is recommended to run the server as
   a system tray application.

   For an installation in production mode AND when you have administrator rights on
   your computer, you can chose to register and start a service instead.

   .. image:: _images/wininstall8.png

#. **Start the server**

   FrePPLe’s user interface is web-based. You need to start the web server first
   in one of the following ways:

   #. Either it was already started at the last step of the installation process.

   #. Select “Run frePPLe server” from the program menu to start the web server
      in the system tray. If you’re new to frePPLe, this method is preferred.

   #. Select “Start Service” from the program menu or the Windows service manager.
      This option is available only when you choose to register a service during
      the installation.

   FrePPLe in the system tray:

   .. image:: _images/systemtray1.png

   .. image:: _images/systemtray2.png

   FrePPLe as a service:

   .. image:: _images/winservice.png

#. **Open your browser http\://localhost:8000/**

   You can type in the URL manually or double click the system tray icon.

   An administrator user account is created initially: **admin** with password **admin**.

.. tip::

  Change the password of the **admin** user as soon as possible.

  Leaving the default password may be convenient, but is considered a security risk.

.. tip::

  Multiple versions of frePPLe can be installed on the same machine.

  Multiple installations of the same release can’t. If you’ld need such a setup, it is better to
  install once and create different copies of the custom folder. Each copy will get need different
  parameter file djangosettings.py.
