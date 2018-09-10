#
# Process this file with autoconf to produce a configure script.
#

#
# Copyright (C) 2007-2016 by frePPLe bvba
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Initialization
#
AC_PREREQ(2.60)
AC_INIT([frepple], [4.4.2])
AC_CONFIG_SRCDIR([src/main.cpp])
AC_CONFIG_HEADER([config.h])
AM_INIT_AUTOMAKE([tar-ustar foreign])

#
# Checks for programs and initialize libtool
#
AC_GNU_SOURCE
LT_INIT([disable-static], [win32-dll], [dlopen])
AC_PROG_CXX
AC_PROG_INSTALL
AC_PROG_MAKE_SET
AC_LANG(C++)
AC_LANG_COMPILER_REQUIRE
AC_PROG_LIBTOOL

# Note: the library version number and the package version number are
# INDEPENDENT. The library version is the concatenation of LIBCURRENT,
# LIBREVISION and LIBAGE (in this order and separated by a colon).
# Use the following rules for updating the numbering scheme.
# 1) Increment LIBREVISION if source code has changed at all
# 2) If the API has changed, increment LIBCURRENT and set LIBREVISION to 0
# 3) If the API changes compatibly (i.e. simply adding a new function
#    without changing or removing earlier interfaces), then increment LIBAGE.
# 4) If the API changes incompatibly set LIBAGE back to 0
LIBRARY_VERSION=[0:0:0]
AC_SUBST(LIBRARY_VERSION)

#
# Define an extra configure argument to enable debugging
#
AC_ARG_ENABLE(debug,
AS_HELP_STRING([--enable-debug],[Turn on debugging]),
[case "${enableval}" in
  yes) debug=true ;;
  no)  debug=false ;;
  *) AC_MSG_ERROR([bad value ${enableval} for --enable-debug]) ;;
esac],[debug=false])
AM_CONDITIONAL(DEBUG, test x$debug = xtrue)

#
# Define an extra configure argument to compile for test coverage measurement
# This works only with the gcov tool and the gcc compiler
#
AC_ARG_ENABLE(coverage,
AS_HELP_STRING([--enable-coverage],
[Compile for test coverage measurement (GCC only, using gcov)]),
[case "${enableval}" in
  yes) coverage=true
       AC_CHECK_PROGS(GCOV, gcov, nogcov)
       if test x$GCOV = xnogcov
       then
          AC_MSG_ERROR([Could not find gcov, no coverage build is possible])
       fi
       ;;
  no)  coverage=false ;;
  *) AC_MSG_ERROR([bad value ${enableval} for --enable-coverage]) ;;
esac],[coverage=false])
AM_CONDITIONAL(COVERAGE, test x$coverage = xtrue)

#
# Define an extra configure argument to compile an executable suitable for
# profiling. This compiler settings work only with the gcc compiler.
# Valgrind is highly recommended as the profiling tool. (gprof doesn't do
# trick because frePPLe uses shared libraries)
#
AC_ARG_ENABLE(profile,
AS_HELP_STRING([--enable-profile],
[Compile for profiling (GCC only)]),
[case "${enableval}" in
  yes) profile=true ;;
  no)  profile=false ;;
  *) AC_MSG_ERROR([bad value ${enableval} for --enable-profile]) ;;
esac],[profile=false])
AM_CONDITIONAL(PROFILE, test x$profile = xtrue)

#
# Define a configure argument to enable/disable building of the documentation
#
AC_ARG_ENABLE([doc],
AS_HELP_STRING([--enable-doc],
[Enable documentation generation(default false)]),
[case "${enableval}" in
  no)  generatedoc=false;;
  yes) generatedoc=true
       AC_CHECK_PROGS(DOXYGEN, doxygen, notavailable)
       AC_CHECK_PROGS(SPHINXBUILD, sphinx-build sphinx-build-3, notavailable)
       if test x$SPHINXBUILD = xnotavailable
       then
          AC_MSG_ERROR([Could not find sphinx-build, no documentation can be built])
          generatedoc=false
       fi
       ;;
  *) AC_MSG_ERROR([bad value ${enableval} for --enable-doc]) ;;
