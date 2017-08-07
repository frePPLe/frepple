
This directory is used to create an RPM distribution.
The resulting binary and source packages can then be installed in your
Linux distribution.

The spec-file is written with the Fedora and Red Hat distributions in mind, 
and follows their packaging guidelines:
  See http://fedoraproject.org/wiki/PackageMaintainers/CreatingPackageHowTo
With a little effort it should work fine for Mandrake, SUSE, CentOS, etc...

Build instructions:
 - You need to have the "rpmdevtools" package installed:
     dnf install rpmdevtools
 - Useful other packages are "rpmlint" and "mock". They are not required
   for the build and we won't discuss their use here.
 - Initialize your build environment with the command:
     rpmdev-setuptree
 - Build the packages:
     make contrib
      
A quick reference of some handy commands
 - Install an RPM
    sudo rpm --nodeps --install frepple-$(VERSION)-1.*.rpm
 - Uninstall an RPM
    sudo rpm --erase frepple
 - List the content of an RPM
    rpm -qpil *.rpm
 - Show the dependencies of an RPM
    rpm -qpR *.rpm
