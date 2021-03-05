
This is a script for creating a windows installer for frePPLe.
The following steps are required:

1) Install NSIS v3.0 or higher (Nullsoft Scriptable Install System)
   This is a free package to create installers.
   Further details on http://nsis.sourceforge.net/

2) Activate the following plugin by copying it into the
   <NSIS>\plugins\x86-unicode folder:
     - AccessControl
     
3) Make sure the following Python extensions are installed.
   They are commented out by default in the requirements.txt file:
      - cx_freeze
      - cx_loggin
      - pywin32
      - adodbapi

4) Download the PostgreSQL binaries for 64-bit windows from:
     http://www.enterprisedb.com/products-services-training/pgbindownload
   Unzip the zip-file in the folder pgsql before running the installer.

5) Build the installer with the command:
      cmake --build . --config Release --target installer
