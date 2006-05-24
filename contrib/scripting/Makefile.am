#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = frepple.i README.txt frepple_perl.pl frepple_python.py frepple_java.java

CLEANFILES = *.so *.dll wrapper*

contrib: clean python perl

# Note that the name of the created shared libraries:
# For PERL the output is frepple.dll / frepple.so
# For PYTHON the output is _frepple.dll / _frepple.so. However if the shared 
# library of the perl build is also available, the python swig interface won't 
# work. Python picks up the wrong shared library.

perl: frepple.i
	$(SWIG) -c++ -perl5 -o wrapper_perl.cpp frepple.i
	$(CXX) -c wrapper_perl.cpp -fPIC -I../../include -I/lib/perl5/5.8/cygwin/core
	$(CXX) -shared wrapper_perl.o -L/lib/perl5/5.8/cygwin/core -L../../src/.libs -lperl -lfrepple -Wl,--add-stdcall-alias -o frepple.dll
#	$(CXX) -c wrapper_perl.cpp -fPIC -I../../include -I/usr/lib/perl5/5.8.6/i386-linux-thread-multi/CORE
#	$(CXX) -shared wrapper_perl.o -L/usr/lib/perl5/5.8.6/i386-linux-thread-multi/CORE -L../../src/.libs -lperl -lfrepple -lxerces-c -o frepple.so
	-perl frepple_perl.pl

python: frepple.i
	$(SWIG) -c++ -python -o wrapper_python.cpp frepple.i
	$(CXX) -c wrapper_python.cpp -fPIC -I../../include -I/usr/include/python2.4
	$(CXX) -shared wrapper_python.o -L/lib/python2.4/config -L../../src/.libs -lpython2.4 -lfrepple -Wl,--add-stdcall-alias -o _frepple.dll
#	$(CXX) -shared wrapper_python.o -L/lib/python2.4/config -L../../src/.libs -lpython2.4 -lfrepple -lxerces-c -o _frepple.so
	-python frepple_python.py

java: frepple.i
	$(SWIG) -c++ -java -o wrapper_java.cpp frepple.i
	$(CXX) -c wrapper_java.cpp -fPIC -I../../include -I/C/i2/bea/jdk141_03/include -I/C/i2/bea/jdk141_03/include/win32
	$(CXX) -shared wrapper_java.o -L/C/i2/bea/jdk141_03/lib -L../../src/.libs -lfrepple.dll -Wl,--add-stdcall-alias -o frepplejava.dll
#	$(CXX) -c wrapper_java.cpp -fPIC -I../../include -I/usr/lib/jvm/java-1.4.2-gcj/include -I/usr/lib/jvm/java-1.4.2-gcj/include/linux
#	$(CXX) -shared wrapper_java.o -L/usr/lib/jvm/java-1.4.2/lib -L../../src/.libs -lfrepple -lxerces-c -o libfrepplejava.so
	javac *.java
	-java -Djava.library.path=. frepple_java
