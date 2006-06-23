#
# Process this file with automake to produce Makefile.in
#

sources = forecast.cpp forecast.h

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno

lib_LTLIBRARIES = libforecast.la
libforecast_la_SOURCES = $(sources)
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
libforecast_la_LDFLAGS = -module -no-undefined
libforecast_la_LIBADD = ../../src/libfrepple.la 
else
libforecast_la_LDFLAGS = -module 
endif
