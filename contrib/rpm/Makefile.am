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
	cp /usr/src/redhat/RPMS/*/frepple-$(VERSION)* .
	cp /usr/src/redhat/RPMS/*/frepple-debuginfo-$(VERSION)* .
	cp /usr/src/redhat/SRPMS/frepple-$(VERSION)* .

install-rpm:
	sudo rpm --nodeps --install frepple-0.1.3-1.i386.rpm

uninstall-rpm:
	sudo rpm --erase frepple
