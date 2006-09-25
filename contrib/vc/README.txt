
               BUILD INSTRUCTIONS ON WINDOWS
               -----------------------------
              USING MICROSOFT VISUAL C++ 2005
              -------------------------------

The Frepple source distribution comes with Microsoft Visual C++ projects and
workspaces to build Frepple. This document contains instructions on how to
use these workspaces and some notes specific to the use of this compiler.

The project configuration files are generated with version 8 of Visual C++. 
Unfortunately these are not compatible with earlier releases :-(  :-( :-(
A free version, called "Visual C++ 2005 Express Edition", can be downloaded from
the Microsoft website.


BUILD INSTRUCTIONS
------------------

The following describes the steps you need to build Frepple.

1. Install xerces-c and follow the build instructions for the Visual C++.
   The binary release package of Xerces-c may have been built with an
   earlier release of Visual C++ and it is therefore recommended to recompile
   xerces-c from the source code.

2. Make sure to add the xerces-c include and library directory to the paths
   used in your Visual C++ environment.

3. Double-click the solution file "contrib/vc/frepple.sln".

4. Build the project 'main' or 'main_static' to get the console application.
   Build the project 'dll' to get the dynamic library.

5. When using the executable, remember to include the xercess dll directory
   in the path.

6. If you also want to build the interface to other languages, you'll also need 
   to install 'swig'.
   The properties of the project 'swig' need to be updated to add the include 
   and library directories of the language you're compiling for.
   The swig executable should be added to your path too.
   Select the configuration 'Release_and_Swig' when compiling the library, since
   the other configurations simply skip the swig build.

NOTES
-----

* All code generated is based on multi-threaded execution.
  When compiling a single-threaded application or DLL, you'll need to:
    - change these code generation option for all projects
    - remove the preprocessor variable MT from the projects
