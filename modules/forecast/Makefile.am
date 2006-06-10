#
# Process this file with automake to produce Makefile.in
#

sources = forecast.cpp forecast.h

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno

lib_LTLIBRARIES = libforecast.la
libforecast_la_SOURCES = $(sources)
libforecast_la_LDFLAGS = -module 
