#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = vc scripting borland excel installer webservice j2ee apache 

contrib:
	for dir in $(SUBDIRS); do cd $$dir; $(MAKE) contrib; cd ..; done
