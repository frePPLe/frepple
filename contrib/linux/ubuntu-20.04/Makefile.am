#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = dockerfile debian
CLEANFILES = *.rpm *.gz requirements.txt *.deb

TAGNAME = ubuntu-18.04
BUILD = 1

$(top_builddir)/frepple-$(VERSION).tar.gz: 
	cd $(top_builddir); make dist

contrib: $(top_builddir)/frepple-$(VERSION).tar.gz
	cp $(top_builddir)/frepple-$(VERSION).tar.gz frepple_$(VERSION).orig.tar.gz
	cp $(top_builddir)/requirements.txt .
	sed -i '/lxml/d' requirements.txt
	docker build --tag frepple-$(TAGNAME)-builder:$(VERSION) --target builder .
	docker cp `docker create frepple-$(TAGNAME)-builder:$(VERSION)`:frepple_$(VERSION)-$(BUILD)_amd64.deb $(TAGNAME)-frepple_$(VERSION)_$(BUILD).amd64.deb
	docker cp `docker create frepple-$(TAGNAME)-builder:$(VERSION)`:frepple-doc_$(VERSION)-$(BUILD)_all.deb $(TAGNAME)-frepple-doc_$(VERSION)-$(BUILD)_all.deb
	docker build --tag frepple-$(TAGNAME):$(VERSION) .
	rm frepple_$(VERSION).orig.tar.gz
