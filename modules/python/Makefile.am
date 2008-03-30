#
# Process this file with automake to produce Makefile.in
#

sources = frepple2python.cpp embeddedpython.cpp embeddedpython.h module.cpp wrapper.cpp

# Install the library in the bin directory.
# Ain't standard practice, but in this way all binaries are consolidated in a
# single directory.
libdir = @bindir@

EXTRA_DIST = $(sources) mod_python.xsd

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

CLEANFILES = *.gcda *.gcov *.gcno

if PYTHON

lib_LTLIBRARIES = mod_python.la
mod_python_la_SOURCES = $(sources)
mod_python_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_python_la_LDFLAGS += -no-undefined
mod_python_la_LIBADD = ../../src/libfrepple.la
endif

# not really portable, but does the job on linux
all-local:
if DEBUG
	-cp .libs/mod_python.so ../../bin
else
if COVERAGE
	-cp .libs/mod_python.so ../../bin
else
if PROFILE
	-cp .libs/mod_python.so ../../bin
else
	-cp .libs/mod_python.so ../../bin
	-$(STRIP) ../../bin/mod_python.so
endif
endif
endif
	cp mod_python.xsd ../../bin

install-exec-local:
	cp mod_python.xsd $(bindir)

uninstall-local:
	rm $(bindir)/mod_python.xsd

endif

clean-local:
	-rm -f ../../bin/mod_python.xsd
	-rm -f ../../bin/mod_python.so
