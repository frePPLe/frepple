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

