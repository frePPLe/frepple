#
# Process this file with automake to produce Makefile.in
#

APACHECTL = ~/httpd/bin/apachectl
APXS = ~/httpd/bin/apxs
PWD = `pwd`

EXTRA_DIST = htdocs mod_frepple.cpp frepple.conf README.txt inventory.cpp mod_frepple.h frepple.key frepple.crt createmodel.pl
CLEANFILES = *.o *.dll *.la *.slo

contrib: stop build start

# Stop the apache server
stop:
	${APACHECTL} -k stop -f ${PWD}/frepple.conf

# Build the frepple apache module
build: mod_frepple.cpp inventory.cpp  mod_frepple.h
	g++ -c -fPIC -DHAVE_CONFIG_H -I../.. -I`$(APXS) -q INCLUDEDIR` -I../../include inventory.cpp
	g++ -c -fPIC -DHAVE_CONFIG_H -I../.. -I`$(APXS) -q INCLUDEDIR` -I../../include mod_frepple.cpp
	g++ -shared -fPIC -I`$(APXS) -q INCLUDEDIR` -I../../include inventory.o mod_frepple.o ../../src/.libs/libfrepple.a -lxerces-c -o mod_frepple.so
#	${APXS} -i -c -n frepple_module -o mod_frepple.so inventory.cpp mod_frepple.cpp  ../../src/.libs/libfrepple.a  -lxerces-c
#	${APXS} -i -n frepple_module mod_frepple.so
# 	Required for SELinux distributions!
#	chcon -c -v -t texrel_shlib_t mod_frepple.so


# Start the apache server
start:
	${APACHECTL} -k start -f ${PWD}/frepple.conf

# These are the commands I used to compile my own Apache server.
# The Apache server coming with my linux distribution didn't have a good MPM.
# The commands below are an example only... (Note that I enabled SSL support 
# which is optional, and which requires you also have the openssl development 
# libraries installed)
build_apache:
	cd ~/workspace/httpd-2.2.*
	configure -with-mpm=worker --prefix=/home/johan/httpd --enable-deflate --disable-include --disable-env --enable-headers --disable-cgi --disable-cgid --enable-so --enable-ssl
	make
	make install

# These is the command I used to create my SSL certificate
# The command below is an example only...
config_ssl:
	openssl req -new -x509 -nodes -days 3650 -keyout frepple.key -out frepple.crt