#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = *.expect pegging.xml

CLEANFILES = output.* *.stackdump core *.gcda *.gcov *.gcno

check_PROGRAMS = pegging

AM_CPPFLAGS=-I@top_builddir@/include

pegging_SOURCES = main.cpp
pegging_LDADD   = ../../src/libfrepple.la
pegging_LDFLAGS = -static
