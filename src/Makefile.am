#
# Process this file with automake to produce Makefile.in
#

bin_PROGRAMS = frepple frepple_static

# The local target builds the main executables first, and then copies the
# output to the bin directory
all-local: frepple$(EXEEXT) frepple_static$(EXEEXT)
	cp frepple$(EXEEXT) frepple_static$(EXEEXT) ../bin

AM_CPPFLAGS=-I@top_builddir@/include

# Dynamically linked executable
frepple_SOURCES = main.cpp
frepple_LDFLAGS = -dynamic -export-dynamic
frepple_LDADD = ./libfrepple.la

# Statically linked executable
frepple_static_SOURCES = main.cpp
frepple_static_LDFLAGS = -static -export-dynamic
frepple_static_LDADD = ./libfrepple.la

# Shared library
lib_LTLIBRARIES = libfrepple.la
libfrepple_la_SOURCES = dllmain.cpp tags.cpp
libfrepple_la_LDFLAGS = -version-info @LIBRARY_VERSION@
libfrepple_la_LIBADD = ./solver/libsolver.la ./model/libmodel.la ./utils/libutils.la

SUBDIRS = utils model solver modules

EXTRA_DIST = frepple.def dll.rc exe.rc

CLEANFILES = *.gcda *.gcov *.gcno
