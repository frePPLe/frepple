#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = problems

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

problems_SOURCES = main.cpp
problems_LDADD   = ../../src/libfrepple.la
EXTRA_DIST = problems.xml problems.expect

CLEANFILES = output.* *.gcda *.gcov *.gcno test.out