esac],[generatedoc=false])
AM_CONDITIONAL(DOC, test x$generatedoc = xtrue)

#
# Define a configure argument to pass python installation parameters
#
AC_ARG_VAR([PYFLAGS],
[Argument passed to setup.py when installing frePPLe's Python application.])

# Check the availability of the external programs
AC_CHECK_PROG(HAVE_DOT, dot, [YES], [NO])

# Checks for header files.
AC_HEADER_DIRENT
AC_HEADER_STDC
AC_CHECK_HEADERS([fcntl.h stdlib.h unistd.h python.h pthread.h])

# Checks for library functions.
AC_FUNC_MALLOC
AC_FUNC_MKTIME
AC_FUNC_STAT
AC_FUNC_STRFTIME
AC_CHECK_FUNCS([dup2 memset strncasecmp strnicmp strptime putenv _putenv localtime_r])

# Checks for typedefs, structures, and compiler characteristics.
AC_CHECK_HEADERS([ext/slist slist vector map set stack tuple])
AC_HEADER_STDBOOL
AC_C_CONST
AC_C_INLINE
AC_TYPE_SIZE_T
AC_STRUCT_TM

# Verify support for namespaces
AC_TRY_COMPILE(
  [namespace Outer { namespace Inner { int i = 0; }}],
  [using namespace Outer::Inner; return i;],
  [],
  [AC_MSG_ERROR([
  This package requires a C++ compiler that supports namespaces.
  ])])

#
# Verify installation of XERCES-C
#
AC_CHECK_HEADER([xercesc/util/XercesDefs.hpp], [],
[AC_MSG_ERROR([
  This package requires the XERCES-C XML parser...
  Please install this package and its development libraries.
  Check out http://xml.apache.org/xerces-c for more information.
])])
AC_CHECK_LIB([xerces-c], [main], [],
[AC_MSG_ERROR([
  This package requires the XERCES-C XML parser...
  Please install this package and its development libraries.
  Check out http://xml.apache.org/xerces-c for more information.
])])

AC_CHECKING([for xerces-c version >= 3.0 ])
AC_COMPILE_IFELSE([AC_LANG_SOURCE([
  #include "xercesc/util/XercesVersion.hpp"
  #if XERCES_VERSION_MAJOR==3
    int main (void) {return 1;}
  #else
    force compile error;
  #endif
  ])], [],
  [AC_MSG_ERROR([
  This package requires Xerces-C 3.0 or later.
  ])])

#
# Verify installation of PYTHON
#
AM_PATH_PYTHON([3.5], [],
[AC_MSG_ERROR([
  This package requires Python 3.5 or higher.
])])
AC_PATH_TOOL(PYTHON_CONFIG, "python3-config", notavailable)
if test x$PYTHON_CONFIG = xnotavailable
then
  AC_MSG_ERROR([This package requires the Python 3 development libraries.])
fi
LIBS="$($PYTHON_CONFIG --ldflags) $LIBS"
CPPFLAGS="$($PYTHON_CONFIG --includes) $CPPFLAGS"
AC_CHECK_HEADER([Python.h], [],
[AC_MSG_ERROR([
  This package requires Python 3 and its development libraries.
])])

#
# Verify installation of django
#
AC_MSG_CHECKING([django Python module])
$PYTHON -c "import django" 2>/dev/null
if test $? -ne 0 ; then
AC_MSG_RESULT([no])
AC_MSG_ERROR([
  This package requires the django web application framework.
  Please install this package from https://www.djangoproject.com/
  and also make sure to apply frePPLe's patches for it.
])
fi
AC_MSG_RESULT([yes])

#
# Check whether we are running on a Windows operating system
#
AC_CHECK_HEADER(windows.h,
[AC_DEFINE(HAVE_WINDOWS_H, 1, [Define to 1 when running on windows platform.])
])

#
# Compiler&linker flags and include&library directories
#
CPPFLAGS="-I\$(top_builddir)/include $CPPFLAGS"
if test x$debug = xtrue ; then
  # The settings on the next line are the normal debugging parameters
  CXXFLAGS="-ggdb -Wall -std=c++0x $CXXFLAGS -O0"
  AC_DEFINE([DEBUG], [], [Used for debugging builds])
else if test x$coverage = xtrue ; then
  # The settings on the next line are suitable for creating an executable to
  # be used for code coverage measurement using gcc and gprof.
  CXXFLAGS="-fprofile-arcs -ftest-coverage -std=c++0x $CXXFLAGS"
  AC_DEFINE([NDEBUG], [], [Disables assertions])
else if test x$profile = xtrue ; then
  # The settings on the next line are suitable for creating an executable to
  # be used for profiling using gcc.
  # CXXFLAGS="-g -Wall -pg -fno-inline $CXXFLAGS"
  CXXFLAGS="-g -Wall -std=c++0x $CXXFLAGS "
  AC_DEFINE([NDEBUG], [], [Disables assertions])
else
  CXXFLAGS="-O3 -s -std=c++0x $CXXFLAGS"
  AC_DEFINE([NDEBUG], [], [Disables assertions])
fi ; fi ; fi
case $host_os in
  cygwin*)
    LIBS="-lpthread $LIBS"
    # Linker option to avoid some ugly warnings...
    LDFLAGS="$LDFLAGS -Wl,--enable-auto-import"
    ;;
  *)
    LIBS="-ldl $LIBS"
    CXXFLAGS="-pthread $CXXFLAGS"
    ;;
