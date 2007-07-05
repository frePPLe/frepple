#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = freppledb README.txt httpd.conf runserver.py setup.py frepple.ico

clean-local:
	-rm -rf `find . -name '*.pyc'`
	-rm -rf `find . -name '*.pyo'`

# Avoid packaging python bytecode files from the subdirectories
dist-hook:
	-rm -rf `find $(distdir) -name '*.pyc'`
	-rm -rf `find $(distdir) -name '*.pyo'`

start:
	cd freppledb; manage.py runserver

create:
	cd freppledb; manage.py syncdb
