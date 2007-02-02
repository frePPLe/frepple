#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = freppledb README.txt

clean-local:
	-rm -rf `find . -name '*.pyc'`
	-rm -rf `find . -name '*.pyo'`

start:
	cd freppledb; manage.py runserver

create:
	cd freppledb; manage.py syncdb
	cd freppledb; manage.py reset input
	cd freppledb; manage.py reset output
	cd freppledb; manage.py reset execute
