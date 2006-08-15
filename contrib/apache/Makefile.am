#
# Process this file with automake to produce Makefile.in
#

APACHECTL = ~/httpd/bin/apachectl
APXS = ~/httpd/bin/apxs
PWD = `pwd`

EXTRA_DIST = htdocs mod_frepple.cpp frepple.conf README.txt filter.cpp mod_frepple.h
CLEANFILES = *.o *.dll *.la *.slo

contrib: stop build start

stop:
	${APACHECTL} -k stop -f ${PWD}/frepple.conf

build: mod_frepple.cpp filter.cpp  mod_frepple.h
	g++ -c -fPIC -DHAVE_CONFIG_H -I../.. -I`$(APXS) -q INCLUDEDIR` -I../../include filter.cpp
	g++ -c -fPIC -DHAVE_CONFIG_H -I../.. -I`$(APXS) -q INCLUDEDIR` -I../../include mod_frepple.cpp
	g++ -shared -fPIC -I`$(APXS) -q INCLUDEDIR` -I../../include filter.o mod_frepple.o ../../src/.libs/libfrepple.a -lxerces-c -o mod_frepple.so
#	${APXS} -i -c -n frepple_module -o mod_frepple.so filter.cpp mod_frepple.cpp  ../../src/.libs/libfrepple.a  -lxerces-c
#	${APXS} -i -n frepple_module mod_frepple.so

start:
	${APACHECTL} -k start -f ${PWD}/frepple.conf

restart:
	${APACHECTL} -k restart -f ${PWD}/frepple.conf

# These are the commands I used to compile my own Apache server.
# The Apache server coming with my linux distribution didn't have a good MPM.
# The commands below are an example only...
build_apache:
	cd ~/workspace/httpd-2.2.*
	configure -with-mpm=worker --prefix=/home/johan/httpd --enable-deflate --disable-include --disable-env --enable-headers --disable-cgi --disable-cgid --enable-so
	make
	make install
