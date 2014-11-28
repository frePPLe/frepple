
               BUILD INSTRUCTIONS ON WINDOWS
               -----------------------------
              USING MICROSOFT VISUAL C++ 2008
              -------------------------------

The frePPLe source distribution comes with Microsoft Visual C++ projects and
workspaces to build the package. This document contains instructions on how to
use these workspaces and some notes specific to the use of this compiler.

Using more recent versions of Visual Studio will NOT work: Python and its
extension modules are all compiled with Visual C++ 2008, and the frePPle
needs to use the same compiler and C runtime libraries.


PREREQUISITES
-------------

1. Install Visual Studio 2008 (aka vc9)
2. Install xerces-c 3.*
   Installing the 32-bit pre-compiled binaries for vc9 are easiest.
3. Install Python 2.7.*


BUILD INSTRUCTIONS FROM THE COMMAND LINE
----------------------------------------

A convenience build script is provided to compile frePPle.

1. Edit the file build.bat
   The following variables need to be edited:
     - VC: Installation directory of Visual Studio C++ 2008
     - PYTHON: Installation directory of the Python language
     - XERCES: Installation directory of the Xerces-C library
     - GLPK:  *Optional.* Installation directory of the GNU Linear Programming Kit

2. Execute the build.bat command
   The following options can be given on the command line:
      -r:  completely "rebuild" the solution, rather than "build".
      -d:  create a "debug" version, rather than a "release" version


BUILD INSTRUCTIONS FROM THE IDE
-------------------------------

The following describes the steps you need to build frePPLe.

1. Add the xerces-c and python include and library directory to the paths
   used in your Visual C++ environment.

2. Double-click the solution file "contrib/vc/frepple.sln".

4. The configuration 'release' builds the projects 'main' (console application)
   'dll' (shared library), as well as the mail modules.

5. *Optionally* you may want to use the linear programming module.
   If so, install "glpk" and configure its paths in VC++.

6. When using the application, the path should be set such that
   the module libraries are found in the path.
   The easiest way is to have these files in the same directory as the
   application.
