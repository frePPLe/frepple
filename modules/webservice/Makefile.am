#
# Process this file with automake to produce Makefile.in
#

sources = module.cpp server.cpp webservice.cpp

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

EXTRA_DIST = $(sources) module.h webservice.h client.cpp

CLEANFILES = client$(EXEEXT) *.gcda *.gcov *.gcno module_webservice* *.req.xml *.res.xml *.nsmap *.xsd *.wsdl soap*


if WEBSERVICE

serverstubs:
	@SOAPCPP2@ -S webservice.h

lib_LTLIBRARIES = mod_webservice.la
mod_webservicedir = $(datadir)

mod_webservice_la_SOURCES = $(sources) soapC.cpp soapServer.cpp
mod_webservice_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null -lgsoap++
mod_webservice_la_LIBADD = ../../src/libfrepple.la 
mod_webservice_la_DEPENDENCIES = serverstubs

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

