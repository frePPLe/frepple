#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = src include test doc contrib bin lib

EXTRA_DIST = AUTHORS COPYING ChangeLog INSTALL README NEWS Makefile.am Makefile.dist
AUTOMAKE_OPTIONS = gnu

.PHONY: $(.PHONY) contrib

contrib:
	cd contrib; $(MAKE) contrib; cd ..

clean-local:
	-rm -rf install-test
