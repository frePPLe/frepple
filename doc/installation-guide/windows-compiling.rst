====================
Compiling on Windows
====================

Two options exist to compile frePPle under windows:

* `Compiling using Microsoft Visual C++ compiler`_

* `Compiling using the Cygwin compiler`_

The binaries created by these compilers are not compatible with each other.

*********************************************
Compiling using Microsoft Visual C++ compiler
*********************************************

FrePPLe comes with Microsoft Visual Studio projects and workspaces to
compile the source code.

You will also need to install:

* **Visual Studio C++ 2015**.

  The express edition is sufficient.

  Using a different version of Visual Studio will NOT work: Python and its
  extension modules are all compiled with Visual C++ 2015, and frePPle
  needs to use the same compiler and C runtime libraries.

* **Python 3.5 or higher**

  Install the 64-bit version of Python 3.

* **Xerces-C 3.1.3**

  You will have to compile this package from source. The xerces-c team
  provides a Visual Studio file that can be used to create a 64-bit static
  library.

The solution file is *contrib/vc/frepple.sln*. The include and library
directories of Python and Xerces-C will need to configured in Visual Studio.

A convenience script *contrib/vc/build.bat* is also provided to compile from
the command line. The script needs to be edited to point to the installation
folders of Python and Xerces-C.

If you also want to create the installer, you will need to install a number of
additional software components. Detailed instructions are found in the file
contrib/installer/README.txt.

***********************************
Compiling using the Cygwin compiler
***********************************

Cygwin is a large collection of GNU and Open Source tools which provide
functionality similar to a Linux distribution on Windows. The Cygwin environment
is available free of charge from http://www.cygwin.com.

The build instructions on Cygwin are identical to the Linux platforms.

The Cygwin executables are considerably slower than the native Windows binaries.
The Cygwin build is not intended for production environments, but should be
seen as a test and development setup for a Linux environment.
