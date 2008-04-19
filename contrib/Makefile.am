#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = vc scripting installer rpm django

contrib:
	for dir in $(SUBDIRS); do cd $$dir; $(MAKE) contrib; cd ..; done
