#
# Process this file with automake to produce Makefile.in
#

APACHECTL = ~/httpd/bin/apachectl
APXS = ~/httpd/bin/apxs
PWD = ~/workspace/frepple/contrib/apache

EXTRA_DIST = htdocs mod_frepple.cpp frepple.conf README.TXT filter.cpp mod_frepple.h
CLEANFILES = *.o *.dll *.la *.slo

contrib: stop compile start

stop:
	${APACHECTL} -k stop -f ${PWD}/frepple.conf

compile: mod_frepple.cpp filter.cpp  mod_frepple.h
	g++ -c -fPIC -I`$(APXS) -q INCLUDEDIR` -I../../include filter.cpp
	g++ -c -fPIC -I`$(APXS) -q INCLUDEDIR` -I../../include mod_frepple.cpp
	g++ -shared -fPIC -I`$(APXS) -q INCLUDEDIR` -I../../include filter.o mod_frepple.o ../../src/.libs/libfrepple.a -lxerces-c -o mod_frepple.so
	cp mod_frepple.so /home/johan/httpd/modules/mod_frepple.so
#	${APXS} -i -n frepple_module mod_frepple.so

start:
	${APACHECTL} -k start -f ${PWD}/frepple.conf

restart:
	${APACHECTL} -k restart -f ${PWD}/frepple.conf

# These are the commands I used to compile my own Apache server.
# The Apache server coming with my linux distribution didn't have a good MPM.
# The commands below are an example only...
compile_apache:
	cd /home/johan/workspace/httpd-2.0.55
	configure -with-mpm=worker --prefix=/home/johan/httpd --enable-deflate --disable-include --disable-env --enable-headers --disable-cgi --disable-cgid --enable-so
	make
	make install
