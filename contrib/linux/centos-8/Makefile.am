#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.spec httpd.conf dockerfile
CLEANFILES = *.rpm *.gz requirements.txt *.deb

TAGNAME = centos-8

$(top_builddir)/frepple-$(VERSION).tar.gz: 
	cd $(top_builddir); make dist

contrib: $(top_builddir)/frepple-$(VERSION).tar.gz
	cp $(top_builddir)/frepple-$(VERSION).tar.gz $(VERSION).tar.gz
	cp $(top_builddir)/requirements.txt .
	docker build --tag $(TAGNAME)-builder:$(VERSION) --target builder .
	docker cp `docker create $(TAGNAME)-builder:$(VERSION)`:/home/builder/rpm/RPMS/x86_64/frepple-$(VERSION)-1.x86_64.rpm $(TAGNAME)-frepple-$(VERSION)-1.x86_64.rpm
	rm $(VERSION).tar.gz
