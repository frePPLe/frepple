
               BUILD INSTRUCTIONS ON WINDOWS
               -----------------------------
              USING MICROSOFT VISUAL C++ 2008
              -------------------------------

The frePPLe source distribution comes with Microsoft Visual C++ projects and
workspaces to build the package. This document contains instructions on how to
use these workspaces and some notes specific to the use of this compiler.

The project configuration files are generated with version 9 of Visual C++.
Unfortunately these are not compatible with earlier releases :-(  :-( :-(
A free version, called "Visual C++ 2008 Express Edition", can be downloaded from
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

4. The configuration 'release' builds the projects 'main' and 'dll', i.e. the
   console application and the dynamic library.

5. The configuration 'modules' builds the extension modules 'forecast',
   'lp_solver', 'python',... etc.
   Depending on the nature of the module, additional software may need to be
   installed:
     lp_solver requires the glpk toolkit
     python requires the python interpreter
   The Visual C++ include and library paths need to be updated accordingly.

   A BUILD FAILURE IS NOT CIRITICAL. THE MODULE INVOLVED WILL NOT BE AVAILABLE
   BUT THE CORE FREPPLE APPLICATION WILL BE FINE, AND CAN BE USED ON ITS OWN.

6. When using the program, the path should be set such that the xercess dll
   directory and the module libraries are included in the path.
   The easiest approach is to have these files in the same directory as the
   application.

7. If you also want to build the interface to other languages, you'll also need
   to install 'swig'.
   The properties of the project 'swig' need to be updated to add the include
   and library directories of the language you're compiling for.
   The swig executable should be added to your path too.
   Select the configuration 'Release_and_Swig' when compiling the library, since
   the other configurations simply skip the swig build.

