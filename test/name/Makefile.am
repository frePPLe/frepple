#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = name

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

name_SOURCES = main.cpp
name_LDADD   = ../../src/libfrepple.la

EXTRA_DIST = name.expect

CLEANFILES = output.* *.gcda *.gcov *.gcno
