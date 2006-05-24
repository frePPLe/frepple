#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = cluster

AM_CPPFLAGS=-I@top_builddir@/include

cluster_SOURCES = main.cpp
cluster_LDADD   = ../../src/libfrepple.la

EXTRA_DIST = input.xml

CLEANFILES = test.out *.gcda *.gcov *.gcno
