#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = src modules include test contrib bin doc

EXTRA_DIST = AUTHORS COPYING ChangeLog INSTALL README NEWS Makefile.am Makefile.dist
AUTOMAKE_OPTIONS = gnu

.PHONY: $(.PHONY) contrib

contrib:
	cd contrib; $(MAKE) contrib; cd ..

clean-local:
	-rm -rf install-test *.exe

# Avoid packaging any subversion subdirectories that may be left over
dist-hook:
	-rm -rf `find $(top_distdir) -name '.svn' -type d`

# Create an rpm distribution
rpm:  dist
	sudo cp frepple-$(VERSION).tar.gz /usr/src/redhat/SOURCES
	sudo cp frepple.spec /usr/src/redhat/SPECS/frepple-$(VERSION).spec
	sudo rpmbuild -ba /usr/src/redhat/SPECS/frepple-$(VERSION).spec
