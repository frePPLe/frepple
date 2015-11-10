#
# Process this file with automake to produce Makefile.in
#

bin_PROGRAMS = frepple

# The local target builds the main executables first, and then copies the
# output to the bin directory
all-local: frepple$(EXEEXT)
	if test -f .libs/frepple$(EXEEXT); then cp .libs/frepple$(EXEEXT) ../bin; fi
	if test -f .libs/cygfrepple*.dll; then cp .libs/cygfrepple*.dll ../bin; fi
	if test -f .libs/libfrepple.so; then cp .libs/libfrepple*.so* ../bin; fi

# Shared library
lib_LTLIBRARIES = libfrepple.la
libfrepple_la_SOURCES = dllmain.cpp tags.cpp
libfrepple_la_LDFLAGS = -version-info @LIBRARY_VERSION@ -no-undefined
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
libfrepple_la_LDFLAGS += -Wl,--export-all-symbols
endif
libfrepple_la_LIBADD = ./solver/libsolver.la ./model/libmodel.la ./utils/libutils.la

# Python extension
install-data-local: setup.py pythonextension.cpp
	export VERSION="$(PACKAGE_VERSION)" LIB_DIR="$(DESTDIR)$(libdir)"; $(PYTHON) setup.py install --prefix $(DESTDIR)$(prefix) $(PYFLAGS)

uninstall-local:
	-rm -rf $(DESTDIR)$(pythondir)/frepple.*.so $(DESTDIR)$(pythondir)/frepple-$(PACKAGE_VERSION).egg-info

# Dynamically linked executable
frepple_SOURCES = main.cpp
frepple_LDFLAGS = -dynamic -export-dynamic
frepple_LDADD = libfrepple.la


SUBDIRS = utils model solver

EXTRA_DIST = dll.rc exe.rc frepple.ico setup.py pythonextension.cpp

clean-local:
	-rm -rf *.gcda *.gcov *.gcno build
