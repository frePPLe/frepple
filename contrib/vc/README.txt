
               BUILD INSTRUCTIONS ON WINDOWS
               -----------------------------
              USING MICROSOFT VISUAL C++ 2010
              -------------------------------

The frePPLe source distribution comes with Microsoft Visual C++ projects and
workspaces to build the package. This document contains instructions on how to
use these workspaces and some notes specific to the use of this compiler.

Using more recent versions of Visual Studio will NOT work: Python and its
extension modules are all compiled with Visual C++ 2010, and frePPle
needs to use the same compiler and C runtime libraries.


PREREQUISITES
-------------

1. Install Visual Studio 2010 SP1 (aka vc10)
2. Install xerces-c 3.1.1*
   Installing the 32-bit pre-compiled binaries for vc10 are easiest.
3. Install Python 3.2 or higher


BUILD INSTRUCTIONS FROM THE COMMAND LINE
----------------------------------------

A convenience build script is provided to compile frePPle.

1. Edit the file build.bat
   The following variables need to be edited:
     - DOTNET: Installation directory of the Microsoft .NET framework
     - VC: Installation directory of Visual Studio C++ 2010
     - PYTHON: Installation directory of the Python language
     - XERCES: Installation directory of the Xerces-C library

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

3. Choose the "release" or "debug" configuration and build the solution.

4. All relevant output binaries are placed in the "bin" folder.
