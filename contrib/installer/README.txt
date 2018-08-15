
This is a script for creating a windows installer for frePPLe.
The following steps are required:

1) Install NSIS v3.0 or higher (Nullsoft Scriptable Install System)
   This is a free package to create installers.
   Further details on http://nsis.sourceforge.net/

2) Patch the NSIS MultiUser.sh script
   The determination of the default installation folder doesn't recognize the
   64-bit program folder.
   You need to replace:
     StrCpy $INSTDIR "$PROGRAMFILES\${MULTIUSER_INSTALLMODE_INSTDIR}"
   with:
     StrCpy $INSTDIR "$PROGRAMFILES64\${MULTIUSER_INSTALLMODE_INSTDIR}"

3) Activate the following plugins by copying them from the
   <NSIS>\plugins\x86-ansi folder to <NSIS>\plugins\:
     - AccessControl
     - InstallOptions

4) Compile the executables with Microsoft C++ compiler.
   You'll need to compile before creating the installer.

5) Install Python 3.5 or higher
   Adjust the path appropriately, if required.

6) Install the following Python extensions.
   First, install the normal dependencies:
     pip3 install -r requirements.txt
     
7)  The installer uses 2 additional packages
      - cx_freeze
      - pywin32
   The installer uses cx_freeze to create a directory containing the Python
   language (with its libraries and extensions) and the frePPLe user
   interface.

8) Download the PostgreSQL binaries for 64-bit windows from:
     http://www.enterprisedb.com/products-services-training/pgbindownload
   Unzip the zip-file in the folder pgsql before running the installer.

CONSIDERING ALL THE ABOVE, BUILDING THE INSTALLER ISN'T FOR BEGINNERS.
IT REQUIRES PROPER UNDERSTANDING OF ALL COMPONENTS AND THE BUILD PROCESS...
