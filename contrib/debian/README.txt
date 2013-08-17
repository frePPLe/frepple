
This directory is used to create an Debian distribution package.
The resulting binary and source packages can then be installed in your
Linux distribution.

The packaging is written with the Ubuntu distributions in mind, and 
follows its packaging guidelines:
  See https://wiki.ubuntu.com/PackagingGuide/Complete

Build instructions:
 - You need to install the packages "cdbs", "debhelper", "python-support", "pbuilder".
 - Initialize your build environment with the command:
     sudo pbuilder create
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
