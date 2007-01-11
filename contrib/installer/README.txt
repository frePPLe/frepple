
This is a script for creating a windows installer.
To run the installer, the following steps are required:

1) Install NSIS v2.7 or higher (Nullsoft Scriptable Install System)
   This is a free package to create installers.
   Further details on http://nsis.sourceforge.net/

2) Cygwin environment.
   This is because the creation of the installer starts by making the same
   distribution tar-ball as for *nix environments.
   It is recommended to create the distribution file manually from a cygwin
   shell. The installer will create the distribution too but I found this
   method is not reliable.

3) Microsoft C++ compiler
   We distribute the executables created by the microsoft compilers.

4) Before building the installer script you'll need to update the frepple.nsi
   script to point to the directory where the xerces-c dll is stored.

IMPORTANT NOTE:
The windows installer is not the preferred way of distributing Frepple. It
is only provided as a convenience for Windows-based users.
The proper way remains the source tar-ball.
