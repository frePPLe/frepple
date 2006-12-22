#
# Process this file with automake to produce Makefile.in
#

sources = lpsolver.cpp lpsolver.h

EXTRA_DIST = $(sources)

if LP
libmodlpsolver_la_SOURCES = $(sources)
lib_LTLIBRARIES = libmodlpsolver.la
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
libmodlpsolver_la_LDFLAGS = -module -no-undefined
libmodlpsolver_la_LIBADD = ../../src/libfrepple.la
else
libmodlpsolver_la_LDFLAGS = -module
endif
endif

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno
