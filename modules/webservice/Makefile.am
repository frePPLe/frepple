#
# Process this file with automake to produce Makefile.in
#

sources = module.cpp server.cpp webservice.cpp

# Install the library in the bin directory.
# Ain't standard practice, but in this way all binaries are consolidated in a
# single directory.
libdir = @bindir@

AM_CPPFLAGS=-I@top_builddir@/include

EXTRA_DIST = $(sources) mod_webservice.xsd module.h webservice.h client.cpp

CLEANFILES = *.gcda *.gcov *.gcno module_webservice* *.req.xml *.res.xml frepple.nsmap frepple.xsd frepple.wsdl fault*


if WEBSERVICE

lib_LTLIBRARIES = mod_webservice.la

## Direct linking with the gsoap library doesn't work for some reason. We need to compile directly the gsoap code.
#mod_webservice_la_CPPFLAGS = -DDEBUG -I../../include
#mod_webservice_la_SOURCES = faultC.cpp soapServerLib.cpp $(sources)
#mod_webservice_la_LIBADD = -lgsoap++
#mod_webservice_la_SOURCES = faultC.cpp module_webserviceServerLib.cpp $(sources) /home/frepple/workspace/gsoap-2.7/soapcpp2/stdsoap2.cpp
mod_webservice_la_SOURCES = $(sources)
mod_webservice_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_webservice_la_LDFLAGS += -no-undefined
#mod_webservice_la_LIBADD += ../../src/libfrepple.la
endif

module_webserviceServerLib.cpp: webservice.h
	@SOAPCPP2@ webservice.h

faultC.cpp:
	touch fault.h
	@SOAPCPP2@ -pfault fault.h

# An example client application
client: client.cpp module_webserviceServerLib.cpp
	g++ -o client client.cpp faultC.cpp module_webserviceClient.cpp module_webserviceC.cpp /home/frepple/workspace/gsoap-2.7/soapcpp2/stdsoap2.cpp

# not really portable, but does the job on linux
all-local:
if DEBUG
	-cp .libs/mod_webservice.so ../../bin
else
if COVERAGE
	-cp .libs/mod_webservice.so ../../bin
else
if PROFILE
	-cp .libs/mod_webservice.so ../../bin
else
	-cp .libs/mod_webservice.so ../../bin
	-$(STRIP) ../../bin/mod_webservice.so
endif
endif
endif
	cp mod_webservice.xsd ../../bin

endif

clean-local:
	-rm -f ../../bin/mod_webservice.so ../../bin/mod_webservice.xsd

