#
# Process this file with automake to produce Makefile.in
#

sources = frepple2python.cpp embeddedpython.cpp embeddedpython.h module.cpp

EXTRA_DIST = $(sources) pythonutils.h pythonutils.cpp mod_python.xsd

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

CLEANFILES = *.gcda *.gcov *.gcno

if PYTHON

usrlibdir = $(libdir)/frepple
usrlib_LTLIBRARIES = mod_python.la
mod_pythondir = $(datadir)
mod_python_DATA = mod_python.xsd
mod_python_la_SOURCES = $(sources)
mod_python_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_python_la_LDFLAGS += -no-undefined
mod_python_la_LIBADD = ../../src/libfrepple.la
endif

# A convenience copy to quickly collect the results
all-local:
	-cp .libs/mod_python.so ../../bin
	cp mod_python.xsd ../../bin

endif