esac
AM_CONDITIONAL(CYGWIN, test x$host_os = xcygwin)

# Define the output make files
AC_CONFIG_FILES([ Makefile bin/Makefile doc/Makefile ])
AC_CONFIG_FILES([ include/Makefile include/frepple/Makefile ])
AC_CONFIG_FILES([ src/Makefile src/model/Makefile src/solver/Makefile src/utils/Makefile ])
AC_CONFIG_FILES([ contrib/Makefile contrib/vc/Makefile contrib/installer/Makefile contrib/rpm/Makefile contrib/debian/Makefile contrib/odoo/Makefile contrib/docker/Makefile ])
AC_CONFIG_FILES([ test/Makefile test/buffer_batch/Makefile test/cluster/Makefile test/custom_fields/Makefile test/calendar/Makefile test/constraints_combined_1/Makefile test/constraints_combined_2/Makefile test/constraints_leadtime_1/Makefile test/constraints_leadtime_2/Makefile test/constraints_material_1/Makefile test/constraints_material_2/Makefile test/constraints_material_3/Makefile test/constraints_material_4/Makefile test/datetime/Makefile test/distribution_1/Makefile test/flow_alternate_1/Makefile test/flow_alternate_2/Makefile test/flow_fixed/Makefile test/flow_transferbatch/Makefile test/scalability_1/Makefile test/scalability_2/Makefile test/scalability_3/Makefile test/jobshop/Makefile test/xml/Makefile test/xml_remote/Makefile  test/constraints_resource_1/Makefile test/constraints_resource_2/Makefile test/constraints_resource_3/Makefile test/constraints_resource_4/Makefile test/constraints_resource_5/Makefile test/constraints_resource_6/Makefile test/criticality/Makefile test/problems/Makefile test/deletion/Makefile test/demand_policy/Makefile test/operation_alternate/Makefile test/operation_available/Makefile test/operation_effective/Makefile test/operation_pre_post/Makefile test/operation_routing/Makefile test/operation_split/Makefile test/multithreading/Makefile test/name/Makefile test/python_1/Makefile test/python_2/Makefile test/python_3/Makefile test/callback/Makefile test/pegging/Makefile test/safety_stock/Makefile test/flow_effective/Makefile test/load_alternate/Makefile test/load_bucketized/Makefile test/load_effective/Makefile test/setup_1/Makefile test/setup_2/Makefile test/setup_3/Makefile test/skills/Makefile test/supplier/Makefile test/wip/Makefile test/global_purchase/Makefile test/resource_efficiency/Makefile ])

# Generate all make files
AC_OUTPUT

# Byebye message
echo
echo "--------------------------------------------------------"
echo "Configuration is complete"
echo
echo "Run the following commands to compile and install:"
echo "  make "
echo "  make install"
echo
echo "Note that this only compiles and installs the core planning engine."
echo "It does NOT install or configure the web server for the user interface."
echo
echo "--------------------------------------------------------"
