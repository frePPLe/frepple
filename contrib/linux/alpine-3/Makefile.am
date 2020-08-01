#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = dockerfile
CLEANFILES = *.gz requirements.txt

TAGNAME = alpine-3
BUILD = 1

$(top_builddir)/frepple-$(VERSION).tar.gz: 
	cd $(top_builddir); make dist

contrib: $(top_builddir)/frepple-$(VERSION).tar.gz
	cp $(top_builddir)/frepple-$(VERSION).tar.gz .
	cp $(top_builddir)/requirements.txt .
	sed -i '/lxml/d' requirements.txt
	docker build --tag frepple-$(TAGNAME)-builder:$(VERSION) --target builder .
	docker build --tag frepple-$(TAGNAME):$(VERSION) . 
	rm frepple*$(VERSION)*.tar.gz requirements.txt
