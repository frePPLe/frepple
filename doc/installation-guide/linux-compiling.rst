==================
Compiling on Linux
==================

The instructions on this page describe how you compile the frePPLe source code
into binaries. After compilation you need to return to the installation and
configuration steps outlined on the previous page.

In the folder contrib/docker you find a number of dockerfiles that automate the
instructions below for some common linux distributions.

#. Update your system with the development software packages.

   * | gcc
     | Front end for the GNU compiler suite.

   * | gcc-c++
     | GNU C++ compiler.

   * | xerces-c, 3.1 or higher
     | Xerces is a validating XML parser provided by the Apache Foundation.
     | You need to install the libraries as well as the development libraries.

   * | python 3.8 or higher
     | Python is a modern, easy to learn interpreted programming language.
     | You need to install the language as well as the development libraries.

   * | git
     | Distributed version control tool.

   * | CMake, 3.0 or higher
     | CMake is a cross-platform tool for building and packaging software.

   * | python-sphinx (optional)
     | A modern documentation generation tool.

   * | PostgreSQL, 12 or higher
     | The world's most advanced open source relational database. And that's not
       an overstatement...

#. Pick up the latest code from the repository:
   ::

     git clone https://github.com/frePPLe/frePPLe.git <project_directory>

#. Initialize the build environment

   The CMakeLists.txt file has some logic to detect your Linux distribution
   and configure the build script. In case you're working on an unknown distribution
   or version, you will need to update this file.

   The initialization step will also check for all required build software and
     report any missing packages.

   ::

     cd <project_directory>
     mkdir build
     cd build
     cmake ..

#. Build the software

   ::

     cd <project_directory>/build
     cmake --build . --config Release

#. Install the software

   ::

     cd <project_directory>/build
     cmake --install .

#. Optionally, create a installation .deb or .rpm package

   ::

     cd <project_directory>/build
     cmake --build . --target package

#. Free the disk space used during the build.

   ::

     cd <project_directory>
     rm -rf build

#. To sync your environment with the latest changes from the repository:

   ::

     cd <project_directory>
     git pull

#. Putting it all together... Here is an example build script for Ubuntu:

   ::

      # Update your linux with the right development packages
      # The package manager and the package names will vary by distribution
      sudo apt update
      sudo apt install libxerces-c3.2 libxerces-c-dev openssl libssl-dev cmake python3 python3-dev g++ git libpq5 libpq-dev python3-sphinx

      # Clone the source code from the git repository
      git clone https://github.com/frePPLe/frePPLe.git -b master ~/frepple

      # Install Python packages
      cd ~/frepple
      sudo pip3 install -r ./requirements.dev.txt

      # Compile
      mkdir ~/frepple/build
      cd ~/frepple/build
      cmake ..
      cmake --build . --target Release
      cmake --build . --target package
