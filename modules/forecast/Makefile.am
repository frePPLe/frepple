#
# Process this file with automake to produce Makefile.in
#

sources = forecast.cpp forecast.h

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno

lib_LTLIBRARIES = mod_forecast.la
mod_forecast_la_SOURCES = $(sources)
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_forecast_la_LDFLAGS = -module -no-undefined 
mod_forecast_la_LIBADD = ../../src/libfrepple.la
else
mod_forecast_la_LDFLAGS = -module -avoid-version
endif

all-local: 
	cp .libs/mod_forecast.so ../../bin 
	$(STRIP) ../../bin/mod_forecast.so

install-exec-local:
	cp .libs/mod_forecast.so $(bindir)

uninstall-local:
	rm $(bindir)/mod_forecast.so
