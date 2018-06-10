#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = README.txt frepple.spec httpd.conf
CLEANFILES = *.rpm

# This make target builds the RPMs, suitable for Fedora.
contrib:
	cd ../..; make dist
	cp ../../frepple-$(VERSION).tar.gz ~/rpmbuild/SOURCES/$(VERSION).tar.gz
	rm -fr ~/rpmbuild/BUILD/frepple-*$(VERSION)
	rm -fr ~/rpmbuild/BUILDROOT/frepple-*$(VERSION)
	cp frepple.spec ~/rpmbuild/SPECS/frepple.spec
	rpmbuild -ba ~/rpmbuild/SPECS/frepple.spec
	cp ~/rpmbuild/RPMS/*/frepple-*$(VERSION)*rpm .
	cp ~/rpmbuild/SRPMS/frepple-$(VERSION)* .

