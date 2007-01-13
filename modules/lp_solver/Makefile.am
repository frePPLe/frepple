#
# Process this file with automake to produce Makefile.in
#

sources = lpsolver.cpp lpsolver.h

# Install the library in the bin directory.
# Ain't standard practice, but in this way all binaries are consolidated in a
# single directory.
libdir = @bindir@

EXTRA_DIST = $(sources) mod_lpsolver.xsd

if LP

mod_lpsolver_la_SOURCES = $(sources)
lib_LTLIBRARIES = mod_lpsolver.la
mod_lpsolver_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_lpsolver_la_LDFLAGS += -no-undefined
mod_lpsolver_la_LIBADD = ../../src/libfrepple.la
endif

all-local:
# not really portable, but does the job on linux
	-cp .libs/mod_lpsolver.so ../../bin
	-$(STRIP) ../../bin/mod_lpsolver.so
	cp mod_lpsolver.xsd ../../bin

clean-local:
	-rm -f ../../bin/mod_lpsolver.xsd
	-rm -f ../../bin/mod_lpsolver.so

install-exec-local:
	cp mod_lpsolver.xsd $(bindir)

uninstall-local:
	rm $(bindir)/mod_lpsolver.xsd

endif

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno
