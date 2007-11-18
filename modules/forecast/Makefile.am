#
# Process this file with automake to produce Makefile.in
#

sources = forecast.cpp forecast.h forecastsolver.cpp

# Install the library in the bin directory.
# Ain't standard practice, but in this way all binaries are consolidated in a
# single directory.
libdir = @bindir@

AM_CPPFLAGS=-I@top_builddir@/include

EXTRA_DIST = mod_forecast.xsd $(sources)

CLEANFILES = *.gcda *.gcov *.gcno

if FORECAST

lib_LTLIBRARIES = mod_forecast.la
mod_forecast_la_SOURCES = $(sources)
mod_forecast_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_forecast_la_LDFLAGS += -no-undefined
mod_forecast_la_LIBADD = ../../src/libfrepple.la
endif

all-local:
# not really portable, but does the job on linux
	-cp .libs/mod_forecast.so ../../bin
	-$(STRIP) ../../bin/mod_forecast.so
	cp mod_forecast.xsd ../../bin

install-exec-local:
	cp mod_forecast.xsd $(bindir)

uninstall-local:
	rm $(bindir)/mod_forecast.xsd

endif

clean-local:
	-rm -f ../../bin/mod_forecast.xsd
	-rm -f ../../bin/mod_forecast.so
