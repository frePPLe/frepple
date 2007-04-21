#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.i README.txt frepple_perl.pl frepple_python.py frepple_java.java

CLEANFILES = *.so *.dll wrapper* *.class

if CYGWIN
JAVAHOME = /C/Program Files/Java/jdk1.5.0_07
PERLHOME = /lib/perl5/5.8/cygwin/core
else
JAVAHOME = /usr/lib/jvm/java-1.4.2-gcj
PERLHOME = /usr/lib/perl5/5.8.8/i386-linux-thread-multi/CORE
endif

contrib: clean python perl

# Note that the name of the created shared libraries:
# For PERL the output is frepple.dll / frepple.so
# For PYTHON the output is _frepple.dll / _frepple.so. However if the shared
# library of the perl build is also available, the python swig interface won't
# work. Python picks up the wrong shared library.

perl: frepple.i
	$(SWIG) -c++ -perl5 -o wrapper_perl.cpp frepple.i
if CYGWIN
	$(CXX) -c wrapper_perl.cpp -fPIC -I../../include -I"$(PERLHOME)"
	$(CXX) -shared wrapper_perl.o -L"$(PERLHOME)" -L../../src/.libs -lperl -lfrepple -Wl,--add-stdcall-alias -o frepple.dll
else
	$(CXX) -c wrapper_perl.cpp -fPIC -I../../include -I"$(PERLHOME)"
	$(CXX) -shared wrapper_perl.o "-L$(PERLHOME)" -L../../src/.libs -lperl -lfrepple -lxerces-c -o frepple.so
endif
	-perl frepple_perl.pl

python: frepple.i
	$(SWIG) -c++ -python -o wrapper_python.cpp frepple.i
if CYGWIN
	$(CXX) -c wrapper_python.cpp -fPIC -I../../include -I/usr/include/python2.5
	$(CXX) -shared wrapper_python.o -L/lib/python2.4/config -L../../src/.libs -lpython2.5 -lfrepple -Wl,--add-stdcall-alias -o _frepple.dll
else
	$(CXX) -c wrapper_python.cpp -fPIC -I../../include -I/usr/include/python2.4
	$(CXX) -shared wrapper_python.o -L/lib/python2.4/config -L../../src/.libs -lpython2.4 -lfrepple -lxerces-c -o _frepple.so
endif
	-python frepple_python.py

java: frepple.i
	$(SWIG) -c++ -java -o wrapper_java.cpp frepple.i
if CYGWIN
	$(CXX) -c wrapper_java.cpp -fPIC -I../../include -I"$(JAVAHOME)/include" -I"$(JAVAHOME)/include/win32"
	$(CXX) -shared wrapper_java.o -L"$(JAVAHOME)/lib" -L../../src/.libs -lfrepple.dll -Wl,--add-stdcall-alias -o frepplejava.dll
else
	$(CXX) -c wrapper_java.cpp -fPIC -I../../include -I"$(JAVAHOME)/include" -I"$(JAVAHOME)/include/linux"
	$(CXX) -shared wrapper_java.o -L"$(JAVAHOME)/lib" -L../../src/.libs -lfrepple -lxerces-c -o libfrepplejava.so
endif
	"$(JAVAHOME)/bin/javac" *.java
	-"$(JAVAHOME)/bin/java" -Djava.library.path=. frepple_java
