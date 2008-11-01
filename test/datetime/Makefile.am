#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = datetime

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

datetime_SOURCES = main.cpp
datetime_LDADD   = ../../src/libfrepple.la

EXTRA_DIST = main.cpp datetime.expect

CLEANFILES = *.out *.gcda *.gcov *.gcno
