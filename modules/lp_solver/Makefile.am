#
# Process this file with automake to produce Makefile.in
#

sources = lpsolver.cpp lpsolver.h

EXTRA_DIST = $(sources) mod_lpsolver.xsd

if LP

usrlibdir = $(libdir)/frepple
usrlib_LTLIBRARIES = mod_lpsolver.la
mod_lpsolver_la_SOURCES = $(sources)
mod_lpsolverdir = $(datadir)
mod_lpsolver_DATA = mod_lpsolver.xsd
mod_lpsolver_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null

if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_lpsolver_la_LDFLAGS += -no-undefined
mod_lpsolver_la_LIBADD = ../../src/libfrepple.la
endif

# A convenience copy to quickly collect the results
all-local:
	-cp .libs/mod_lpsolver.so ../../bin
	cp mod_lpsolver.xsd ../../bin

endif

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno
