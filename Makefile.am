#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = src include test contrib bin doc

EXTRA_DIST = AUTHORS COPYING ChangeLog INSTALL README README.md NEWS Makefile.am Makefile.dist
AUTOMAKE_OPTIONS = gnu

.PHONY: $(.PHONY) contrib

contrib:
	cd contrib; $(MAKE) contrib; cd ..

clean-local:
	-rm -rf install-test *.exe

# Remove our custom subdirectories
uninstall-local:
	-rm -rf $(DESTDIR)$(datadir)/frepple $(DESTDIR)$(libdir)/frepple

# Avoid packaging any git directory that may be left over
dist-hook:
	-rm -rf `find $(top_distdir) -name '.git' -type d`
