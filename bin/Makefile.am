#
# Process this file with automake to produce Makefile.in
#

nobasedir = $(datadir)/frepple
nobase_DATA = frepple.xsd frepple_core.xsd init.xml
pkgsysconfdir = $(sysconfdir)/frepple
pkgsysconf_DATA = license.xml

install-data-hook:
	cd "$(DESTDIR)$(datadir)/frepple" && $(LN_S) "$(pkgsysconfdir)/license.xml" license.xml

EXTRA_DIST = $(nobase_DATA) $(pkgsysconf_DATA)

clean-local:
	-rm -rf *.tds *.exe *.lib *.pdb *.dll *.so *.so.* *.exp *.tds *.BAK *.ilk mod_*.xsd *.out output*.* frepple *.log *.sqlite
