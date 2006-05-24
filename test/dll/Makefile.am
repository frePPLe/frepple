#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = dll

AM_CPPFLAGS=-I@top_builddir@/include

dll_SOURCES = main.cpp
dll_LDADD   = ../../src/libfrepple.la

CLEANFILES = output.* *.stackdump core *.gcda *.gcov *.gcno
