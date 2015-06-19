
This is a script for creating a windows installer for frePPLe.
To create the installer, the following steps are required:

1) Install NSIS v3.0 or higher (Nullsoft Scriptable Install System)
   This is a free package to create installers.
   Further details on http://nsis.sourceforge.net/

2) Activate the following plugins by copying them from the
   <NSIS>\plugins\x86-ansi folder to <NSIS>\plugins\:
     - AccessControl
     - InstallOptions

3) Install Cygwin environment and run "make dist"
   This is because the creation of the installer starts by making the same
   distribution tar-ball as for *nix environments.
   It is recommended to create the distribution file manually from a Cygwin
   shell. The installer will create the distribution too but I found this
   method is not reliable.

4) Compile the executables with Microsoft C++ compiler.
   We distribute the executables created by the Microsoft compilers.
   You'll need to compile before creating the installer.

5) Install Python
   Make sure to use the Windows version of Python, rather than the one included
   with Cygwin.
   Adjust the path appropriately, if required.

6) Install the following Python extensions:
      - py2exe, for Python 3, >= 0.9.2.2
      - django (needs patching!)
      - cherrypy
      - psycopg2
      - pywin32
   The installer uses py2exe to create a directory containing the Python
   language (with its libraries and extensions) and the frePPLe web user
   interface.
   As the standalone web server we use WSGIServer that is provided by the
   CherryPy project. It is a bit more scalable and robust than the Django
   development server.

7) Before building the installer script you'll need to update the frepple.nsi
   script to point to the directory where the xerces-c dll is stored.

CONSIDERING ALL THE ABOVE, BUILDING THE INSTALLER ISN'T FOR BEGINNERS.
IT REQUIRES PROPER UNDERSTANDING OF ALL COMPONENTS AND THE FREPPLE BUILD PROCESS...
