
This is a script for creating a windows installer for frePPLe.
To run the installer, the following steps are required:

1) Install NSIS v2.41 or higher (Nullsoft Scriptable Install System)
   This is a free package to create installers.
   Further details on http://nsis.sourceforge.net/

2) Install Cygwin environment and run "make dist"
   This is because the creation of the installer starts by making the same
   distribution tar-ball as for *nix environments.
   It is recommended to create the distribution file manually from a Cygwin
   shell. The installer will create the distribution too but I found this
   method is not reliable.

3) Compile the execuatbles with Microsoft C++ compiler
   We distribute the executables created by the microsoft compilers.
   You'll need to compile before creating the installer.

4) Install python
   Make sure to use the Windows version of Python, rather than the one included
   with Cygwin.
   Adjust the path appropriately, if required.

5) Install the python modules py2exe and cherrypy.
   The installer uses py2exe to create a directory including python, django
   and the frepple web user interface.
   As the standalone web server we use WSGIServer that is provided by the
   CherryPy project. It is a bit more scalable and robust than the Django
   development server.

6) Create sample sqlite database
   The installer will pick up the sqlite database in the file bin\frepple.sqlite.
   You'll should make sure it is initialized correctly and contains only the
   sample dataset.

7) Before building the installer script you'll need to update the frepple.nsi
   script to point to the directory where the xerces-c dll is stored.

CONSIDERING ALL THE ABOVE, BUILDING THE INSTALLER ISN'T FOR BEGINNERS. IT
REQUIRES IN DEPTH UNDERSTANDING OF ALL COMPONENTS AND THEIR USAGE IN FREPPLE...
