#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = vc installer rpm debian django odoo

contrib:
	for dir in $(SUBDIRS); do cd $$dir; $(MAKE) contrib; cd ..; done
