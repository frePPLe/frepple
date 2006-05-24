#
# Process this file with automake to produce Makefile.in
#

sources = solverbuffer.cpp solverdemand.cpp solveroperation.cpp solverplan.cpp solverresource.cpp

AM_CPPFLAGS=-I@top_builddir@/include

CLEANFILES = *.gcda *.gcov *.gcno

EXTRA_DIST = lpsolver.cpp

noinst_LTLIBRARIES = libsolver.la

if LP
libsolver_la_SOURCES = $(sources) lpsolver.cpp
else
libsolver_la_SOURCES = $(sources)
endif
