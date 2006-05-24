#
# Process this file with automake to produce Makefile.in
#

SUBDIRS =

EXTRA_DIST = webservice installer vc borland j2ee scripting apache excel

contrib:
	for dir in $(EXTRA_DIST); do cd $$dir; $(MAKE) contrib; cd ..; done

clean:
	for dir in $(EXTRA_DIST); do cd $$dir; $(MAKE) clean; cd ..; done
