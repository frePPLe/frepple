#
# Process this file with automake to produce Makefile.in
#

bin_PROGRAMS = frepple

# Install the library in the bin directory.
# Ain't standard practice, but in this way all binaries are consolidated in a
# single directory.
libdir = @bindir@

# The local target builds the main executables first, and then copies the
# output to the bin directory
all-local: frepple$(EXEEXT)
	if test -f .libs/frepple$(EXEEXT); then cp .libs/frepple$(EXEEXT) ../bin; fi
	if test -f .libs/cygfrepple*.dll; then cp .libs/cygfrepple*.dll ../bin; fi
	if test -f .libs/libfrepple.so; then cp .libs/libfrepple.so* ../bin; fi

AM_CPPFLAGS=-I@top_builddir@/include

# Shared library
lib_LTLIBRARIES = libfrepple.la
libfrepple_la_SOURCES = dllmain.cpp tags.cpp
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
libfrepple_la_LDFLAGS = -version-info @LIBRARY_VERSION@ -no-undefined -Wl,--export-all-symbols
else
libfrepple_la_LDFLAGS = -version-info @LIBRARY_VERSION@ -no-undefined
endif
libfrepple_la_LIBADD = ./solver/libsolver.la ./model/libmodel.la ./utils/libutils.la

# Dynamically linked executable
frepple_SOURCES = main.cpp
frepple_LDFLAGS = -dynamic -export-dynamic
frepple_LDADD = libfrepple.la

SUBDIRS = utils model solver

EXTRA_DIST = dll.rc exe.rc

CLEANFILES = *.gcda *.gcov *.gcno
