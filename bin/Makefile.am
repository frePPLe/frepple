#
# Process this file with automake to produce Makefile.in
#

nobasedir = $(datadir)/frepple
nobase_DATA = frepple.xsd

pkgsysconfdir = $(sysconfdir)/frepple
pkgsysconf_DATA = license.xml

EXTRA_DIST = $(nobase_DATA) $(pkgsysconf_DATA)

clean-local:
	-rm -rf *.tds *.exe *.lib *.pdb *.dll *.pyd *.so *.so.* *.exp *.tds *.BAK *.ilk mod_*.xsd *.out output*.* frepple *.log
