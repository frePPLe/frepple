==================
Compiling on Linux
==================

This page describes 3 different methods:

* | `Compiling from a source tarball`_
  | Generic instructions, which doesn’t include any deployment related actions.

* | `Compiling from the github source code repository`_
  | Extra instructions when you compile from the latest source code.

* | `Compiling from a Debian source package`_
  | This is the **recommended method for all Debian based distributions**.
  | The Debian package not only compiles the software, but also configures the
    Apache web server, user permissions, configuration files and log directories.

* | `Compiling from a RPM source package`_
  | This is the **recommended method for all Red Hat based distributions**.
  | The RPM package not only compiles the software, but also configures the
    Apache web server, user permissions, configuration files and log directories.

The instructions on this page describe how you compile the frePPLe source code
into binaries. After compilation you need to return to the installation and
configuration steps outlined on the previous page.

*******************************
Compiling from a source tarball
*******************************

This section describes the generic steps you need to build frePPLe from the source code.
FrePPLe uses a very standard build process, based on the automake suite.

#. Download the source code from http://sourceforge.net/projects/frepple/files/

   If you want to use source code directly from the github repository, you'll
   need to replace this step with the instructions from the following section.

#. Update your system with the development software packages.

   * | gcc, v3.4 or higher
     | Front end for the GNU compiler suite.

   * | gcc-c++, compatible with gcc release
     | GNU C++ compiler.

   * | xerces-c, 3.0 or 3.1
     | Xerces is a validating XML parser provided by the Apache Foundation.
     | You need to install the libraries as well as the development libraries.

   * | python 3.3 or higher
     | Python is a modern, easy to learn interpreted programming language.
     | You need to install the language as well as the development libraries.
     | Note: FrePPLe versions < 3.0 required Python 2.7.

#. Configure the build with the following command:
   ::

     ./configure –sysconfdir=/etc

   You can use the option '–help’ to see the list of available options.

   The sysconfdir option is required to make sure the configuration files
   are always available under /etc, even when the package is compiled with
   a prefix such as /usr/local.

#. Compile the source code:
   ::

     make all

#. Run the test suite:
   ::

     make check

   Not all tests are currently passing, so you shouldn’t be worried about
   a couple of failures.

#. Install the files:
   ::

     make install

#. Free the disk space used during the build and test phases.
   ::

     make clean


************************************************
Compiling from the github source code repository
************************************************

To work with the source code directly from the github repository you will
need the following steps to replace the first point in the section above.

#. Update your machine with the following packages

   #. | git
      | Distributed version control tool.

   #. | autoconf, v2.59 or later
      | Gnu Autoconf produces shell scripts to automatically configure software
        source code packages. This makes the source code easier to port across
        platforms.

   #. | automake, v1.9.5 or later
      | Gnu Automake is a tool for automatically generating make-files.

   #. | libtool, v1.5 or later
      | Libtool hides the complexity of developing and using shared libraries
        for different platforms behind a consistent and portable interface.

   #. | python-sphinx (optional)
      | A modern documentation generation tool.

#. Pick up the latest code from the repository with the command:
   ::

     git clone https://github.com/frePPLe/frePPLe.git <project_directory>

#. Initialize the automake/autoconf/libtool scripts:
   ::

     cd <project_directory>
     make -f Makefile.dist prep

#. Now the configure script is up to date and you can follow the same steps as in
   the section above.

#. To sync your environment with the latest changes from the repository:
   ::

     cd <project_directory>
     git pull

**************************************
Compiling from a debian source package
**************************************

The steps to work with such packages are standard:

#. Install the django package as described on the previous page.

#. Install the dpkg-dev package and all prerequisite packages for frepple:
   ::

     apt-get install dpkg-dev debhelper cdbs autotools-dev python-dev libxerces-c-dev libtool python-sphinx

#. Build the source directory.

   Expand all files listed in the .dsc file.

#. Build the package in the source directory.
   ::

     dpkg-buildpackage -B

***********************************
Compiling from a RPM source package
***********************************

The steps to work with such packages are standard:

#. Install the django package as described on the previous page.

#. Install the rpmbuild package:
   ::

     yum install rpmbuild
     or
     zypper in rpmbuild

#. Create a build directory structure:
   ::

     rpmdev-setuptree
     or
     mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

#. Install the source RPM file:

   This will create files in the SOURCES directory of your RPM building directory
   tree, and a .spec file in the SPECS directory.
   ::

     rpm -i frepple-*.src.rpm

#. Build the RPM:

   Go the SPECS directory and give the command to build the RPM:
   ::

     cd /home/your_userid/rpm/SPECS
     rpmbuild -bb frepple.spec
