==================
Compiling on Linux
==================

This page describes 3 different methods:

* | `Compiling from the github source code repository or source tarball`_
  | Instructions for compilation from the latest source code.

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

******************************************************************
Compiling from the github source code repository or source tarball
******************************************************************

To work with the source code directly from the github repository you will
need the following steps:

#. Update your system with the development software packages.

   * | gcc, v3.4 or higher
     | Front end for the GNU compiler suite.

   * | gcc-c++, compatible with gcc release
     | GNU C++ compiler.

   * | xerces-c, 3.0 or 3.1
     | Xerces is a validating XML parser provided by the Apache Foundation.
     | You need to install the libraries as well as the development libraries.

   * | python 3.4 or higher
     | Python is a modern, easy to learn interpreted programming language.
     | You need to install the language as well as the development libraries.

   * | git
     | Distributed version control tool.

   * | autoconf, v2.59 or later
     | Gnu Autoconf produces shell scripts to automatically configure software
        source code packages. This makes the source code easier to port across
        platforms.

   * | automake, v1.9.5 or later
     | Gnu Automake is a tool for automatically generating make-files.

   * | libtool, v1.5 or later
     | Libtool hides the complexity of developing and using shared libraries
        for different platforms behind a consistent and portable interface.

   * | python-sphinx (optional)
     | A modern documentation generation tool.

#. Pick up the latest code from the repository with the command:
   ::

     git clone https://github.com/frePPLe/frePPLe.git <project_directory>

#. Initialize the automake/autoconf/libtool scripts:
   ::

     cd <project_directory>
     make -f Makefile.dist prep

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

#. To sync your environment with the latest changes from the repository:
   ::

     cd <project_directory>
     git pull

#. Example Suse Enterprise 12 SP1 build script to create RPMs:
   ::

      export GITURL="https://github.com/frePPLe/frePPLe.git"
      export GITBRANCH=master

      # Basics
      sudo zypper update
      sudo zypper --non-interactive install --force-resolution libxerces-c-3_1 libxerces-c-devel openssl openssl-devel libtool make automake autoconf doxygen python3 python3-devel gcc-c++ graphviz rpm-build git libpq5 postgresql-devel

      #create rpm tree
      mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

      # GIT
      git clone $GITURL -b $GITBRANCH frepple-$RELEASE/

      # PIP and PIP requirements
      sudo python3 -m ensurepip
      sudo pip3 install -r ~/frepple-$RELEASE/requirements.txt
      sudo pip3 install psycopg2 Sphinx

      # FREPPLE
      cd ~/frepple-$RELEASE
      make -f Makefile.dist prep config
      cd contrib/rpm
      make suse

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

     dnf install rpmbuild
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
