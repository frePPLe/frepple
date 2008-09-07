#
# Process this file with automake to produce Makefile.in
#

AM_CPPFLAGS=-I@top_builddir@/include -DDATADIRECTORY='"@datadir@"' -DLIBDIRECTORY='"@libdir@"'

CLEANFILES = *.gcda *.gcov *.gcno

noinst_LTLIBRARIES = libutils.la
libutils_la_SOURCES = date.cpp xmlparser.cpp actions.cpp library.cpp name.cpp
