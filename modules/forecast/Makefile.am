#
# Process this file with automake to produce Makefile.in
#

sources = forecast.cpp forecast.h forecastsolver.cpp module.cpp timeseries.cpp pythonforecast.cpp

EXTRA_DIST = mod_forecast.xsd $(sources)

CLEANFILES = *.gcda *.gcov *.gcno

if FORECAST

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

usrlibdir = $(libdir)/frepple
usrlib_LTLIBRARIES = mod_forecast.la
mod_forecastdir = $(datadir)
mod_forecast_DATA = mod_forecast.xsd
mod_forecast_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null -lfrepple
mod_forecast_la_SOURCES = $(sources)

if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_forecast_la_LDFLAGS += -no-undefined
mod_forecast_la_LIBADD = ../../src/libfrepple.la
endif

# A convenience copy to quickly collect the results
all-local:
	-cp .libs/mod_forecast.so ../../bin
	cp mod_forecast.xsd ../../bin

endif

