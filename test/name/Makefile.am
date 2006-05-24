#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = name name2

AM_CPPFLAGS=-I@top_builddir@/include

name_SOURCES = main.cpp
name_LDADD   = ../../src/libfrepple.la
name_LDFLAGS = -static

# @todo let name test run with the dynamically linked file
name2_SOURCES = main.cpp
name2_LDADD   = ../../src/libfrepple.la

EXTRA_DIST = main.cpp name.expect

CLEANFILES = output.* *.gcda *.gcov *.gcno
