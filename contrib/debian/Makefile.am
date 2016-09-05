#
# Process this file with automake to produce Makefile.in
#

DEBIANFILES = changelog compat control copyright frepple*.install frepple.postinst frepple.postrm rules watch
EXTRA_DIST = README.txt httpd.conf $(DEBIANFILES)

clean-local:
	-rm -rf frepple_* frepple-$(VERSION) *.deb DEBIAN

# This make target builds a Debian distribution file, suitable for Ubuntu.
contrib:
	cd ../..; make dist
	cp ../../frepple-$(VERSION).tar.gz frepple_$(VERSION).orig.tar.gz
	-rm -rf frepple-$(VERSION)
	tar -xzf frepple_$(VERSION).orig.tar.gz
	mkdir -p frepple-$(VERSION)/debian/source
	cp $(DEBIANFILES) frepple-$(VERSION)/debian
	echo '3.0 (quilt)' > frepple-$(VERSION)/debian/source/format
	cd frepple-$(VERSION) && dpkg-buildpackage -us -uc -D
