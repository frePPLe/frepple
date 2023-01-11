==================
Compiling on Linux
==================

The instructions on this page describe how you compile the frePPLe source code
into binaries. After compilation you need to return to the installation and
configuration steps outlined on the previous page.

In the folder contrib/docker you find a number of dockerfiles that build from
scratch on all supported linux distributions. You can get inspiration from there,
or even reuse these containers.

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
