#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = sample_module.cpp sample_module.1.expect sample_module.2.expect sample_module.h sample_module.xml frepple.xsd sample_module.vcxproj sample_module.vcxproj.filters visual_studio_2010.sln

CLEANFILES = output.* *.stackdump core *.gcda *.gcov *.gcno *.out

check_LTLIBRARIES = mod_sample.la
mod_sample_la_SOURCES = sample_module.cpp
mod_sample_la_LDFLAGS = -module -shrext .so -avoid-version -rpath /dev/null
mod_sample_la_LIBADD = ../../src/libfrepple.la
if CYGWIN
# Cygwin doesn't like undefined symbols in a windows dll
mod_sample_la_LDFLAGS += -no-undefined
endif

# A convenience copy to quickly collect the results
check-local:
	-cp .libs/mod_sample.so ../../bin

clean-local:
	-rm -rf Debug Release *.user *.opt *.ncb *.suo *.log *.sdf ipch
