
               BUILD INSTRUCTIONS ON WINDOWS
               -----------------------------
               USING MICROSOFT VISUAL STUDIO
               -----------------------------

The Frepple source distribution comes with Microsoft Visual C++ projects and
workspaces to build Frepple. This document contains instructions on how to
use these workspaces and some notes specific to the use of this compiler.

Version 7 or higher of Visual C++ is required.


BUILD INSTRUCTIONS
------------------

The following describes the steps you need to build Frepple.

1. Install xerces-c and follow the build instructions for the Visual
   Studio.

2. Double-click the workspace file contrib/vc/frepple.sln

3. Edit the settings of each of the projects to point to the correct xerces
   include directory and import library.

4. Build the project 'main' or 'main_static' to get the console application.
   Build the project 'dll' to get the dynamic library.

5. When using the executable, remember to include the xercess dll directory
   in the path.

6. If you also want to build the perl interface, you'll need to install 'perl'
   and 'swig'.
   The properties of the project 'swig' need to be updated to add the perl
   include and library directories.
   The swig executable should be added to your path too.
   Select the configuration 'Release_and_Swig' when compiling the library, since
   the other configurations simply skip the swig build.

NOTES
-----

* All code generated is based on single-threaded execution.
  When compiling a multi-threaded application or DLL (which is currently NOT
  supported yet), you'll need to:
    - change these code generation option for all projects
    - define the preprocessor variable MT
