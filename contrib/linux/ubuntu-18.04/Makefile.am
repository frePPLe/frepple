#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = dockerfile debian
CLEANFILES = *.rpm *.gz requirements.txt *.deb

TAGNAME = ubuntu-18.04

$(top_builddir)/frepple-$(VERSION).tar.gz: 
	cd $(top_builddir); make dist

contrib: $(top_builddir)/frepple-$(VERSION).tar.gz
	cp $(top_builddir)/frepple-$(VERSION).tar.gz frepple_$(VERSION).orig.tar.gz
	cp $(top_builddir)/requirements.txt .
	docker build --tag $(TAGNAME)-builder:$(VERSION) --target builder .
	docker cp `docker create $(TAGNAME)-builder:$(VERSION)`:frepple_$(VERSION)-1_amd64.deb $(TAGNAME)-frepple_$(VERSION)_1.amd64.deb
	rm frepple_$(VERSION).orig.tar.gz
