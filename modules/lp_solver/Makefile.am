#
# Process this file with automake to produce Makefile.in
#

sources = lpsolver.cpp lpsolver.h

EXTRA_DIST = $(sources)

if LP

mod_lpsolver_la_SOURCES = $(sources)
lib_LTLIBRARIES = mod_lpsolver.la
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_lpsolver_la_LDFLAGS = -module -no-undefined
mod_lpsolver_la_LIBADD = ../../src/libfrepple.la
else
mod_lpsolver_la_LDFLAGS = -module -avoid-version
endif

all-local: 
	cp .libs/mod_lpsolver.so ../../bin
	$(STRIP) ../../bin/mod_lpsolver.so

install-exec-local:
	cp .libs/mod_lpsolver.so $(bindir)

uninstall-local:
	rm $(bindir)/mod_lpsolver.so

endif

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno
