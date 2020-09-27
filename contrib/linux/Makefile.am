#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = centos-8 debian-10 opensuse-15.1 rhel-8 ubuntu-18.04 ubuntu-20.04 alpine-3

EXTRA_DIST = README.txt

runtime:
	docker-compose up 

.PHONY: contrib

contrib:
	for dir in $(SUBDIRS); do \
	  cd $$dir; \
	  echo $$dir; \
	  $(MAKE) contrib; \
	done
