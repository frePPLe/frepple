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

* **Visual Studio C++ 2010**.

  The express edition is sufficient.

  Using more recent versions of Visual Studio will NOT work: Python3 and
  its extension modules are all compiled with Visual C++ 2010, and frePPle
  needs to use the same compiler and C runtime libraries.

* **Python 3.2, 3.3 or 3.4**
  Python 3.5 is NOT supported yet on Windows, as it requires a different
  compiler version. (Note that Python 3.5 is supported for the linux version)

* **Xerces-C 3.1**

  Best is to install the precompiled binaries for vc9.

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
The Cygwin build is not recommended for production environments, but should be
seen as a test and development setup for a Linux environment.
