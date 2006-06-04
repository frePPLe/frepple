#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = datetime

AM_CPPFLAGS=-I@top_builddir@/include

datetime_SOURCES = main.cpp
datetime_LDADD   = ../../src/utils/libutils.la

EXTRA_DIST = main.cpp datetime.expect

CLEANFILES = *.out *.gcda *.gcov *.gcno
