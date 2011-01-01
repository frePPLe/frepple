#
# Process this file with automake to produce Makefile.in
#

sources = module.cpp server.cpp webservice.cpp

EXTRA_DIST = $(sources) module.h webservice.h client.cpp

CLEANFILES = client$(EXEEXT) *.gcda *.gcov *.gcno module_webservice* *.req.xml *.res.xml *.nsmap *.xsd *.wsdl soap*


if WEBSERVICE

soapC.cpp:
	@SOAPCPP2@ -S webservice.h

BUILT_SOURCES = soapC.cpp soapServer.cpp

pkglib_LTLIBRARIES = mod_webservice.la
mod_webservicedir = $(datadir)/frepple

dist_mod_webservice_la_SOURCES = $(sources)
nodist_mod_webservice_la_SOURCES = soapC.cpp soapServer.cpp
mod_webservice_la_LDFLAGS = -module -shrext .so -avoid-version -lgsoap++
mod_webservice_la_LIBADD = ../../src/libfrepple.la 

if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_webservice_la_LDFLAGS += -no-undefined
endif

# An example client application
client: client.cpp webservice.h
	@SOAPCPP2@ -C webservice.h
	g++ -o client client.cpp soapC.cpp soapClient.cpp -lgsoap++

# A convenience copy to quickly collect the results
all-local:
	-cp .libs/mod_webservice.so ../../bin

endif

