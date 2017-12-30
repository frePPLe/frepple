#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = vc installer rpm debian odoo docker

contrib:
	for dir in $(SUBDIRS); do cd $$dir; $(MAKE) contrib; cd ..; done
