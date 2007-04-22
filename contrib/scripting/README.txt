
This is a script for generating access to the frepple library from a number of
scripting languages, such as Perl, Python, Tcl/Tk, Ruby, etc
You'll the SWIG (Simplified Wrapper Interface Generator) tool for using this.
See http://swig.sourceforge.net/ for more information.

Out of the many languages supported by SWIG, I am working with the Perl,
Python and java languages.

The following describes the steps to execute:

1) Install SWIG.
   You'll also need to install the development version of the language you want
   to interface with. For java this means you need JDK, while for perl and python
   the required files are included with a standard installation.

2) Run 'make java'
   Or run 'make python'
   Or run 'make perl'
   The steps in the makefile are first running swig to generate the interface
   wrapper code, and then compile the results.
   You may need to update the file makefile.am to update the paths to the
   language directories and/or compilation parameters.

   For java on windows there is a Visual Studio project that runs swig and
   compiles the wrapper code. You'll need to configure Visual Studio to add the
   following directories in the search paths:
     a) <SDK>/bin in executable directory path
     b) <SDK>/lib in library directory path
     c) <SDK>/include in include directory path

3) To execute the examples you'll need to make sure the frepple shared library
   and the modules are available in your path.
   For perl and python this is easiest done by adding $FREPPLE_HOME and . to the
   shared library path.
   For java this requires using the option "-Djava.library.path=[YOURDIR]" on the
   java command line. Java searches this path when loading native libraries.
