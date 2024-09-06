=====================
Using a Dev-Container
=====================

The instructions on this page describe how to start developing from a Dev-Container 
in your host machine.

This is the reccomended and fastest way to start developing in frePPLe.

It just requires docker (and optionally docker-compose) installed on the host machine, 
and Visual Studio Code with the Dev Containers extension.

It was developed and tested using Visual Studio Code from Microsoft.

In the folder ".devcontainer" you will find the devcontainer json file.
This file points to a Dockerfile where the container image is defined.

Optionally there is a docker-compose file to set up a DB in the case you
are missing a DB in your host machine.

#. Pick up the latest code from the repository:
   ::

     git clone https://github.com/frePPLe/frePPLe.git <project_directory>

#. Initialize the build environment


   Make sure you have VS Code with Dev Containers extension installed.
   
   When you open the project folder VS Code should prompt you to start the Dev-Container. 
   This should trigger a series of steps and can take a couple of minutes.

   If you are starting from a fresh image the C++ code compilation will be triggered. 
   The CMakeLists.txt file has some logic to detect your Linux distribution
   and configure the build script.

   The initialization step will also check for all required build software and
   report any missing packages.

#. Build the software

   The previous step should have already done the compilation but, 
   in case you need to do it yourself, the instructions are simple.

   In VS Code, with the cmake extension installed, just build all the targets.

#. Optional, start a DB container.

   If you do not have a DB in your host machine this step will create a working 
   PostgreSQL DB, with persistent data, in a docker container.
   The data is stored in your home folder inside "freppledata" folder

   In a terminal window in your host machine:

   ::

     cd <project_directory>/.devcontainer
     docker-compose up

   If the DB is fresh you must not forget to create all the tables by
   running (in a Dev-Container terminal):

   ::

     cd <project_directory>
     frepplectl.py migrate

   If the DB cannot be found you should check the IP address of your Dev-Container.
   It should be something like 172.17.0.2 and, in this case, for the
   Dev-Container your host machine is at 172.17.0.1. This address should be 
   in your "djangosettings.py" DB settings or, even better, in a "localsettings.py"
   file where you can override the default djangosettings values.

#. Start frePPLe server:

   If the DB tables are already present you can start the development server:

   ::

     cd <project_directory>
     frepplectl.py runserver

   At this point you should be able to open http://127.0.0.1:8000 from a browser 
   in the host machine.

   You are now ready to start developing.

