#
# Process this file with automake to produce Makefile.in
#

bin_PROGRAMS = frepple

# The local target builds the main executables first, and then copies the
# output to the bin directory
all-local: frepple$(EXEEXT)
	cp frepple$(EXEEXT) ../bin
	cp .libs/libfrepple.so* ../bin

AM_CPPFLAGS=-I@top_builddir@/include

# Shared library
lib_LTLIBRARIES = libfrepple.la
libfrepple_la_SOURCES = dllmain.cpp tags.cpp
libfrepple_la_LDFLAGS = -version-info @LIBRARY_VERSION@ -no-undefined
libfrepple_la_LIBADD = ./solver/libsolver.la ./model/libmodel.la ./utils/libutils.la

# Dynamically linked executable
frepple_SOURCES = main.cpp
frepple_LDFLAGS = -dynamic -export-dynamic
frepple_LDADD = libfrepple.la

SUBDIRS = utils model solver

EXTRA_DIST = dll.rc exe.rc

CLEANFILES = *.gcda *.gcov *.gcno
