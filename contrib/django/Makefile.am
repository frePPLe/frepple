#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = freppledb README.txt httpd.conf

clean-local:
	-rm -rf `find . -name '*.pyc'`
	-rm -rf `find . -name '*.pyo'`

# Avoid packaging python bytecode files from the subdirectories
dist-hook:
	-rm -rf `find $(distdir) -name '*.pyc'`
	-rm -rf `find $(distdir) -name '*.pyo'`

create:
	cd freppledb; ./manage.py syncdb

check:
	cd freppledb; ./manage.py test

runserver:
	cd freppledb; ./manage.py runserver

international:
	cd freppledb; make-messages.py -a && compile-messages.py 
