#
# Process this file with automake to produce Makefile.in
#

libsolver_la_SOURCES = solverprocure.cpp solverbuffer.cpp solverdemand.cpp solveroperation.cpp solverplan.cpp solverresource.cpp

AM_CPPFLAGS=-I@top_builddir@/include -I/usr/include/python$(PYTHON_VERSION)

CLEANFILES = *.gcda *.gcov *.gcno

noinst_LTLIBRARIES = libsolver.la

