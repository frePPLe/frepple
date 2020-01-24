#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.spec httpd.conf dockerfile
CLEANFILES = *.rpm *.gz requirements.txt *.deb

TAGNAME = rhel-8

$(top_builddir)/frepple-$(VERSION).tar.gz: 
	cd $(top_builddir); make dist


# THE ENVIRONMENT VARIABLE RHEL_USER AND RHEL_PASSWORD NEED TO BE SET.
# OTHERWISE DOCKER HAS NO ACCESS TO THE RED HAT REPOSITORIES.

contrib: $(top_builddir)/frepple-$(VERSION).tar.gz
	cp $(top_builddir)/frepple-$(VERSION).tar.gz $(VERSION).tar.gz
	cp $(top_builddir)/requirements.txt .
	docker build --tag $(TAGNAME)-builder:$(VERSION) --target builder \
          --build-arg RHEL_USER=$(RHEL_USER) \
          --build-arg RHEL_PASSWORD=$(RHEL_PASSWORD) .
	docker cp `docker create $(TAGNAME)-builder:$(VERSION)`:/home/builder/rpm/RPMS/x86_64/frepple-$(VERSION)-1.el8.x86_64.rpm $(TAGNAME)-frepple-$(VERSION)-1.el8.x86_64.rpm
	rm $(VERSION).tar.gz requirements.txt
