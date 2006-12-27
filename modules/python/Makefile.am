#
# Process this file with automake to produce Makefile.in
#

sources = embeddedpython.cpp embeddedpython.h

EXTRA_DIST = $(sources)

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

CLEANFILES = *.gcda *.gcov *.gcno

if PYTHON

lib_LTLIBRARIES = mod_python.la
mod_python_la_SOURCES = $(sources)
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_python_la_LDFLAGS = -module -no-undefined 
mod_python_la_LIBADD = ../../src/libfrepple.la
else
mod_python_la_LDFLAGS = -module -avoid-version
endif

all-local: 
	cp .libs/mod_python.so ../../bin
	$(STRIP) ../../bin/mod_python.so

install-exec-local:
	cp .libs/mod_python.so $(bindir)

uninstall-local:
	rm $(bindir)/mod_python.so

endif
