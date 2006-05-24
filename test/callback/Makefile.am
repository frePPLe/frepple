#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = callback

AM_CPPFLAGS=-I@top_builddir@/include

callback_SOURCES = main.cpp
callback_LDADD   = ../../src/libfrepple.la
EXTRA_DIST = callback.xml callback.expect

CLEANFILES = output.* *.gcda *.gcov *.gcno
