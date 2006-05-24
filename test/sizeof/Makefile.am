#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = sizeof

AM_CPPFLAGS=-I@top_builddir@/include

sizeof_SOURCES = main.cpp
sizeof_LDADD   = ../../src/libfrepple.la
sizeof_LDFLAGS = -static

EXTRA_DIST = main.cpp sizeof.expect

CLEANFILES = output.* *.stackdump core *.gcda *.gcov *.gcno
