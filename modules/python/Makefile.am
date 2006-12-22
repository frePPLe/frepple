#
# Process this file with automake to produce Makefile.in
#

sources = embeddedpython.cpp embeddedpython.h

EXTRA_DIST = $(sources)

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

CLEANFILES = *.gcda *.gcov *.gcno

if PYTHON
lib_LTLIBRARIES = libmodpython.la
libmodpython_la_SOURCES = $(sources)
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
libmodpython_la_LDFLAGS = -module -no-undefined 
libmodpython_la_LIBADD = ../../src/libfrepple.la
else
libmodpython_la_LDFLAGS = -module
endif
endif
