
This directory is used to create an Debian distribution package.
The resulting binary and source packages can then be installed in your
Linux distribution.

The packaging is written with the Ubuntu distributions in mind, and 
follows its packaging guidelines:
  See https://wiki.ubuntu.com/PackagingGuide/Complete

NOTE:
The packages do not install or configure the Django user interface yet.

Build instructions:
 - You need to install the packages "cdbs", "debhelper", "pbuilder" and "dh-make".  
 - Enable the Universe repository for your pbuild environment, by creating a
   file ~/.pbuilderrc with this line in it:
     COMPONENTS="main restricted universe multiverse"
 - Initialize your build environment with the command:
     sudo pbuild create
 - Build the packages
     make contrib

Additional handy commands:
 - Install a package
     dpkg -i <package>
 - Remove a package
     dpkg -r <package>
 - Lists the binary package to which a particular file belongs. 
     dpkg -S 
 - Lists currently installed packages. 
     dpkg -l 
 - Lists the contents of a binary package. 
   It is useful for ensuring that files are installed to the right places. 
     dpkg -c <package> 
 - Shows the control file for a binary package. 
   It is useful for ensuring that the dependencies are correct. 
     dpkg -f <package> 
