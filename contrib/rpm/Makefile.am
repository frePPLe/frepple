#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = README.txt frepple.spec 
CLEANFILES = *.rpm

# This make target builds the RPMs on Fedora.
#
# You need to have the "rpmdevtools" package installed and you need to 
# initialize your build environment with the command "rpmdev-setuptree".
#
# See http://fedoraproject.org/wiki/PackageMaintainers/CreatingPackageHowTo
#
contrib: 
	cd ../..; make dist
	cp ../../frepple-$(VERSION).tar.gz ~/rpmbuild/SOURCES
	rm -fr ~/rpmbuild/BUILD/frepple-*$(VERSION) 
	rm -fr ~/rpmbuild/BUILDROOT/frepple-*$(VERSION) 
	cp frepple.spec ~/rpmbuild/SPECS/frepple-$(VERSION).spec
	rpmbuild -ba ~/rpmbuild/SPECS/frepple-$(VERSION).spec
	cp ~/rpmbuild/RPMS/*/frepple-*$(VERSION)*rpm .
	cp ~/rpmbuild/SRPMS/frepple-$(VERSION)* .

# Additional handy commands
# - Install an RPM
#    sudo rpm --nodeps --install frepple-$(VERSION)-1.*.rpm
# - Uninstall an RPM
#    sudo rpm --erase frepple
# - List the content of an RPM
#    rpm -qpil *.rpm
# - Show the dependencies of an RPM
#    rpm -qpR *.rpm
