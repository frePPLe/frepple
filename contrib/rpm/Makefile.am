#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = README.txt frepple.spec 
CLEANFILES = *.rpm

contrib: 
	cd ../..; make dist
	sudo cp ../../frepple-$(VERSION).tar.gz /usr/src/redhat/SOURCES
	sudo cp frepple.spec /usr/src/redhat/SPECS/frepple-$(VERSION).spec
	sudo rpmbuild -ba /usr/src/redhat/SPECS/frepple-$(VERSION).spec
	cp /usr/src/redhat/RPMS/*/frepple-*$(VERSION)*rpm .
	cp /usr/src/redhat/SRPMS/frepple-$(VERSION)* .

# Review the resulting RPMs: list the content, show dependencies
inspect-rpm:
	rpm -qpil *.rpm
	rpm -qpR *.rpm

install-rpm:
	sudo rpm --nodeps --install frepple-$(VERSION)-1.i386.rpm

uninstall-rpm:
	sudo rpm --erase frepple
