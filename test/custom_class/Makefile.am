#
# Process this file with automake to produce Makefile.in
#

check_PROGRAMS = custom_class

AM_CPPFLAGS=-I@top_builddir@/include

custom_class_SOURCES = main.cpp
custom_class_LDADD   = ../../src/libfrepple.la
custom_class_LDFLAGS = -static

EXTRA_DIST = main.cpp custom_class.expect custom_class.h custom_class.xml init.xml frepple.xsd

CLEANFILES = output.* *.stackdump core *.gcda *.gcov *.gcno *.out

